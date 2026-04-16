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
from pymeasure.instruments.validators import strict_range, strict_discrete_set
from pymeasure.instruments.values import BOOLEAN_TO_ON_OFF, str_enum_from_values


class AFG31000Channel(Channel):
    """Represents a single output channel of the Tektronix AFG31000 series.

    Commands are automatically prefixed with ``source{id}:`` via :meth:`insert_id`.
    Output-state commands use the ``output{id}:`` prefix and are sent via ``self.parent``.
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
        "haversine": "HAV",
        "user": "USER",
        "emem": "EMEMory",
    }

    FREQ_LIMIT = [1e-6, 250e6]
    DUTY_LIMIT = [0.001, 99.999]
    PHASE_LIMIT = [-360.0, 360.0]
    AMPLITUDE_VPP_LIMIT = [2e-3, 20.0]   # high-Z; 50 Ω limit is 1mVpp–10Vpp
    OFFSET_LIMIT = [-10.0, 10.0]
    IMPEDANCE_LIMIT = [1, 10000]
    VOLTAGE_UNITS = str_enum_from_values("VOLTAGE_UNITS", ["VPP", "VRMS", "DBM"])
    BURST_MODES   = str_enum_from_values("BURST_MODES",   ["TRIGgered", "GATed", "INFinity"])
    SWEEP_TYPES   = str_enum_from_values("SWEEP_TYPES",   ["LINear", "LOGarithmic"])
    MOD_SOURCES   = str_enum_from_values("MOD_SOURCES",   ["INTernal", "EXTernal"])
    POLARITY      = str_enum_from_values("POLARITY",      ["NORMal", "INVerted"])

    # --- Waveform shape ---

    shape = Channel.control(
        "function:shape?", "function:shape %s",
        """Control the output waveform shape. (str)

        Accepted values: 'sinusoidal', 'square', 'pulse', 'ramp', 'prnoise',
        'dc', 'sinc', 'gaussian', 'lorentz', 'erise', 'edecay', 'haversine',
        'user', 'emem'.
        """,
        validator=strict_discrete_set,
        values=SHAPES,
        map_values=True,
    )

    # --- Frequency ---

    frequency = Channel.control(
        "frequency:fixed?", "frequency:fixed %e",
        """Control the output frequency in Hz. (float)""",
        validator=strict_range,
        values=FREQ_LIMIT,
    )

    # --- Amplitude / voltage ---

    voltage_unit = Channel.control(
        "voltage:unit?", "voltage:unit %s",
        """Control the voltage unit ('VPP', 'VRMS', or 'DBM'). (str)""",
        validator=strict_discrete_set,
        values=VOLTAGE_UNITS,
    )

    amplitude = Channel.control(
        "voltage:amplitude?", "voltage:amplitude %e",
        """Control the output amplitude in the current voltage unit. (float)""",
        validator=strict_range,
        values=AMPLITUDE_VPP_LIMIT,
    )

    offset = Channel.control(
        "voltage:offset?", "voltage:offset %e",
        """Control the DC offset in Volts. (float)""",
        validator=strict_range,
        values=OFFSET_LIMIT,
    )

    high_level = Channel.control(
        "voltage:high?", "voltage:high %e",
        """Control the high voltage level in Volts. (float)""",
    )

    low_level = Channel.control(
        "voltage:low?", "voltage:low %e",
        """Control the low voltage level in Volts. (float)""",
    )

    # --- Phase ---

    phase = Channel.control(
        "phase:initiate?", "phase:initiate %g DEG",
        """Control the output phase in degrees. (float)""",
        validator=strict_range,
        values=PHASE_LIMIT,
    )

    # --- Pulse-specific ---

    pulse_duty_cycle = Channel.control(
        "pulse:dcycle?", "pulse:dcycle %.4f",
        """Control the pulse duty cycle in percent. (float)""",
        validator=strict_range,
        values=DUTY_LIMIT,
    )

    pulse_width = Channel.control(
        "pulse:width?", "pulse:width %e",
        """Control the pulse width in seconds. (float)""",
    )

    pulse_lead_time = Channel.control(
        "pulse:transition:leading?", "pulse:transition:leading %e",
        """Control the pulse leading-edge transition time in seconds. (float)""",
    )

    pulse_trail_time = Channel.control(
        "pulse:transition:trailing?", "pulse:transition:trailing %e",
        """Control the pulse trailing-edge transition time in seconds. (float)""",
    )

    # --- Output state / impedance ---

    output_impedance = Channel.control(
        "output:impedance?", "output:impedance %d",
        """Control the output load impedance in Ohms (1–10000, or 'INFinity'). (int)""",
        validator=strict_range,
        values=IMPEDANCE_LIMIT,
        cast=int,
    )

    output_polarity = Channel.control(
        "output:polarity?", "output:polarity %s",
        """Control the output polarity ('NORMal' or 'INVerted'). (str)""",
        validator=strict_discrete_set,
        values=POLARITY,
    )

    # --- AM modulation ---

    am_state = Channel.control(
        "am:state?", "am:state %s",
        """Control whether AM modulation is enabled. (bool)""",
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True,
    )

    am_depth = Channel.control(
        "am:depth?", "am:depth %g",
        """Control the AM modulation depth in percent (0–120). (float)""",
        validator=strict_range,
        values=[0.0, 120.0],
    )

    am_frequency = Channel.control(
        "am:internal:frequency?", "am:internal:frequency %e",
        """Control the internal AM modulation frequency in Hz. (float)""",
        validator=strict_range,
        values=[1e-3, 50e3],
    )

    am_source = Channel.control(
        "am:source?", "am:source %s",
        """Control the AM modulation source ('INTernal' or 'EXTernal'). (str)""",
        validator=strict_discrete_set,
        values=MOD_SOURCES,
    )

    # --- FM modulation ---

    fm_state = Channel.control(
        "fm:state?", "fm:state %s",
        """Control whether FM modulation is enabled. (bool)""",
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True,
    )

    fm_deviation = Channel.control(
        "fm:deviation?", "fm:deviation %e",
        """Control the FM frequency deviation in Hz. (float)""",
    )

    fm_frequency = Channel.control(
        "fm:internal:frequency?", "fm:internal:frequency %e",
        """Control the internal FM modulation frequency in Hz. (float)""",
        validator=strict_range,
        values=[1e-3, 50e3],
    )

    fm_source = Channel.control(
        "fm:source?", "fm:source %s",
        """Control the FM modulation source ('INTernal' or 'EXTernal'). (str)""",
        validator=strict_discrete_set,
        values=MOD_SOURCES,
    )

    # --- PM modulation ---

    pm_state = Channel.control(
        "pm:state?", "pm:state %s",
        """Control whether PM modulation is enabled. (bool)""",
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True,
    )

    pm_deviation = Channel.control(
        "pm:deviation?", "pm:deviation %g",
        """Control the PM phase deviation in degrees. (float)""",
        validator=strict_range,
        values=[0.0, 360.0],
    )

    pm_source = Channel.control(
        "pm:source?", "pm:source %s",
        """Control the PM modulation source ('INTernal' or 'EXTernal'). (str)""",
        validator=strict_discrete_set,
        values=MOD_SOURCES,
    )

    # --- FSK modulation ---

    fsk_state = Channel.control(
        "fsk:state?", "fsk:state %s",
        """Control whether FSK modulation is enabled. (bool)""",
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True,
    )

    fsk_frequency = Channel.control(
        "fsk:frequency?", "fsk:frequency %e",
        """Control the FSK hop frequency in Hz. (float)""",
        validator=strict_range,
        values=FREQ_LIMIT,
    )

    # --- Sweep ---

    sweep_state = Channel.control(
        "sweep:state?", "sweep:state %s",
        """Control whether frequency sweep is enabled. (bool)""",
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True,
    )

    sweep_type = Channel.control(
        "sweep:type?", "sweep:type %s",
        """Control the sweep type ('LINear' or 'LOGarithmic'). (str)""",
        validator=strict_discrete_set,
        values=SWEEP_TYPES,
    )

    sweep_time = Channel.control(
        "sweep:time?", "sweep:time %e",
        """Control the sweep time in seconds (1 ms – 300 s). (float)""",
        validator=strict_range,
        values=[1e-3, 300.0],
    )

    sweep_start_freq = Channel.control(
        "frequency:start?", "frequency:start %e",
        """Control the sweep start frequency in Hz. (float)""",
        validator=strict_range,
        values=FREQ_LIMIT,
    )

    sweep_stop_freq = Channel.control(
        "frequency:stop?", "frequency:stop %e",
        """Control the sweep stop frequency in Hz. (float)""",
        validator=strict_range,
        values=FREQ_LIMIT,
    )

    # --- Burst ---

    burst_state = Channel.control(
        "burst:state?", "burst:state %s",
        """Control whether burst mode is enabled. (bool)""",
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True,
    )

    burst_mode = Channel.control(
        "burst:mode?", "burst:mode %s",
        """Control the burst mode ('TRIGgered', 'GATed', or 'INFinity'). (str)""",
        validator=strict_discrete_set,
        values=BURST_MODES,
    )

    burst_count = Channel.control(
        "burst:ncycles?", "burst:ncycles %d",
        """Control the number of cycles per burst (1–1,000,000). (int)""",
        validator=strict_range,
        values=[1, 1_000_000],
        cast=int,
    )

    burst_delay = Channel.control(
        "burst:delay?", "burst:delay %e",
        """Control the burst delay in seconds. (float)""",
    )

    # --- id routing ---

    def insert_id(self, command):
        """Prepend ``source{id}:`` to every channel command."""
        return f"source{self.id}:{command}"

    # --- Convenience methods ---

    def enable(self):
        """Enable the channel output."""
        self.parent.write(f"output{self.id}:state on")

    def disable(self):
        """Disable the channel output."""
        self.parent.write(f"output{self.id}:state off")

    @property
    def output_enabled(self):
        """Return True if the channel output is enabled."""
        return self.parent.ask(f"output{self.id}:state?").strip().upper() in ("ON", "1")

    def set_waveform(self, shape="sinusoidal", frequency=1e3, amplitude=1.0,
                     offset=0.0, units="VPP", phase=0.0):
        """Convenience method to configure the channel waveform in a single call.

        :param shape: Waveform shape key from :attr:`SHAPES`.
        :param frequency: Output frequency in Hz.
        :param amplitude: Output amplitude in the chosen unit.
        :param offset: DC offset in Volts.
        :param units: Voltage unit ('VPP', 'VRMS', or 'DBM').
        :param phase: Output phase in degrees.
        """
        scpi_shape = strict_discrete_set(shape, self.SHAPES)
        if scpi_shape in self.SHAPES:
            scpi_shape = self.SHAPES[scpi_shape]
        self.write(f"function:shape {scpi_shape}")
        self.write(f"frequency:fixed {frequency:e}")
        self.write(f"voltage:unit {units}")
        self.write(f"voltage:amplitude {amplitude:e}")
        self.write(f"voltage:offset {offset:e}")
        self.write(f"phase:initiate {phase:g} DEG")


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

    def __init__(self, adapter,
                 name="Tektronix AFG31000 Arbitrary Function Generator",
                 channels=2,
                 **kwargs):
        super().__init__(adapter, name, **kwargs)
        self._num_channels = channels
        self.ch1 = AFG31000Channel(self, 1)
        if channels >= 2:
            self.ch2 = AFG31000Channel(self, 2)

    # --- Instrument-level commands ---

    def reset(self):
        """Reset the instrument to factory defaults."""
        self.write("*RST")

    def beep(self):
        """Emit an audible beep from the instrument."""
        self.write("system:beep")

    def opc(self):
        """Return 1 when all pending operations are complete."""
        return int(self.ask("*OPC?"))

    def wait(self):
        """Block until all pending instrument operations complete."""
        self.write("*WAI")

    @property
    def error(self):
        """Return the next error string from the error queue."""
        return self.ask("system:error?")

    def enable_all(self):
        """Enable the output on all channels."""
        for ch_id in range(1, self._num_channels + 1):
            self.write(f"output{ch_id}:state on")

    def disable_all(self):
        """Disable the output on all channels."""
        for ch_id in range(1, self._num_channels + 1):
            self.write(f"output{ch_id}:state off")

    def align_phase(self):
        """Synchronise the phase of both channels (sets both to 0° simultaneously)."""
        self.write("source1:phase:initiate 0 DEG")
        if self._num_channels >= 2:
            self.write("source2:phase:initiate 0 DEG")
        self.write("source1:phase:initiate")  # triggers phase alignment

    @property
    def trigger_source(self):
        """Return the trigger source ('INTernal', 'EXTernal', or 'MAN')."""
        return self.ask("trigger:source?").strip()

    @trigger_source.setter
    def trigger_source(self, value):
        value = strict_discrete_set(value, self.TRIGGER_SOURCES)
        self.write(f"trigger:source {value}")

    def trigger(self):
        """Issue a manual trigger (bus trigger)."""
        self.write("*TRG")
