#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2024 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

from pymeasure.instruments import Instrument, Channel, SCPIMixin
from pymeasure.instruments.sub_instrument import SubInstrument # TODO refactor class to use sub_system instead, 
from pymeasure.instruments.process import get_processor_default, preprocess_input_enum
from pymeasure.instruments.validators import strict_range, strict_discrete_set, joined_validators, cast_to_alphanumeric, SCPI_discrete_set
from pymeasure.instruments.values import Choices, DICTS, str_enum_from_values
from pymeasure.instruments.specs import SCPI_ID, InstrumentSpecs
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class AFG31000Specs(InstrumentSpecs):
    """Per-model capability/limit specification for an AFG31000-series unit.

    Holds the limits that cannot be queried from the instrument over SCPI and so
    must live in code — most notably the advanced-mode (sequence) sample-rate
    ceiling, which ``SEQControl:SRATe`` accepts no ``MIN``/``MAX`` for.

    Attributes:
        model_num: Model number (e.g. ``'AFG31052'``).
        bandwidth: Maximum output bandwidth in Hz.
        arb_sample_rate: Arbitrary-waveform sample rate in samples per second.
        seq_sample_rate: Advanced-mode (sequence) sample-rate ceiling in samples
            per second. For the 50 MHz models this is *lower* than
            :attr:`arb_sample_rate`.
        channels: Number of output channels.
        min_pulse_width: Minimum pulse width in seconds.
    """

    model_num: str = ""
    bandwidth: float = 0.0
    arb_sample_rate: float = 0.0
    seq_sample_rate: float = 0.0
    channels: int = 0
    min_pulse_width: float = 0.0


# AFG31000-series model table. Sourced from Tektronix AFG31000 Series Programmer's
# Manual 077-148-803:
#   - Table 1 "AFG31000 models" -> bandwidth, arb_sample_rate, channels
#   - Default Settings -> Advanced Mode -> per-model sequence sample rate
#     (note the trap: the 50 MHz models cap the sequence rate at 500 MS/s, which
#     is *not* equal to their 1 GS/s arbitrary sample rate)
#   - [SOURce]:PULSe:WIDTh -> min_pulse_width
AFG31000_MODELS = {
    spec.model_num: spec
    for spec in (
        #              model_num    bandwidth arb_srate seq_srate channels min_pw
        AFG31000Specs("AFG31021",   25e6,     250e6,    250e6,    1,       16e-9),
        AFG31000Specs("AFG31022",   25e6,     250e6,    250e6,    2,       16e-9),
        AFG31000Specs("AFG31051",   50e6,     1e9,      500e6,    1,       10e-9),
        AFG31000Specs("AFG31052",   50e6,     1e9,      500e6,    2,       10e-9),
        AFG31000Specs("AFG31101",   100e6,    1e9,      1e9,      1,       6e-9),
        AFG31000Specs("AFG31102",   100e6,    1e9,      1e9,      2,       6e-9),
        AFG31000Specs("AFG31151",   150e6,    2e9,      2e9,      1,       5e-9),
        AFG31000Specs("AFG31152",   150e6,    2e9,      2e9,      2,       5e-9),
        AFG31000Specs("AFG31251",   250e6,    2e9,      2e9,      1,       4e-9),
        AFG31000Specs("AFG31252",   250e6,    2e9,      2e9,      2,       4e-9),
    )
}


class AFG31000ElementChoices(Choices):
    """Accepted-value enums for :class:`AFG31000SequenceElement` commands."""

    jump_target_type = str_enum_from_values("JTARGET_TYPES", ["INDex", "NEXT", "OFF"])
    jump_event = str_enum_from_values("TRIGGER_EVENTS", ["EXTernal", "BUS", "MANual", "TIMer"])
    jump_slope = str_enum_from_values("SLOPES", ["POSitive", "NEGative"])
    wait_event = jump_event
    wait_slope = jump_slope


class AFG31000SequenceElement(Channel):
    """Represents a single element of the AFG31000 advanced-mode waveform sequence.

    The channel ``id`` is the sequence element index ``n`` (1–256), substituted for
    ``{ch}`` into the ``sequence:elem{ch}:`` command prefix via :meth:`Channel.insert_id`.
    This class collects the ``SEQuence:ELEM[n]`` commands — the per-element settings
    that control jumps, waits, looping, markers, and the waveform(s) the element plays.

    Element interfaces are reached through the :class:`AFG31000Sequence` sub-instrument's
    :attr:`~AFG31000Sequence.element` dict, e.g. ``afg.sequence.element[1]``.

    .. code-block:: python

        afg = AFG31000("USB0::0x0699::0x035B::C010001::INSTR")
        elem = afg.sequence.element[1]    # first sequence element

        elem.loop_count = 100
        elem.goto_state = True
        elem.goto_index = 6
        elem.set_waveform("P:/Pulse1000.tfwx", channel=1)
    """

    ELEMENT_LIMIT = [1, 256]
    LOOP_COUNT_LIMIT = [1, 1_000_000]

    #: Accepted-value enums for this element's commands; see
    #: :class:`AFG31000ElementChoices`. Referenced directly by the controls below
    #: (``values=choices.jump_slope``) and by users (``element.choices.jump_slope``).
    choices = AFG31000ElementChoices

    # --- GOTO (unconditional jump after this element) ---

    goto_state = Channel.control(
        "sequence:elem{ch}:goto:state?", "sequence:elem{ch}:goto:state %d",
        """Control whether the GOTO target index is used for this element. (bool)

        When enabled, the sequencer jumps to :attr:`goto_index` after generating this
        element instead of moving on to the next element.
        """,
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_INT,
        map_values=True,
    )

    goto_index = Channel.control(
        "sequence:elem{ch}:goto:index?", "sequence:elem{ch}:goto:index %d",
        """Control the GOTO target element index (1–256). (int)

        Only takes effect when :attr:`goto_state` is enabled.
        """,
        validator=strict_range,
        values=ELEMENT_LIMIT,
        cast=int,
    )

    # --- Marker ---

    marker_state = Channel.control(
        "sequence:elem{ch}:marker:state?", "sequence:elem{ch}:marker:state %d",
        """Control the marker output state for this element. (bool)""",
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_INT,
        map_values=True,
    )

    # --- Event jump ---

    jump_target_type = Channel.control(
        "sequence:elem{ch}:jtarget:type?", "sequence:elem{ch}:jtarget:type %s",
        """Control the event-jump target type ('INDex', 'NEXT', or 'OFF'). (str)

        'INDex' jumps to :attr:`jump_target_index`, 'NEXT' jumps to the next element,
        and 'OFF' disables event jumps (trigger events are ignored).
        """,
        preprocess_input=preprocess_input_enum(choices.jump_target_type),
        validator=strict_discrete_set,
        values=choices.jump_target_type,
    )

    jump_target_index = Channel.control(
        "sequence:elem{ch}:jtarget:index?", "sequence:elem{ch}:jtarget:index %d",
        """Control the event-jump target element index (1–256). (int)

        Only takes effect when :attr:`jump_target_type` is set to 'INDex'.
        """,
        validator=strict_range,
        values=ELEMENT_LIMIT,
        cast=int,
    )

    jump_event = Channel.control(
        "sequence:elem{ch}:jump:event?", "sequence:elem{ch}:jump:event %s",
        """Control the jump trigger event source. (str)

        Accepted values: 'EXTernal', 'BUS', 'MANual', 'TIMer'.
        """,
        preprocess_input=preprocess_input_enum(choices.jump_event),
        validator=strict_discrete_set,
        values=choices.jump_event,
    )

    jump_slope = Channel.control(
        "sequence:elem{ch}:jump:slope?", "sequence:elem{ch}:jump:slope %s",
        """Control the external-trigger slope for the jump event
        ('POSitive' or 'NEGative'). (str)""",
        preprocess_input=preprocess_input_enum(choices.jump_slope),
        validator=strict_discrete_set,
        values=choices.jump_slope,
    )

    # --- Looping ---

    loop_count = Channel.control(
        "sequence:elem{ch}:loop:count?", "sequence:elem{ch}:loop:count %d",
        """Control the number of times this element repeats (1–1,000,000). (int)

        Ignored when :attr:`loop_infinite` is enabled.
        """,
        validator=strict_range,
        values=LOOP_COUNT_LIMIT,
        cast=int,
    )

    loop_infinite = Channel.control(
        "sequence:elem{ch}:loop:infinite?", "sequence:elem{ch}:loop:infinite %d",
        """Control whether this element loops infinitely. (bool)

        While enabled, the sequencer repeats this element continuously until the
        sequence is stopped or the run mode is changed.
        """,
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_INT,
        map_values=True,
    )

    # --- Wait trigger ---

    wait_trigger_state = Channel.control(
        "sequence:elem{ch}:twait:state?", "sequence:elem{ch}:twait:state %d",
        """Control whether this element waits for a trigger before playing. (bool)""",
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_INT,
        map_values=True,
    )

    wait_event = Channel.control(
        "sequence:elem{ch}:twait:event?", "sequence:elem{ch}:twait:event %s",
        """Control the wait trigger event source. (str)

        Accepted values: 'EXTernal', 'BUS', 'MANual', 'TIMer'.
        """,
        preprocess_input=preprocess_input_enum(choices.wait_event),
        validator=strict_discrete_set,
        values=choices.wait_event,
    )

    wait_slope = Channel.control(
        "sequence:elem{ch}:twait:slope?", "sequence:elem{ch}:twait:slope %s",
        """Control the external-trigger slope for the wait event
        ('POSitive' or 'NEGative'). (str)""",
        preprocess_input=preprocess_input_enum(choices.wait_slope),
        validator=strict_discrete_set,
        values=choices.wait_slope,
    )

    # --- Waveform assignment (per source channel m) ---

    def waveform(self, channel=1):
        """Query the waveform assigned to a source channel for this sequence element.

        :param channel: Source channel index ``m`` (1 or 2). Defaults to 1.
        :returns: The waveform path/name string (e.g. ``"P:/Pulse1000.tfwx"``).
        """
        return self.ask(f"sequence:elem{{ch}}:waveform{channel}?").strip()

    def set_waveform(self, name, channel=1):
        """Assign a waveform to a source channel for this sequence element.

        All waveforms assigned to a single sequence element must be the same length.

        :param name: Waveform path/name string. ``M:/`` is internal memory, ``U:/`` is
            external USB memory, and ``P:/`` is the internal predefined waveforms.
        :param channel: Source channel index ``m`` (1 or 2). Defaults to 1.
        """
        self.write(f'sequence:elem{{ch}}:waveform{channel} "{name}"')


class AFG31000SequenceChoices(Choices):
    """Accepted-value enums for :class:`AFG31000Sequence` commands."""

    run_mode = str_enum_from_values("RUN_MODES", ["CONTinuous", "TRIGgered", "GATed", "SEQuence"])


class AFG31000Sequence(SubInstrument):
    """Represents the advanced (sequence) mode of the Tektronix AFG31000 series.

    This sub-instrument holds the per-element interfaces in the :attr:`element` dict,
    keyed by their 1-based element index (``element[1]`` … ``element[256]``), and
    exposes the sequence-control commands (``SEQControl:*``, ``SEQuence:LENGth``,
    ``SEQuence:NEW``) that act on the sequence as a whole.

    A dict is used for :attr:`element` rather than a list/tuple because the instrument
    numbers sequence elements from 1, whereas Python sequences start at 0.

    .. code-block:: python

        afg = AFG31000("USB0::0x0699::0x035B::C010001::INSTR")

        afg.sequence.length = 2                    # create a 2-element sequence
        afg.sequence.element[1].set_waveform("P:/Pulse1000.tfwx", channel=1)
        afg.sequence.element[1].loop_count = 100
        afg.sequence.state = True                  # enter sequence mode
        afg.sequence.run()                         # start output
    """

    NUM_ELEMENTS = 256

    #: Accepted-value enums for the sequence commands; see
    #: :class:`AFG31000SequenceChoices` (e.g. ``sequence.choices.run_mode.sequence``).
    choices = AFG31000SequenceChoices

    LENGTH_LIMIT = [0, NUM_ELEMENTS]
    DELAY_LIMIT = [-320e-9, 320e-9]   # skew time, two-channel models only
    TIMER_LIMIT = [2e-6, 3600.0]      # jump/wait timer
    SCALE_LIMIT = [0.0, 1000.0]
    OFFSET_LIMIT = [-1e6, 1e6]

    def __init__(self, parent, id=None):
        super().__init__(parent, id)
        #: Mapping of element index (1–:attr:`NUM_ELEMENTS`) to its
        #: :class:`AFG31000SequenceElement` interface. Keyed from 1 to match the
        #: instrument's 1-based element numbering.
        self.element = {
            n: AFG31000SequenceElement(parent, n)
            for n in range(1, self.NUM_ELEMENTS + 1)
        }

    # --- Sequence definition ---

    length = Instrument.control(
        "sequence:length?", "sequence:length %d",
        """Control the number of elements in the sequence (0–256). (int)

        Setting 0 clears every element. Setting a value smaller than the current
        length deletes the trailing elements; this cannot be undone.
        """,
        validator=strict_range,
        values=LENGTH_LIMIT,
        cast=int,
    )

    def new(self):
        """Create a new, empty sequence (clears the waveform list and resets defaults)."""
        self.write("sequence:new")

    # --- Run control ---

    run_mode = Instrument.control(
        "seqcontrol:rmode?", "seqcontrol:rmode %s",
        """Control the advanced-mode run mode. (str)

        Accepted values: 'CONTinuous', 'TRIGgered', 'GATed', 'SEQuence'.
        """,
        preprocess_input=preprocess_input_enum(choices.run_mode),
        validator=strict_discrete_set,
        values=choices.run_mode,
    )

    state = Instrument.control(
        "seqcontrol:state?", "seqcontrol:state %d",
        """Control whether the instrument is in sequence mode (vs. AFG mode). (bool)""",
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_INT,
        map_values=True,
    )

    running = Instrument.measurement(
        "seqcontrol:rstate?",
        """Get whether the sequence is currently running. (bool)""",
        values=DICTS.BOOLEAN_TO_INT,
        map_values=True,
    )

    sample_rate = Instrument.control(
        "seqcontrol:srate?", "seqcontrol:srate %e",
        """Control the sequence sampling rate in samples per second. (float)""",
    )

    def set_sample_rate(self, rate):
        """Set the sequence sample rate, validated against the model's ceiling.

        ``SEQControl:SRATe`` accepts no ``MIN``/``MAX`` over SCPI, so the
        advanced-mode sample-rate ceiling cannot be range-checked on the wire.
        This convenience validates ``rate`` against the resolved model's
        :attr:`~AFG31000Specs.seq_sample_rate` (from :attr:`AFG31000.specs`)
        before writing. The plain :attr:`sample_rate` property is left unchecked.

        :param rate: Desired sequence sample rate in samples per second.
        :raises ValueError: If ``rate`` exceeds the model's sequence sample-rate
            ceiling.
        """
        specs = getattr(self.parent, "specs", None)
        if specs is None:
            logger.warning(
                "Cannot validate sequence sample rate: model specs unavailable; "
                "writing %g S/s unchecked.", rate)
        elif rate > specs.seq_sample_rate:
            raise ValueError(
                f"Sequence sample rate {rate:g} S/s exceeds the "
                f"{specs.model_num} ceiling of {specs.seq_sample_rate:g} S/s.")
        self.sample_rate = rate

    delay = Instrument.control(
        "seqcontrol:delay?", "seqcontrol:delay %e",
        """Control the inter-channel trigger delay (skew) in seconds
        (-320 ns to 320 ns, two-channel models only). (float)""",
        validator=strict_range,
        values=DELAY_LIMIT,
    )

    timer = Instrument.control(
        "seqcontrol:timer?", "seqcontrol:timer %e",
        """Control the jump/wait trigger timer in seconds (2 µs to 3600 s). (float)""",
        validator=strict_range,
        values=TIMER_LIMIT,
    )

    def run(self):
        """Start the output of the waveform or sequence (validates the sequence first)."""
        self.write("seqcontrol:run:immediate")

    def stop(self):
        """Stop the output of the sequence."""
        self.write("seqcontrol:stop:immediate")

    def reset(self):
        """Reset the sequence to its default state (clears the waveform list and table)."""
        self.write("seqcontrol:reset:immediate")

    # --- Per source-channel scale / offset ---

    def source_scale(self, channel=1):
        """Query the sequence output scale for a source channel.

        :param channel: Source channel index (1 or 2). Defaults to 1.
        :returns: The output scale as a float (percent, 0.0–1000.0).
        """
        return float(self.ask(f"seqcontrol:source{channel}:scale?"))

    def set_source_scale(self, scale, channel=1):
        """Set the sequence output scale for a source channel.

        :param scale: Output scale in percent (0.0–1000.0).
        :param channel: Source channel index (1 or 2). Defaults to 1.
        """
        scale = strict_range(scale, self.SCALE_LIMIT)
        self.write(f"seqcontrol:source{channel}:scale {scale:g}")

    def source_offset(self, channel=1):
        """Query the sequence output offset for a source channel.

        :param channel: Source channel index (1 or 2). Defaults to 1.
        :returns: The output offset as a float.
        """
        return float(self.ask(f"seqcontrol:source{channel}:offset?"))

    def set_source_offset(self, offset, channel=1):
        """Set the sequence output offset for a source channel.

        :param offset: Output offset value (-1e6 to 1e6).
        :param channel: Source channel index (1 or 2). Defaults to 1.
        """
        offset = strict_range(offset, self.OFFSET_LIMIT)
        self.write(f"seqcontrol:source{channel}:offset {offset:e}")


class AFG31000Memory(SubInstrument):
    """File-system (mass memory) and setup-memory interface of the AFG31000 series.

    The instrument exposes three virtual drives. Every path-taking command is provided
    once per drive, with the drive letter and quoting handled automatically:

    - ``usb_*`` → U: USB mass memory (read/write)
    - ``memory_*`` → M: internal flash mass memory (read/write)
    - ``read_only_memory_*`` → P: internal predefined waveforms (read-only)

    Because the predefined (P:) drive is read-only, commands that write to a drive
    (delete, make-directory, store, save, lock) only have ``usb_`` and ``memory_``
    forms, while commands that read from a drive (load, open, recall, change-directory)
    also have a ``read_only_memory_`` form.

    The setup-memory commands (``MEMory:STATe``, ``*SAV``, ``*RCL``) address internal
    setup slots 0-4 and are not drive-specific.

    .. code-block:: python

        afg = AFG31000("USB0::0x0699::0x035B::C010001::INSTR")

        afg.memory.usb_delete = "TEK001.TFWX"          # MMEMory:DELete "U:/TEK001.TFWX"
        afg.memory.memory_make_directory = "sample"    # MMEMory:MDIRectory "M:/sample"
        afg.memory.read_only_memory_load_trace("Sine.tfwx", edit_memory=1)
        afg.memory.save(2)                             # *SAV 2
    """

    SETUP_SLOTS = [0, 4]        # *SAV/*RCL and MEMory:STATe slot range
    LOCKABLE_SLOTS = [1, 4]     # slot 0 (last setup) cannot be locked
    EDIT_MEMORIES = [1, 2]      # EMEMory1 / EMEMory2

    def __init__(self, parent, id=None):
        super().__init__(parent, id)

    # --- Status queries (no drive/path argument) ---

    catalog = Instrument.measurement(
        "mmemory:catalog?",
        """Get the mass-storage catalog: used bytes, free bytes, then file entries.""",
    )

    current_directory = Instrument.measurement(
        "mmemory:cdirectory?",
        """Get the current working directory of the mass-storage system. (str)""",
        get_process=lambda v: str(v).strip().strip('"'),
    )

    # --- Change directory (read access: all three drives) ---

    usb_change_directory = Instrument.setting(
        'mmemory:cdirectory "U:/%s"',
        """Set the current working directory to a path on the USB (U:) drive. (str)""",
    )
    memory_change_directory = Instrument.setting(
        'mmemory:cdirectory "M:/%s"',
        """Set the current working directory to a path on the internal (M:) drive. (str)""",
    )
    read_only_memory_change_directory = Instrument.setting(
        'mmemory:cdirectory "P:/%s"',
        """Set the current working directory to a path on the predefined (P:) drive. (str)""",
    )

    # --- Delete file/directory (write access: USB and internal only) ---

    usb_delete = Instrument.setting(
        'mmemory:delete "U:/%s"',
        """Set the file or directory to delete on the USB (U:) drive. (str)""",
    )
    memory_delete = Instrument.setting(
        'mmemory:delete "M:/%s"',
        """Set the file or directory to delete on the internal (M:) drive. (str)""",
    )

    # --- Make directory (write access) ---

    usb_make_directory = Instrument.setting(
        'mmemory:mdirectory "U:/%s"',
        """Set the directory to create on the USB (U:) drive. (str)""",
    )
    memory_make_directory = Instrument.setting(
        'mmemory:mdirectory "M:/%s"',
        """Set the directory to create on the internal (M:) drive. (str)""",
    )

    # --- Open sequence file (read access: all three drives) ---

    usb_open_sequence = Instrument.setting(
        'mmemory:open:sequence "U:/%s"',
        """Set the sequence file to open from the USB (U:) drive. (str)""",
    )
    memory_open_sequence = Instrument.setting(
        'mmemory:open:sequence "M:/%s"',
        """Set the sequence file to open from the internal (M:) drive. (str)""",
    )
    read_only_memory_open_sequence = Instrument.setting(
        'mmemory:open:sequence "P:/%s"',
        """Set the sequence file to open from the predefined (P:) drive. (str)""",
    )

    # --- Save sequence file (write access) ---

    usb_save_sequence = Instrument.setting(
        'mmemory:save:sequence "U:/%s"',
        """Set the path to save the current sequence to on the USB (U:) drive. (str)""",
    )
    memory_save_sequence = Instrument.setting(
        'mmemory:save:sequence "M:/%s"',
        """Set the path to save the current sequence to on the internal (M:) drive. (str)""",
    )

    # --- Recall setup file (read access: all three drives) ---

    usb_recall_setup = Instrument.setting(
        'recall:setup "U:/%s"',
        """Set the setup file to recall from the USB (U:) drive. (str)""",
    )
    memory_recall_setup = Instrument.setting(
        'recall:setup "M:/%s"',
        """Set the setup file to recall from the internal (M:) drive. (str)""",
    )
    read_only_memory_recall_setup = Instrument.setting(
        'recall:setup "P:/%s"',
        """Set the setup file to recall from the predefined (P:) drive. (str)""",
    )

    # --- Save setup file (write access) ---

    usb_save_setup = Instrument.setting(
        'save:setup "U:/%s"',
        """Set the path to save the current setup to on the USB (U:) drive. (str)""",
    )
    memory_save_setup = Instrument.setting(
        'save:setup "M:/%s"',
        """Set the path to save the current setup to on the internal (M:) drive. (str)""",
    )

    # --- Load setup file from a drive into a setup slot (read access: 3 drives) ---

    def _load_state(self, drive, location, file_name):
        location = int(strict_range(location, self.SETUP_SLOTS))
        self.write(f'mmemory:load:state {location:d},"{drive}:/{file_name}"')

    def usb_load_state(self, location, file_name):
        """Copy a setup file from the USB (U:) drive into setup slot ``location`` (0-4)."""
        self._load_state("U", location, file_name)

    def memory_load_state(self, location, file_name):
        """Copy a setup file from the internal (M:) drive into setup slot ``location``."""
        self._load_state("M", location, file_name)

    def read_only_memory_load_state(self, location, file_name):
        """Copy a setup file from the predefined (P:) drive into setup slot ``location``."""
        self._load_state("P", location, file_name)

    # --- Load a waveform from a drive into edit memory (read access: 3 drives) ---

    def _load_trace(self, drive, file_name, edit_memory=1):
        edit_memory = int(strict_discrete_set(edit_memory, self.EDIT_MEMORIES))
        self.write(f'mmemory:load:trace ememory{edit_memory:d},"{drive}:/{file_name}"')

    def usb_load_trace(self, file_name, edit_memory=1):
        """Copy a waveform from the USB (U:) drive into edit memory (1 or 2)."""
        self._load_trace("U", file_name, edit_memory)

    def memory_load_trace(self, file_name, edit_memory=1):
        """Copy a waveform from the internal (M:) drive into edit memory (1 or 2)."""
        self._load_trace("M", file_name, edit_memory)

    def read_only_memory_load_trace(self, file_name, edit_memory=1):
        """Copy a predefined waveform from the (P:) drive into edit memory (1 or 2)."""
        self._load_trace("P", file_name, edit_memory)

    # --- Store a setup slot to a drive (write access: USB and internal) ---

    def _store_state(self, drive, location, file_name):
        location = int(strict_range(location, self.SETUP_SLOTS))
        self.write(f'mmemory:store:state {location:d},"{drive}:/{file_name}"')

    def usb_store_state(self, location, file_name):
        """Save setup slot ``location`` (0-4) to a file on the USB (U:) drive."""
        self._store_state("U", location, file_name)

    def memory_store_state(self, location, file_name):
        """Save setup slot ``location`` (0-4) to a file on the internal (M:) drive."""
        self._store_state("M", location, file_name)

    # --- Store edit memory to a drive (write access) ---

    def _store_trace(self, drive, file_name, edit_memory=1):
        edit_memory = int(strict_discrete_set(edit_memory, self.EDIT_MEMORIES))
        self.write(f'mmemory:store:trace ememory{edit_memory:d},"{drive}:/{file_name}"')

    def usb_store_trace(self, file_name, edit_memory=1):
        """Save edit memory (1 or 2) to a waveform file on the USB (U:) drive."""
        self._store_trace("U", file_name, edit_memory)

    def memory_store_trace(self, file_name, edit_memory=1):
        """Save edit memory (1 or 2) to a waveform file on the internal (M:) drive."""
        self._store_trace("M", file_name, edit_memory)

    # --- Lock / unlock a file on a drive (write access) ---

    def _set_lock(self, drive, file_name, locked):
        self.write(f'mmemory:lock:state "{drive}:/{file_name}",{int(bool(locked)):d}')

    def _lock_state(self, drive, file_name):
        return bool(int(self.ask(f'mmemory:lock:state? "{drive}:/{file_name}"')))

    def usb_set_lock(self, file_name, locked=True):
        """Lock or unlock a file on the USB (U:) drive against overwrite/deletion."""
        self._set_lock("U", file_name, locked)

    def memory_set_lock(self, file_name, locked=True):
        """Lock or unlock a file on the internal (M:) drive against overwrite/deletion."""
        self._set_lock("M", file_name, locked)

    def usb_lock_state(self, file_name):
        """Query whether a file on the USB (U:) drive is locked. (bool)"""
        return self._lock_state("U", file_name)

    def memory_lock_state(self, file_name):
        """Query whether a file on the internal (M:) drive is locked. (bool)"""
        return self._lock_state("M", file_name)

    # --- Setup memory (slots 0-4; not drive-specific) ---

    recall_last_auto = Instrument.control(
        "memory:state:recall:auto?", "memory:state:recall:auto %d",
        """Control whether the last setup is auto-recalled at power-on. (bool)""",
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_INT,
        map_values=True,
    )

    def setup_delete(self, location):
        """Delete the contents of setup-memory slot ``location`` (0-4)."""
        location = int(strict_range(location, self.SETUP_SLOTS))
        self.write(f"memory:state:delete {location:d}")

    def setup_valid(self, location):
        """Query whether setup-memory slot ``location`` (0-4) holds a setup. (bool)"""
        location = int(strict_range(location, self.SETUP_SLOTS))
        return bool(int(self.ask(f"memory:state:valid? {location:d}")))

    def setup_set_lock(self, location, locked=True):
        """Lock or unlock setup-memory slot ``location`` (1-4) against overwrite."""
        location = int(strict_range(location, self.LOCKABLE_SLOTS))
        self.write(f"memory:state:lock {location:d},{int(bool(locked)):d}")

    def setup_lock_state(self, location):
        """Query whether setup-memory slot ``location`` (1-4) is locked. (bool)"""
        location = int(strict_range(location, self.LOCKABLE_SLOTS))
        return bool(int(self.ask(f"memory:state:lock? {location:d}")))

    def save(self, location):
        """Save the current instrument state to setup-memory slot ``location`` (0-4)."""
        location = int(strict_range(location, self.SETUP_SLOTS))
        self.write(f"*SAV {location:d}")

    def recall(self, location):
        """Restore the instrument state from setup-memory slot ``location`` (0-4)."""
        location = int(strict_range(location, self.SETUP_SLOTS))
        self.write(f"*RCL {location:d}")


class AFG31000ChannelChoices(Choices):
    """Accepted-value enums for :class:`AFG31000Channel` commands."""

    shape = str_enum_from_values("SHAPES", {
        "sinusoidal": "SIN",
        "square": "SQU",
        "pulse": "PULS",
        "ramp": "RAMP",
        "prnoise": "PRN",
        "dc": "DC",
        "sinc": "SINC",
        "gaussian": "GAUS",
        "lorentz": "LOR",
        "erise": "ERIS",
        "edecay": "EDEC",
        "haversine": "HARV",
        "file": "EFIL",
        "memory": "EMEM",
    })
    voltage_unit = str_enum_from_values("VOLTAGE_UNITS", ["VPP", "VRMS", "DBM"])
    output_impedance = str_enum_from_values("IMPEDANCE_OPTIONS", ["INFinity", "MINimum", "MAXimum"])
    burst_mode = str_enum_from_values("BURST_MODES", ["TRIGgered", "GATed", "INFinity"])
    sweep_spacing = str_enum_from_values("SWEEP_TYPES", ["LINear", "LOGarithmic"])
    output_polarity = str_enum_from_values("POLARITY", ["NORMal", "INVerted"])
    am_source = str_enum_from_values("MOD_SOURCES", ["INTernal", "EXTernal"])
    fm_source = am_source
    pm_source = am_source


class AFG31000Channel(Channel):
    """Represents a single output channel of the Tektronix AFG31000 series.

    Commands use the ``source{ch}:`` prefix for source commands and ``output{ch}:``
    for output-state commands, both resolved via :meth:`Channel.insert_id`.
    """

    FREQ_LIMIT = [1e-6, 250e6]
    DUTY_LIMIT = [0.001, 99.999]
    PHASE_LIMIT = [-180.0, 180.0]
    AMPLITUDE_VPP_LIMIT = [2e-3, 20.0]   # high-Z; 50 Ω limit is 1mVpp–10Vpp
    OFFSET_LIMIT = [-10.0, 10.0]
    IMPEDANCE_LIMIT = [1, 10000]

    #: Accepted-value enums for this channel's commands; see
    #: :class:`AFG31000ChannelChoices`. The single source of truth for the enum-backed
    #: controls below, which reference it directly (``values=choices.shape``).
    choices = AFG31000ChannelChoices

    # --- Waveform shape ---

    shape = Channel.control(
        "source{ch}:function:shape?", "source{ch}:function:shape %s",
        """Control the output waveform shape. (str)

        Accepts the human-readable names 'sinusoidal', 'square', 'pulse', 'ramp',
        'prnoise', 'dc', 'sinc', 'gaussian', 'lorentz', 'erise', 'edecay',
        'haversine', 'file', 'memory' (or an unambiguous abbreviation of at least
        three characters, e.g. 'mem' for 'memory'), as well as the SCPI mnemonics
        ('EMEM', 'EFIL', ...). The query returns the SCPI mnemonic.
        """,
        preprocess_input=preprocess_input_enum(choices.shape),
        validator=strict_discrete_set,
        values=choices.shape,
    )

    # --- Frequency ---

    frequency = Channel.control(
        "source{ch}:frequency:fixed?", "source{ch}:frequency:fixed %e",
        """Control the output frequency in Hz. (float)""",
        validator=strict_range,
        values=FREQ_LIMIT,
    )

    # --- Amplitude / voltage ---

    voltage_unit = Channel.control(
        "source{ch}:voltage:unit?", "source{ch}:voltage:unit %s",
        """Control the voltage unit ('VPP', 'VRMS', or 'DBM'). (str)""",
        preprocess_input=preprocess_input_enum(choices.voltage_unit),
        validator=strict_discrete_set,
        values=choices.voltage_unit,
    )

    amplitude = Channel.control(
        "source{ch}:voltage:amplitude?", "source{ch}:voltage:amplitude %e",
        """Control the output amplitude in the current voltage unit. (float)""",
        validator=strict_range,
        values=AMPLITUDE_VPP_LIMIT,
    )

    offset = Channel.control(
        "source{ch}:voltage:offset?", "source{ch}:voltage:offset %e",
        """Control the DC offset in Volts. (float)""",
        validator=strict_range,
        values=OFFSET_LIMIT,
    )

    high_level = Channel.control(
        "source{ch}:voltage:high?", "source{ch}:voltage:high %e",
        """Control the high voltage level in Volts. (float)""",
    )

    low_level = Channel.control(
        "source{ch}:voltage:low?", "source{ch}:voltage:low %e",
        """Control the low voltage level in Volts. (float)""",
    )

    # --- Phase ---

    phase = Channel.control(
        "source{ch}:phase:adjust?", "source{ch}:phase:adjust %g DEG",
        """Control the output phase in degrees. (float)""",
        validator=strict_range,
        values=PHASE_LIMIT,
    )

    # --- Pulse-specific ---

    pulse_duty_cycle = Channel.control(
        "source{ch}:pulse:dcycle?", "source{ch}:pulse:dcycle %.4f",
        """Control the pulse duty cycle in percent. (float)""",
        validator=strict_range,
        values=DUTY_LIMIT,
    )

    pulse_width = Channel.control(
        "source{ch}:pulse:width?", "source{ch}:pulse:width %e",
        """Control the pulse width in seconds. (float)""",
    )

    pulse_lead_time = Channel.control(
        "source{ch}:pulse:transition:leading?", "source{ch}:pulse:transition:leading %e",
        """Control the pulse leading-edge transition time in seconds. (float)""",
    )

    pulse_trail_time = Channel.control(
        "source{ch}:pulse:transition:trailing?", "source{ch}:pulse:transition:trailing %e",
        """Control the pulse trailing-edge transition time in seconds. (float)""",
    )

    # --- Output state / impedance ---

    # Mixed numeric-range + enum: the enum part still comes from `choices`.
    output_impedance = Channel.control(
        "output{ch}:impedance?", "output{ch}:impedance %s",
        """Control the output load impedance in Ohms (1–10000). (int)""",
        preprocess_input=preprocess_input_enum(choices.output_impedance),
        validator=joined_validators(strict_range, SCPI_discrete_set),
        values=[IMPEDANCE_LIMIT, choices.output_impedance],
        get_process=get_processor_default(caster=cast_to_alphanumeric,
                                          validator=strict_range,
                                          values=IMPEDANCE_LIMIT,
                                          default=choices.output_impedance.INFINITY),  # type: ignore
    )

    output_polarity = Channel.control(
        "output{ch}:polarity?", "output{ch}:polarity %s",
        """Control the output polarity ('NORMal' or 'INVerted'). (str)""",
        preprocess_input=preprocess_input_enum(choices.output_polarity),
        validator=strict_discrete_set,
        values=choices.output_polarity,
    )

    output_enabled = Channel.control(
        "output{ch}:state?", "output{ch}:state %s",
        """Get whether the channel output is enabled. (bool)""",
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_INT,
        map_values=True,
    )

    # --- AM modulation ---

    am_state = Channel.control(
        "source{ch}:am:state?", "source{ch}:am:state %s",
        """Control whether AM modulation is enabled. (bool)""",
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_ON_OFF,
        map_values=True,
    )

    am_depth = Channel.control(
        "source{ch}:am:depth?", "source{ch}:am:depth %g",
        """Control the AM modulation depth in percent (0–120). (float)""",
        validator=strict_range,
        values=[0.0, 120.0],
    )

    am_frequency = Channel.control(
        "source{ch}:am:internal:frequency?", "source{ch}:am:internal:frequency %e",
        """Control the internal AM modulation frequency in Hz. (float)""",
        validator=strict_range,
        values=[1e-3, 1e6],
    )

    am_source = Channel.control(
        "source{ch}:am:source?", "source{ch}:am:source %s",
        """Control the AM modulation source ('INTernal' or 'EXTernal'). (str)""",
        preprocess_input=preprocess_input_enum(choices.am_source),
        validator=strict_discrete_set,
        values=choices.am_source,
    )

    # --- FM modulation ---

    fm_state = Channel.control(
        "source{ch}:fm:state?", "source{ch}:fm:state %s",
        """Control whether FM modulation is enabled. (bool)""",
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_ON_OFF,
        map_values=True,
    )

    fm_deviation = Channel.control(
        "source{ch}:fm:deviation?", "source{ch}:fm:deviation %e",
        """Control the FM frequency deviation in Hz. (float)""",
    )

    fm_frequency = Channel.control(
        "source{ch}:fm:internal:frequency?", "source{ch}:fm:internal:frequency %e",
        """Control the internal FM modulation frequency in Hz. (float)""",
        validator=strict_range,
        values=[1e-3, 1e6],
    )

    fm_source = Channel.control(
        "source{ch}:fm:source?", "source{ch}:fm:source %s",
        """Control the FM modulation source ('INTernal' or 'EXTernal'). (str)""",
        preprocess_input=preprocess_input_enum(choices.fm_source),
        validator=strict_discrete_set,
        values=choices.fm_source,
    )

    # --- PM modulation ---

    pm_state = Channel.control(
        "source{ch}:pm:state?", "source{ch}:pm:state %s",
        """Control whether PM modulation is enabled. (bool)""",
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_ON_OFF,
        map_values=True,
    )

    pm_deviation = Channel.control(
        "source{ch}:pm:deviation?", "source{ch}:pm:deviation %g DEG",
        """Control the PM phase deviation in degrees (0–180). (float)""",
        validator=strict_range,
        values=[0.0, 180.0],
    )

    pm_source = Channel.control(
        "source{ch}:pm:source?", "source{ch}:pm:source %s",
        """Control the PM modulation source ('INTernal' or 'EXTernal'). (str)""",
        preprocess_input=preprocess_input_enum(choices.pm_source),
        validator=strict_discrete_set,
        values=choices.pm_source,
    )

    # --- FSK modulation ---

    fsk_state = Channel.control(
        "source{ch}:fsk:state?", "source{ch}:fsk:state %s",
        """Control whether FSK modulation is enabled. (bool)""",
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_ON_OFF,
        map_values=True,
    )

    fsk_frequency = Channel.control(
        "source{ch}:fsk:frequency?", "source{ch}:fsk:frequency %e",
        """Control the FSK hop frequency in Hz. (float)""",
        validator=strict_range,
        values=FREQ_LIMIT,
    )

    # --- Sweep ---

    sweep_state = Channel.control(
        "source{ch}:frequency:mode?", "source{ch}:frequency:mode %s",
        """Control whether frequency sweep is enabled. (bool)""",
        validator=strict_discrete_set,
        values={True: "SWEep", False: "CW"},
        map_values=True,
        get_process=lambda v: "SWEep" if v.strip().upper().startswith("SWE") else "CW",
    )

    sweep_spacing = Channel.control(
        "source{ch}:sweep:spacing?", "source{ch}:sweep:spacing %s",
        """Control the sweep spacing ('LINear' or 'LOGarithmic'). (str)""",
        preprocess_input=preprocess_input_enum(choices.sweep_spacing),
        validator=strict_discrete_set,
        values=choices.sweep_spacing,
    )

    sweep_time = Channel.control(
        "source{ch}:sweep:time?", "source{ch}:sweep:time %e",
        """Control the sweep time in seconds (1 ms – 500 s). (float)""",
        validator=strict_range,
        values=[1e-3, 500.0],
    )

    sweep_start_freq = Channel.control(
        "source{ch}:frequency:start?", "source{ch}:frequency:start %e",
        """Control the sweep start frequency in Hz. (float)""",
        validator=strict_range,
        values=FREQ_LIMIT,
    )

    sweep_stop_freq = Channel.control(
        "source{ch}:frequency:stop?", "source{ch}:frequency:stop %e",
        """Control the sweep stop frequency in Hz. (float)""",
        validator=strict_range,
        values=FREQ_LIMIT,
    )

    # --- Burst ---

    burst_state = Channel.control(
        "source{ch}:burst:state?", "source{ch}:burst:state %s",
        """Control whether burst mode is enabled. (bool)""",
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_ON_OFF,
        map_values=True,
    )

    burst_mode = Channel.control(
        "source{ch}:burst:mode?", "source{ch}:burst:mode %s",
        """Control the burst mode ('TRIGgered' or 'GATed'). (str)""",
        preprocess_input=preprocess_input_enum(choices.burst_mode),
        validator=strict_discrete_set,
        values=choices.burst_mode,
    )

    burst_count = Channel.control(
        "source{ch}:burst:ncycles?", "source{ch}:burst:ncycles %d",
        """Control the number of cycles per burst (1–1,000,000). (int)""",
        validator=strict_range,
        values=[1, 1_000_000],
        cast=int,
    )

    burst_delay = Channel.control(
        "source{ch}:burst:tdelay?", "source{ch}:burst:tdelay %e",
        """Control the burst trigger delay in seconds. (float)""",
    )

    # --- Convenience methods ---

    def enable(self):
        """Enable the channel output."""
        self.write("output{ch}:state on")

    def disable(self):
        """Disable the channel output."""
        self.write("output{ch}:state off")

    def set_waveform(self, shape="sinusoidal", frequency=1e3,
                     high_lvl=1.0, low_lvl=0.0,
                     units="VPP", phase=0.0):
        """Convenience method to configure the channel waveform in a single call.

        :param shape: Waveform shape key from :attr:`SHAPES`.
        :param frequency: Output frequency in Hz.
        :param high_lvl: High voltage level in Volts.
        :param low_lvl: Low voltage level in Volts.
        :param units: Voltage unit ('VPP', 'VRMS', or 'DBM').
        :param phase: Output phase in degrees.
        """
        assert shape in self.choices.shape, \
            "Selected shape for set_waveform must be in instrument.choices.shape"

        self.shape = shape
        self.frequency = frequency
        self.voltage_unit = units
        self.high_level = high_lvl
        self.low_level = low_lvl
        self.phase = phase


class AFG31000Choices(Choices):
    """Accepted-value enums for top-level :class:`AFG31000` commands."""

    trigger_source = str_enum_from_values("TRIGGER_SOURCES", ["INTernal", "EXTernal", "MAN", "TIM"])


class AFG31000(SCPIMixin, Instrument):
    """Represents the Tektronix AFG31000 series arbitrary function generator
    and provides a high-level interface for interacting with the instrument.

    Two-channel models (AFG31022, AFG31052, AFG31102, AFG31152, AFG31252) expose
    both :attr:`ch1` and :attr:`ch2`. Single-channel models only use :attr:`ch1`.

    .. code-block:: python

        afg = AFG31000("USB0::0x0699::0x035B::C010001::INSTR")
        afg.reset()

        afg.ch1.set_waveform(shape='sinusoidal', frequency=1e6, amplitude=1.0)
        afg.ch1.enable()

        afg.ch2.shape = 'square'
        afg.ch2.frequency = 500e3
        afg.ch2.amplitude = 2.5
        afg.ch2.pulse_duty_cycle = 30.0
        afg.ch2.enable()
    """

    #: Accepted-value enums for the top-level commands; see :class:`AFG31000Choices`
    #: (e.g. ``afg.choices.trigger_source.external``).
    choices = AFG31000Choices

    #: Fallback channel count, used only when the model cannot be resolved against
    #: :data:`AFG31000_MODELS` (unknown/future model).
    NUM_CHANNELS = 2

    def __init__(self, adapter,
                name="Tektronix AFG31000 Arbitrary Function Generator",
                model=None,
                **kwargs):
        """Initialise the AFG31000 and resolve its per-model specifications.

        :param adapter: VISA resource string or adapter for the instrument.
        :param name: Human-readable instrument name.
        :param model: Optional model number (e.g. ``'AFG31052'``). When ``None``
            (the default) the model is determined by querying ``*IDN?``; when
            given, that query is skipped and the supplied model is used instead
            (useful for tests and offline construction).
        """
        super().__init__(adapter, name, **kwargs)

        if model is None:
            #: Parsed ``*IDN?`` identification (``None`` if ``model`` was supplied).
            self.scpi_id = SCPI_ID.from_id(self.id)
            model_num = self.scpi_id.model_num
        else:
            self.scpi_id = None
            model_num = model

        #: Resolved per-model :class:`AFG31000Specs` (``None`` if the model could
        #: not be identified or is not in :data:`AFG31000_MODELS`).
        self.specs: Optional[AFG31000Specs] = None
        try:
            if not model_num:
                raise KeyError(model_num)
            self.specs = AFG31000Specs.from_registry(model_num, AFG31000_MODELS)
            channels = self.specs.channels
        except KeyError:
            logger.warning(
                "Unknown AFG31000 model %r; specs unavailable, defaulting to "
                "%d channel(s).", model_num, self.NUM_CHANNELS)
            channels = self.NUM_CHANNELS

        #: Number of output channels actually created for this unit.
        self.num_channels = channels
        for n in range(1, channels + 1):
            setattr(self, f'ch{n}', AFG31000Channel(self, n))

        #: Advanced (sequence) mode sub-instrument. Element interfaces are reached
        #: via ``self.sequence.element[n]`` (n = 1 … 256).
        self.sequence = AFG31000Sequence(self)

        #: Mass-memory and setup-memory sub-instrument. File operations target the
        #: U:/USB, M:/internal and P:/predefined drives; setup slots are 0 … 4.
        self.memory = AFG31000Memory(self)


    trigger_source = Instrument.control(
        "trigger:source?", "trigger:source %s",
        """Control the trigger source ('INTernal', 'EXTernal', 'MAN', or 'TIM'). (str)""",
        preprocess_input=preprocess_input_enum(choices.trigger_source),
        validator=strict_discrete_set,
        values=choices.trigger_source,
    )

    # --- Instrument-level commands ---

    def beep(self):
        """Emit an audible beep from the instrument."""
        self.write("system:beeper")

    def wait(self):
        """Block until all pending instrument operations complete."""
        self.write("*WAI")

    def enable_all(self):
        """Enable the output on all channels."""
        for ch_id in range(1, self.num_channels + 1):
            self.write(f"output{ch_id}:state on")

    def disable_all(self):
        """Disable the output on all channels."""
        for ch_id in range(1, self.num_channels + 1):
            self.write(f"output{ch_id}:state off")

    def align_phase(self):
        """Synchronise the phase of all channels (sets all to 0°, then triggers alignment)."""
        for n in range(1, self.num_channels + 1):
            self.write(f"source{n}:phase:adjust 0 DEG")
        self.write("source1:phase:initiate")

    # --- Instrument-level command Aliases  ---

    def set_software_trigger(self):
        """Issue a manual trigger (bus trigger)."""
        self.trigger_source = 'EXT'

    def trigger(self):
        """Issue a manual trigger (bus trigger)."""
        self.write("*TRG")


# ---------------------------------------------------------------------------
# Module-level decode tables — map SCPI query response mnemonics to
# human-readable strings.  Use these for display/logging; do not pass them
# back to the instrument.
# ---------------------------------------------------------------------------

AFG_SHAPE_DECODE = {
    "SIN":  "Sinusoidal",
    "SQU":  "Square",
    "PULS": "Pulse",
    "RAMP": "Ramp",
    "PRN":  "Pulse Noise",
    "DC":   "DC",
    "SINC": "Sinc",
    "GAUS": "Gaussian",
    "LOR":  "Lorentz",
    "ERIS": "Exponential Rise",
    "EDEC": "Exponential Decay",
    "HARV": "Haversine",
    "EFIL": "External File",
    "EMEM": "Edit Memory",
}

AFG_VOLTAGE_UNIT_DECODE = {
    "VPP":  "Peak-to-Peak Volts",
    "VRMS": "RMS Volts",
    "DBM":  "dBm",
}

AFG_BURST_MODE_DECODE = {
    "TRIG": "Triggered",
    "GAT":  "Gated",
}

AFG_SWEEP_SPACING_DECODE = {
    "LIN": "Linear",
    "LOG": "Logarithmic",
}

AFG_MOD_SOURCE_DECODE = {
    "INT": "Internal",
    "EXT": "External",
}

AFG_POLARITY_DECODE = {
    "NORM": "Normal",
    "INV":  "Inverted",
}

AFG_TRIGGER_SOURCE_DECODE = {
    "INT": "Internal",
    "EXT": "External",
    "MAN": "Manual",
}

AFG_TRIGGER_SLOPE_DECODE = {
    "POS": "Positive",
    "NEG": "Negative",
}

AFG_FREQUENCY_MODE_DECODE = {
    "CW":   "Continuous Wave",
    "SWE":  "Sweep",
    "LIST": "List",
}

AFG_SWEEP_MODE_DECODE = {
    "AUTO": "Auto",
    "MAN":  "Manual",
}

AFG_MOD_FUNCTION_DECODE = {
    "SIN":  "Sinusoidal",
    "SQU":  "Square",
    "RAMP": "Ramp",
    "PRN":  "Pulse Noise",
    "EFIL": "External File",
    "EMEM": "Edit Memory",
}

AFG_RUN_MODE_DECODE = {
    "CONT": "Continuous",
    "TRIG": "Triggered",
    "GAT":  "Gated",
    "SEQ":  "Sequenced",
}

AFG_BURST_IDLE_DECODE = {
    "STAR": "Start",
    "END":  "End",
    "FIRS": "First",
}

AFG_OUTPUT_TRIGGER_MODE_DECODE = {
    "TRIG": "Trigger Out",
    "SYNC": "Sync Out",
}

AFG_IMPEDANCE_DECODE = {
    "50":   "50 Ohm",
    "INF":  "High Impedance",
}
