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
from typing import Iterator, List

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

from pymeasure.instruments import Instrument, sub_system
from pymeasure.instruments.validators import strict_range, strict_discrete_set
# from pymeasure.instruments.values import # ,BOOLEAN_TO_INT, BINARY, BOOLEAN_TO_ON_OFF
from pymeasure.instruments.process import normalize_str_to_upper

class TriggerLevels:
    """An indexable, writable view of the per-channel levels of one trigger.

    Indices are channel numbers, matching the front panel and the ``CH<x>``
    suffix of the underlying command, so ``levels[1]`` is CH1 and index 0 is
    not valid. Reading a single index queries just that channel; iterating,
    printing, or calling :meth:`to_list` issues one bulk query instead.

    :param trigger: The :class:`Trigger` command group used for communication.
    :param trigger_id: The trigger these levels belong to, ``'A'`` or ``'B'``.
    :param channel_count: Number of analog channels on the instrument.
    """

    def __init__(self, trigger, trigger_id: str, channel_count: int) -> None:
        self.trigger = trigger
        self.trigger_id = trigger_id
        self.channel_count = channel_count

    def _validate_channel(self, channel: int) -> int:
        """Return ``channel`` unchanged, or raise if it is not a valid channel number."""
        if channel not in range(1, self.channel_count + 1):
            raise IndexError(
                f"Channel {channel!r} is out of range, "
                f"expected a channel number from 1 to {self.channel_count}."
            )
        return channel

    def __getitem__(self, channel: int) -> float:
        """Return the trigger level of ``channel``, in volts."""
        self._validate_channel(channel)
        return self.trigger.values(
            f'TRIGger:{self.trigger_id}:LEVel:CH{channel}?')[0]

    def __setitem__(self, channel: int, level: float) -> None:
        """Set the trigger level of ``channel`` to ``level`` volts."""
        self._validate_channel(channel)
        self.trigger.write(
            f'TRIGger:{self.trigger_id}:LEVel:CH{channel} {level:g}')

    def __len__(self) -> int:
        """Return the number of channels covered by this view."""
        return self.channel_count

    def __iter__(self) -> Iterator[float]:
        """Iterate over the levels of every channel, lowest channel number first."""
        return iter(self.to_list())

    def to_list(self) -> List[float]:
        """Return the levels of every channel in a single query, CH1 first."""
        return self.trigger.values(
            f'TRIGger:{self.trigger_id}:LEVel?', separator=';')

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.trigger_id!r}, {self.to_list()})"


# TODO: This will need to be refactored, the trigger sub system is complicated 
# TODO refactor this into primary and secondary triggers (A and B), (might want a base trigger?)
class Trigger(sub_system.CommandGroupSubSystem):
    """
    Represents the trigger system of the oscilloscope.
    
    Use the commands in the Trigger Command Group to control all aspects of
    triggering for the instrument. There are two triggers: A and B. Where appropriate,
    the command set has parallel constructions for each trigger.
    
    You can set the A or B triggers to edge mode. Edge triggering lets you display
    a waveform at or near the point where the signal passes through a voltage level
    of your choosing.
    
    You can also set A or B triggers to pulse or logic modes. With pulse triggering,
    the instrument triggers whenever it detects a pulse of a certain width or height.
    Logic triggering lets you logically combine the signals on one or more channels.
    The instrument then triggers when it detects a certain combination of signal levels.
    """

    def __init__(self, parent, command_group_name=None, *args, **kwargs) -> None:
        super().__init__(parent, command_group_name, *args, **kwargs)
        self._a_level = TriggerLevels(self, 'A', parent.analog_channels_count)
        self._b_level = TriggerLevels(self, 'B', parent.analog_channels_count)

    # Force trigger
    force = Instrument.setting(
        'TRIGger:FORCe',
        """Forces a trigger event to occur.
        
        Creates an immediate trigger event, regardless of whether trigger conditions
        are met. This is useful for single-shot acquisitions.
        """
    )

    # Trigger A properties (most commonly used trigger)
    a_edge_coupling = Instrument.control(
        'TRIGger:A:EDGE:COUPling?', 'TRIGger:A:EDGE:COUPling %s',
        """Sets or queries the trigger coupling for edge trigger.
        
        Conditions:
        - DC: DC coupling (passes all signal components)
        - AC: AC coupling (blocks DC component)
        - HFRej: High frequency reject (attenuates signals above 50 kHz)
        - LFRej: Low frequency reject (attenuates signals below 50 kHz)
        - NOISErej: Reduces trigger sensitivity to reduce triggering on noise
        
        Command syntax: TRIGger:A:EDGE:COUPling {DC|AC|HFRej|LFRej|NOISErej}
        """,
        validator=strict_discrete_set,
        values=["DC", "AC", "HFREJ", "HFR", "LFREJ", "LFR", "NOISEREJ", "NOIS"]
    )

    a_edge_slope = Instrument.control(
        'TRIGger:A:EDGE:SLOpe?', 'TRIGger:A:EDGE:SLOpe %s',
        """Sets or queries the trigger slope for edge trigger.
        
        Controls whether the oscilloscope triggers on the rising or falling edge.
        Values: {RISe|FALL|EITHer}
        RISe: Trigger on rising (positive-going) edge
        FALL: Trigger on falling (negative-going) edge
        EITHer: Trigger on either edge
        """,
        validator=strict_discrete_set,
        values=["RISE", "RIS", "FALL", "EITHER", "EITH"]
    )

    #TODO we need to accept str or an int and then cast the into to f"CH{number}"
    a_edge_source = Instrument.control(
        'TRIGger:A:EDGE:SOUrce?', 'TRIGger:A:EDGE:SOUrce %s',
        """Sets or queries the trigger source for edge trigger.
        
        Specifies which signal to use as the trigger source.
        Examples: CH1, CH2, CH3, CH4, LINE, AUX, etc.
        """
    )

    a_holdoff_time = Instrument.control(
        'TRIGger:A:HOLDoff:TIMe?', 'TRIGger:A:HOLDoff:TIMe %g',
        """Sets or queries the trigger holdoff time.
        
        Sets the time period after a trigger during which the trigger system
        will not respond to additional trigger events. Units are seconds.
        """
    )

    a_holdoff_mode = Instrument.control(
        'TRIGger:A:HOLDoff:BY?', 'TRIGger:A:HOLDoff:BY %s',
        """Sets or queries whether trigger holdoff is based on time or events.
        
        Values: {TIMe|EVENts}
        TIMe: Holdoff by time period
        EVENts: Holdoff by number of events
        """,
        validator=strict_discrete_set,
        values=["TIME", "TIM", "EVENTS", "EVEN"]
    )

    @property
    def a_level(self) -> TriggerLevels:
        """Control the A trigger level of each channel, in volts.

        The returned view is indexed by channel number, so index 1 is CH1::

            scope.trigger.a_level[1] = 0.5   # set CH1 to 0.5 V
            scope.trigger.a_level[1]         # -> 0.5
            list(scope.trigger.a_level)      # -> every channel, CH1 first

        Assigning to the attribute itself writes ``TRIGger:A:LEVel``, which
        applies a single level to every channel at once::

            scope.trigger.a_level = 0.5
        """
        return self._a_level

    @a_level.setter
    def a_level(self, level: float) -> None:
        self.write(f'TRIGger:A:LEVel {level:g}')

    a_mode = Instrument.control(
        'TRIGger:A:MODe?', 'TRIGger:A:MODe %s',
        """Sets or queries the trigger mode.
        
        Values: {AUTO|NORMal}
        AUTO: Automatically triggers periodically if no trigger event detected
        NORMal: Triggers only when trigger conditions are met
        """,
        preprocess_input = normalize_str_to_upper,
        validator=strict_discrete_set,
        set_process = normalize_str_to_upper,
        values=["AUTO", "NORMAL", "NORM"]
    )

    a_type = Instrument.control(
        'TRIGger:A:TYPe?', 'TRIGger:A:TYPe %s',
        """Sets or queries the type of A trigger.
        
        Sets what type of event will trigger the oscilloscope.
        Common values: {EDGE|PULSEWidth|RUNT|LOGic|SETHold|TRANsition|BUS}
        EDGE: Edge trigger (most common)
        PULSEWidth: Trigger on pulse width
        RUNT: Trigger on runt pulses
        LOGic: Logic pattern trigger
        SETHold: Setup and hold trigger
        TRANsition: Rise/fall time trigger
        BUS: Serial bus trigger
        """,
        validator=strict_discrete_set,
        set_process = normalize_str_to_upper,
        values=["EDGE", "PULSEWIDTH", "PULSE", "RUNT", "LOGIC", "LOG",
                "SETHOLD", "SETH", "TRANSITION", "TRAN", "BUS"]
    )

    # Pulse width trigger properties
    a_pulsewidth_highlimit = Instrument.control(
        'TRIGger:A:PULSEWidth:HIGHLimit?', 'TRIGger:A:PULSEWidth:HIGHLimit %g',
        """Sets or queries the upper limit for pulse width trigger.
        
        Sets or queries the upper limit to use, in seconds, when triggering on detection
        of a pulse whose duration is inside or outside a range of two values.
        """
    )

    a_pulsewidth_lowlimit = Instrument.control(
        'TRIGger:A:PULSEWidth:LOWLimit?', 'TRIGger:A:PULSEWidth:LOWLimit %g',
        """Sets or queries the lower limit for pulse width trigger.
        
        Sets or queries the lower limit to use, in seconds, when triggering on detection
        of a pulse whose duration is inside or outside a range of two values.
        """
    )

    a_pulsewidth_polarity = Instrument.control(
        'TRIGger:A:PULSEWidth:POLarity?', 'TRIGger:A:PULSEWidth:POLarity %s',
        """Sets or queries the polarity for pulse width trigger.
        
        Values: {POSitive|NEGative}
        POSitive: Trigger on positive pulses
        NEGative: Trigger on negative pulses
        """,
        validator=strict_discrete_set,
        set_process = normalize_str_to_upper,
        values=["POSITIVE", "POS", "NEGATIVE", "NEG"]
    )

    a_pulsewidth_source = Instrument.control(
        'TRIGger:A:PULSEWidth:SOUrce?', 'TRIGger:A:PULSEWidth:SOUrce %s',
        """Sets or queries the source waveform for pulse width trigger.
        
        Specifies which channel to monitor for pulse width triggering.
        """
    )

    a_pulsewidth_when = Instrument.control(
        'TRIGger:A:PULSEWidth:WHEn?', 'TRIGger:A:PULSEWidth:WHEn %s',
        """Sets or queries when to trigger based on pulse width.
        
        Sets or queries to trigger when a pulse is detected with a width (duration)
        that is less than, greater than, equal to, or unequal to a specified value.
        Values: {LESSthan|MOREthan|EQual|UNEQual|WIThin|OUTside}
        """,
        validator=strict_discrete_set,
        set_process = normalize_str_to_upper,
        values=["LESSTHAN", "LESS", "MORETHAN", "MORE", "EQUAL", "EQ",
                "UNEQUAL", "UNEQ", "WITHIN", "WITH", "OUTSIDE", "OUTS"]
    )

    # Trigger B properties (secondary trigger)
    b_edge_coupling = Instrument.control(
        'TRIGger:B:EDGE:COUPling?', 'TRIGger:B:EDGE:COUPling %s',
        """Sets or queries the B trigger coupling for edge trigger.
        
        Same options as A trigger coupling.
        """,
        validator=strict_discrete_set,
        set_process = normalize_str_to_upper,
        values=["DC", "AC", "HFREJ", "HFR", "LFREJ", "LFR", "NOISEREJ", "NOIS"]
    )

    b_edge_slope = Instrument.control(
        'TRIGger:B:EDGE:SLOpe?', 'TRIGger:B:EDGE:SLOpe %s',
        """Sets or queries the B trigger slope for edge trigger.
        
        Same options as A trigger slope.
        """,
        validator=strict_discrete_set,
        set_process = normalize_str_to_upper,
        values=["RISE", "RIS", "FALL", "EITHER", "EITH"]
    )

    b_edge_source = Instrument.control(
        'TRIGger:B:EDGE:SOUrce?', 'TRIGger:B:EDGE:SOUrce %s',
        """Sets or queries the B trigger source for edge trigger.
        
        Specifies which signal to use as the B trigger source.
        """
    )

    @property
    def b_level(self) -> TriggerLevels:
        """Control the B trigger level of each channel, in volts.

        Indexed by channel number exactly like :attr:`a_level`::

            scope.trigger.b_level[1] = 0.5   # set CH1 to 0.5 V

        Assigning to the attribute itself writes ``TRIGger:B:LEVel``, applying
        a single level to every channel at once.
        """
        return self._b_level

    @b_level.setter
    def b_level(self, level: float) -> None:
        self.write(f'TRIGger:B:LEVel {level:g}')

    b_type = Instrument.control(
        'TRIGger:B:TYPe?', 'TRIGger:B:TYPe %s',
        """Sets or queries the type of B trigger.
        
        Same options as A trigger type.
        """,
        validator=strict_discrete_set,
        set_process = normalize_str_to_upper,
        values=["EDGE", "PULSEWIDTH", "PULSE", "RUNT", "LOGIC", "LOG",
                "SETHOLD", "SETH", "TRANSITION", "TRAN", "BUS"]
    )

    # Trigger state and frequency
    state = Instrument.measurement(
        'TRIGger:STATE?',
        """Returns the current state of the trigger system.
        
        Returns: {ARMED|AUTO|READY|SAVE|TRIGGER}
        ARMED: Trigger armed and waiting for trigger event
        AUTO: Auto trigger mode active
        READY: Ready to accept trigger
        SAVE: Trigger system saving data
        TRIGGER: Trigger event detected
        """
    )

    frequency = Instrument.measurement(
        'TRIGger:FREQuency?',
        """Returns the trigger frequency.
        
        Returns the rate at which trigger events are occurring, in Hz.
        """
    )

    # Set trigger to 50% automatically
    set_level = Instrument.setting(
        'TRIGger:A SETLevel',
        """Sets the A trigger level automatically to 50% of the signal range.
        
        Automatically adjusts the trigger level to the midpoint of the signal
        amplitude on the selected source.
        """
    )

    b_set_level = Instrument.setting(
        'TRIGger:B SETLevel',
        """Sets the B trigger level automatically to 50% of the signal range.
        
        Automatically adjusts the B trigger level to the midpoint of the signal
        amplitude on the selected source.
        """
    )

    b_reset = Instrument.setting(
        'TRIGger:B:RESET',
        """Resets the B trigger to its default settings.
        
        Returns all B trigger settings to factory defaults.
        """
    )
