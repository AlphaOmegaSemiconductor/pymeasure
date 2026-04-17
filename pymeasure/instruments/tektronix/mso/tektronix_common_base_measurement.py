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

from pymeasure.instruments import Instrument, sub_system
# from pymeasure.instruments.validators import strict_range, strict_discrete_set
# from pymeasure.instruments.values import BOOLEAN_TO_INT, BINARY, BOOLEAN_TO_ON_OFF
from pymeasure.instruments import validators, values

class Measurement(sub_system.CommandGroupSubSystem):
    """
    Represents the automated measurement system of the oscilloscope.
    
    Use the commands in the Measurement Command Group to control the automated
    measurement system. Measurement commands can set and query measurement parameters.
    You can assign parameters, such as waveform sources and reference levels,
    differently for each measurement.
    """

    # General measurement commands
    list_all = Instrument.measurement(
        'MEASUrement:LIST?',
        """Lists all currently defined measurements.
        
        Returns a comma-separated list of all measurement identifiers currently defined.
        """
    )

    delete_all = Instrument.setting(
        'MEASUrement:DELete ALL',
        """Deletes all measurements.
        
        Removes all measurement definitions from the instrument.
        """
    )

    # Add new measurement
    def add_measurement(self, meas_type: str, source1: str = None, source2: str = None):
        """
        Adds a new measurement.
        
        Args:
            meas_type: Type of measurement (e.g., "FREQUENCY", "PERIOD", "AMPLITUDE")
            source1: Primary source channel (e.g., "CH1")
            source2: Secondary source channel for dual-source measurements
        
        Returns:
            Measurement ID (e.g., "MEAS1")
        """
        cmd = f'MEASUrement:ADDNew "{meas_type}"'
        return self.parent.ask(cmd)

    def delete_measurement(self, meas_id: str):
        """
        Deletes a specific measurement.
        
        Args:
            meas_id: Measurement identifier (e.g., "MEAS1")
        """
        self.parent.write(f'MEASUrement:DELete "{meas_id}"')

    # Global measurement settings
    gating = Instrument.control(
        'MEASUrement:GATing?', 'MEASUrement:GATing %s',
        """Sets or queries the global gating setting.
        
        Controls whether measurements are made on a portion of the waveform.
        Values: {OFF|SCREen|CURSor|LOGic|SEARch|TIMe}
        OFF: No gating
        SCREen: Gate to the displayed portion
        CURSor: Gate between cursors
        LOGic: Gate based on logic state
        SEARch: Gate to search marks
        TIMe: Gate to specified time range
        """,
        validator=validators.strict_discrete_set,
        values=["OFF", "SCREEN", "SCRE", "CURSOR", "CURS", "LOGIC", "LOG", 
                "SEARCH", "SEAR", "TIME", "TIM"]
    )

    gating_start = Instrument.control(
        'MEASUrement:GATing:STARTtime?', 'MEASUrement:GATing:STARTtime %g',
        """Sets or queries the start gate time for all measurements that use Global gating.
        
        Sets the start time in seconds for time-based gating.
        """
    )

    gating_end = Instrument.control(
        'MEASUrement:GATing:ENDtime?', 'MEASUrement:GATing:ENDtime %g',
        """Sets or queries the end gate time for all measurements that use Global gating.
        
        Sets the end time in seconds for time-based gating.
        """
    )

    # Reference levels
    ref_method = Instrument.control(
        'MEASUrement:REFLevels:METHod?', 'MEASUrement:REFLevels:METHod %s',
        """Sets or queries the reference level method.
        
        Conditions:
        - PERCent: Reference levels set as percentage of signal amplitude
        - ABSolute: Reference levels set as absolute voltage values
        
        Command syntax: MEASUrement:REFLevels:METHod {PERCent|ABSolute}
        """,
        validator=validators.strict_discrete_set,
        values=["PERCENT", "PERC", "ABSOLUTE", "ABS"]
    )

    ref_abs_high = Instrument.control(
        'MEASUrement:REFLevels:ABSolute:HIGH?', 'MEASUrement:REFLevels:ABSolute:HIGH %g',
        """Sets or queries the high reference level in absolute units.
        
        Used when reference level method is set to ABSolute.
        Units are volts.
        """
    )

    ref_abs_mid = Instrument.control(
        'MEASUrement:REFLevels:ABSolute:MID?', 'MEASUrement:REFLevels:ABSolute:MID %g',
        """Sets or queries the mid reference level in absolute units.
        
        Used when reference level method is set to ABSolute.
        Units are volts.
        """
    )

    ref_abs_low = Instrument.control(
        'MEASUrement:REFLevels:ABSolute:LOW?', 'MEASUrement:REFLevels:ABSolute:LOW %g',
        """Sets or queries the low reference level in absolute units.
        
        Used when reference level method is set to ABSolute.
        Units are volts.
        """
    )

    ref_percent_high = Instrument.control(
        'MEASUrement:REFLevels:PERCent:HIGH?', 'MEASUrement:REFLevels:PERCent:HIGH %g',
        """Sets or queries the high reference level in percent.
        
        Sets the percentage (where 100% is equal to TOP and 0% is equal to BASE)
        used to calculate the high reference level.
        Default is typically 90%.
        """,
        validator=validators.strict_range,
        values=(0, 100)
    )

    ref_percent_mid = Instrument.control(
        'MEASUrement:REFLevels:PERCent:MID?', 'MEASUrement:REFLevels:PERCent:MID %g',
        """Sets or queries the mid reference level in percent.
        
        Sets the percentage (where 100% is equal to TOP and 0% is equal to BASE)
        used to calculate the mid reference level.
        Default is typically 50%.
        """,
        validator=validators.strict_range,
        values=(0, 100)
    )

    ref_percent_low = Instrument.control(
        'MEASUrement:REFLevels:PERCent:LOW?', 'MEASUrement:REFLevels:PERCent:LOW %g',
        """Sets or queries the low reference level in percent.
        
        Sets the percentage (where 100% is equal to TOP and 0% is equal to BASE)
        used to calculate the low reference level.
        Default is typically 10%.
        """,
        validator=validators.strict_range,
        values=(0, 100)
    )

    # Statistics settings
    statistics_mode = Instrument.control(
        'MEASUrement:STATIstics:MODe?', 'MEASUrement:STATIstics:MODe %s',
        """Sets or queries whether measurement statistics are enabled.
        
        When enabled, the oscilloscope calculates statistics on measurement results.
        Values: {OFF|ALL}
        """,
        validator=validators.strict_discrete_set,
        values=["OFF", "ALL"]
    )

    statistics_weighting = Instrument.control(
        'MEASUrement:STATIstics:WEIghting?', 'MEASUrement:STATIstics:WEIghting %d',
        """Sets or queries the statistics weighting factor.
        
        Specifies the time constant for mean and standard deviation statistical accumulations.
        Range: 2 to 1000
        """,
        validator=validators.strict_range,
        values=(2, 1000)
    )

    statistics_clear = Instrument.setting(
        'MEASUrement:STATIstics CLEar',
        """Clears all measurement statistics.
        
        Resets the statistics accumulators for all measurements.
        """
    )

    # Population limit
    population_limit_state = Instrument.control(
        'MEASUrement:POPUlation:LIMIT:STATE?', 'MEASUrement:POPUlation:LIMIT:STATE %s',
        """Sets or queries the global population limit state.
        
        When enabled, measurements stop after reaching the population limit.
        """,
        validator=validators.strict_discrete_set,
        values=values.BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    population_limit_value = Instrument.control(
        'MEASUrement:POPUlation:LIMIT:VALue?', 'MEASUrement:POPUlation:LIMIT:VALue %d',
        """Sets or queries the global population limit value.
        
        Sets the number of measurement samples to acquire before stopping.
        """,
        validator=validators.strict_range,
        values=(1, 1000000000)
    )

    # Measurement-specific methods for common measurements
    def get_measurement_value(self, meas_id: str):
        """
        Gets the current value of a specific measurement.
        
        Args:
            meas_id: Measurement identifier (e.g., "MEAS1")
        
        Returns:
            Current measurement value
        """
        return float(self.parent.ask(f'MEASUrement:{meas_id}:RESUlts:CURRentacq:MEAN?'))

    def get_measurement_statistics(self, meas_id: str):
        """
        Gets the statistics for a specific measurement.
        
        Args:
            meas_id: Measurement identifier (e.g., "MEAS1")
        
        Returns:
            Dictionary with mean, min, max, stdev, and population
        """
        stats = {}
        stats['mean'] = float(self.parent.ask(f'MEASUrement:{meas_id}:RESUlts:ALLAcqs:MEAN?'))
        stats['min'] = float(self.parent.ask(f'MEASUrement:{meas_id}:RESUlts:ALLAcqs:MINimum?'))
        stats['max'] = float(self.parent.ask(f'MEASUrement:{meas_id}:RESUlts:ALLAcqs:MAXimum?'))
        stats['stdev'] = float(self.parent.ask(f'MEASUrement:{meas_id}:RESUlts:ALLAcqs:STDDev?'))
        stats['population'] = int(self.parent.ask(f'MEASUrement:{meas_id}:RESUlts:ALLAcqs:POPUlation?'))
        return stats

    def configure_measurement(self, meas_id: str, meas_type: str, source1: str, source2: str = None):
        """
        Configures a measurement with type and sources.
        
        Args:
            meas_id: Measurement identifier (e.g., "MEAS1")
            meas_type: Type of measurement
            source1: Primary source
            source2: Secondary source (optional)
        """
        self.parent.write(f'MEASUrement:{meas_id}:TYPe {meas_type}')
        self.parent.write(f'MEASUrement:{meas_id}:SOUrce1 {source1}')
        if source2:
            self.parent.write(f'MEASUrement:{meas_id}:SOUrce2 {source2}')

    def set_measurement_state(self, meas_id: str, state: bool):
        """
        Enables or disables a specific measurement.
        
        Args:
            meas_id: Measurement identifier (e.g., "MEAS1")
            state: True to enable, False to disable
        """
        value = "ON" if state else "OFF"
        self.parent.write(f'MEASUrement:{meas_id}:STATE {value}')

    # Common measurement types as convenience methods
    def measure_frequency(self, source: str):
        """
        Measures frequency on the specified source.
        
        Args:
            source: Source channel (e.g., "CH1")
        
        Returns:
            Frequency in Hz
        """
        meas_id = self.add_measurement("FREQUENCY", source)
        return self.get_measurement_value(meas_id)

    def measure_period(self, source: str):
        """
        Measures period on the specified source.
        
        Args:
            source: Source channel (e.g., "CH1")
        
        Returns:
            Period in seconds
        """
        meas_id = self.add_measurement("PERIOD", source)
        return self.get_measurement_value(meas_id)

    def measure_amplitude(self, source: str):
        """
        Measures amplitude on the specified source.
        
        Args:
            source: Source channel (e.g., "CH1")
        
        Returns:
            Amplitude in volts
        """
        meas_id = self.add_measurement("AMPLITUDE", source)
        return self.get_measurement_value(meas_id)

    def measure_rise_time(self, source: str):
        """
        Measures rise time on the specified source.
        
        Args:
            source: Source channel (e.g., "CH1")
        
        Returns:
            Rise time in seconds
        """
        meas_id = self.add_measurement("RISETIME", source)
        return self.get_measurement_value(meas_id)

    def measure_fall_time(self, source: str):
        """
        Measures fall time on the specified source.
        
        Args:
            source: Source channel (e.g., "CH1")
        
        Returns:
            Fall time in seconds
        """
        meas_id = self.add_measurement("FALLTIME", source)
        return self.get_measurement_value(meas_id)

    def measure_pulse_width(self, source: str, polarity: str = "POSITIVE"):
        """
        Measures pulse width on the specified source.
        
        Args:
            source: Source channel (e.g., "CH1")
            polarity: "POSITIVE" or "NEGATIVE"
        
        Returns:
            Pulse width in seconds
        """
        meas_type = "PWIDTH" if polarity == "POSITIVE" else "NWIDTH"
        meas_id = self.add_measurement(meas_type, source)
        return self.get_measurement_value(meas_id)

    def measure_rms(self, source: str, gating: str = "SCREEN"):
        """
        Measures RMS voltage on the specified source.
        
        Args:
            source: Source channel (e.g., "CH1")
            gating: Gating type ("SCREEN", "CURSOR", etc.)
        
        Returns:
            RMS voltage
        """
        # Set gating for this measurement
        old_gating = self.gating
        self.gating = gating
        meas_id = self.add_measurement("RMS", source)
        result = self.get_measurement_value(meas_id)
        self.gating = old_gating  # Restore previous gating
        return result
