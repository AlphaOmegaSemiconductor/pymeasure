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
from pymeasure.instruments.process import get_processor_default, set_processor_dict_map
from pymeasure.instruments.validators import strict_range, strict_discrete_set, joined_validators, cast_to_alphanumeric, SCPI_discrete_set
from pymeasure.instruments.values import BOOLEAN_TO_ON_OFF, BOOLEAN_TO_INT, str_enum_from_values


class AFG31000Channel(Channel):
    """Represents a single output channel of the Tektronix AFG31000 series.

    Commands use the ``source{ch}:`` prefix for source commands and ``output{ch}:``
    for output-state commands, both resolved via :meth:`Channel.insert_id`.
    """

    SHAPES = {
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
        "efile": "EFIL",
        "emem": "EMEM",
    }

    FREQ_LIMIT = [1e-6, 250e6]
    DUTY_LIMIT = [0.001, 99.999]
    PHASE_LIMIT = [-180.0, 180.0]
    AMPLITUDE_VPP_LIMIT = [2e-3, 20.0]   # high-Z; 50 Ω limit is 1mVpp–10Vpp
    OFFSET_LIMIT = [-10.0, 10.0]
    IMPEDANCE_LIMIT = [1, 10000]
    IMPEDANCE_OPTIONS = str_enum_from_values("IMPEDANCE_OPTIONS", ["INFinity","MINimum","MAXimum"])
    VOLTAGE_UNITS = str_enum_from_values("VOLTAGE_UNITS", ["VPP", "VRMS", "DBM"])
    BURST_MODES   = str_enum_from_values("BURST_MODES",   ["TRIGgered", "GATed"])
    SWEEP_TYPES   = str_enum_from_values("SWEEP_TYPES",   ["LINear", "LOGarithmic"])
    MOD_SOURCES   = str_enum_from_values("MOD_SOURCES",   ["INTernal", "EXTernal"])
    POLARITY      = str_enum_from_values("POLARITY",      ["NORMal", "INVerted"])

    # --- Waveform shape ---

    shape = Channel.control(
        "source{ch}:function:shape?", "source{ch}:function:shape %s",
        """Control the output waveform shape. (str)

        Accepted values: 'sinusoidal', 'square', 'pulse', 'ramp', 'prnoise',
        'dc', 'sinc', 'gaussian', 'lorentz', 'erise', 'edecay', 'haversine',
        'efile', 'emem'.
        """,
        preprocess_input=set_processor_dict_map(SHAPES),
        validator=strict_discrete_set,
        values=SHAPES,
        map_values=True,
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
        validator=strict_discrete_set,
        values=VOLTAGE_UNITS,
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

    output_impedance = Channel.control(
        "output{ch}:impedance?", "output{ch}:impedance %s",
        """Control the output load impedance in Ohms (1–10000). (int)""",
        validator=joined_validators(strict_range, SCPI_discrete_set),
        values=[IMPEDANCE_LIMIT, IMPEDANCE_OPTIONS],
        get_process= get_processor_default(caster=cast_to_alphanumeric,
                                        validator=strict_range,
                                        values=IMPEDANCE_LIMIT,
                                        default=IMPEDANCE_OPTIONS.INFINITY),
    )

    output_polarity = Channel.control(
        "output{ch}:polarity?", "output{ch}:polarity %s",
        """Control the output polarity ('NORMal' or 'INVerted'). (str)""",
        validator=strict_discrete_set,
        values=POLARITY,
    )

    output_enabled = Channel.control(
        "output{ch}:state?", "output{ch}:state %s",
        """Get whether the channel output is enabled. (bool)""",
        validator=strict_discrete_set,
        values=BOOLEAN_TO_INT,
        map_values=True,
    )

    # --- AM modulation ---

    am_state = Channel.control(
        "source{ch}:am:state?", "source{ch}:am:state %s",
        """Control whether AM modulation is enabled. (bool)""",
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
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
        validator=strict_discrete_set,
        values=MOD_SOURCES,
    )

    # --- FM modulation ---

    fm_state = Channel.control(
        "source{ch}:fm:state?", "source{ch}:fm:state %s",
        """Control whether FM modulation is enabled. (bool)""",
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
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
        validator=strict_discrete_set,
        values=MOD_SOURCES,
    )

    # --- PM modulation ---

    pm_state = Channel.control(
        "source{ch}:pm:state?", "source{ch}:pm:state %s",
        """Control whether PM modulation is enabled. (bool)""",
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
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
        validator=strict_discrete_set,
        values=MOD_SOURCES,
    )

    # --- FSK modulation ---

    fsk_state = Channel.control(
        "source{ch}:fsk:state?", "source{ch}:fsk:state %s",
        """Control whether FSK modulation is enabled. (bool)""",
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
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
        validator=strict_discrete_set,
        values=SWEEP_TYPES,
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
        values=BOOLEAN_TO_ON_OFF,
        map_values=True,
    )

    burst_mode = Channel.control(
        "source{ch}:burst:mode?", "source{ch}:burst:mode %s",
        """Control the burst mode ('TRIGgered' or 'GATed'). (str)""",
        validator=strict_discrete_set,
        values=BURST_MODES,
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
        assert shape in self.SHAPES, "Selected Shape for Set_Waveform must be in instrument.SHAPES"

        self.shape = shape
        self.frequency = frequency
        self.voltage_unit = units
        self.high_level = high_lvl
        self.low_level = low_lvl
        self.phase = phase


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

    TRIGGER_SOURCES = str_enum_from_values("TRIGGER_SOURCES", ["INTernal", "EXTernal", "MAN"])
    NUM_CHANNELS = 2

    def __init__(self, adapter,
                name="Tektronix AFG31000 Arbitrary Function Generator",
                **kwargs):
        super().__init__(adapter, name, **kwargs)

        assert self.NUM_CHANNELS > 0
        for n in range(1, self.NUM_CHANNELS + 1):
            setattr(self, f'ch{n}', AFG31000Channel(self, n))

        self.reset()

    # --- Instrument-level commands ---

    def beep(self):
        """Emit an audible beep from the instrument."""
        self.write("system:beeper")

    def wait(self):
        """Block until all pending instrument operations complete."""
        self.write("*WAI")

    def enable_all(self):
        """Enable the output on all channels."""
        for ch_id in range(1, self.NUM_CHANNELS + 1):
            self.write(f"output{ch_id}:state on")

    def disable_all(self):
        """Disable the output on all channels."""
        for ch_id in range(1, self.NUM_CHANNELS + 1):
            self.write(f"output{ch_id}:state off")

    def align_phase(self):
        """Synchronise the phase of all channels (sets all to 0°, then triggers alignment)."""
        for n in range(1, self.NUM_CHANNELS + 1):
            self.write(f"source{n}:phase:adjust 0 DEG")
        self.write("source1:phase:initiate")

    trigger_source = Instrument.control(
        "trigger:source?", "trigger:source %s",
        """Control the trigger source ('INTernal', 'EXTernal', or 'MAN'). (str)""",
        validator=strict_discrete_set,
        values=TRIGGER_SOURCES,
    )

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
