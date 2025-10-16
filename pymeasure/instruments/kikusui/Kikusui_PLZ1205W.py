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

from pymeasure.instruments import Instrument, SCPIMixin
from pymeasure.instruments.validators import strict_range, strict_discrete_set
from pymeasure.instruments.values import BOOLEAN_TO_INT, RANGE_ENUM_LMH
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

MFG = "Kikusui"
MODEL = "PLZ1205W"


current_range_values = {'low' : 2.4, # in amps
                        'med' : 24, #in amps
                        'high' : 240 # in amps
                        }

class PLZ1205W(SCPIMixin, Instrument):
    f""" Represents the {MFG} {MODEL} Power supply
    interface for interacting with the instrument.

    .. code-block:: python
        from pymeasure.instruments import {MFG}
        load = {MFG}.{MODEL}(resource)
        load.current_setpoint=10
        load.current_range = load.range.MED
        load.output_enabled=True
        print(load.voltage_measure)
    """
    Range = RANGE_ENUM_LMH

    def __init__(self, adapter, name=f"{MFG} {MODEL}", **kwargs):
        super().__init__(
            adapter, name, **kwargs
        )

    load_setpoint = current_setpoint = Instrument.control(
        "CURR?",
        "CURR %g",
        """Control the load current, accuray depends on range setting.""",
        validator=strict_range,
        values=[0, 240],
        dynamic=True,
    )

    current_slew_rate = Instrument.control(
        "CURR:SLEW?",
        "CURR:SLEW %g",
        """Control the load current slew rate in A/us. ([SOURce:]CURRent:SLEWrate <value>)""",
        validator=strict_range,
        values=[0.060, 60],
        dynamic=True,
    )

    current_range = Instrument.control(
        "CURR:RANG?", "CURR:RANG %s",
        """ Controls the DC current range.""",
        validator=strict_discrete_set,
        values=["LOW", "MED", "HIGH"]
    )
    
    volt_range = Instrument.control(
        "VOLT:RANG?", "VOLT:RANG %s",
        """ Controls the DC current range.""",
        validator=strict_discrete_set,
        values=["LOW", "HIGH"]
    )

    voltage_measure = Instrument.measurement(
        "MEASure:VOLTage:DC?",
        """Measure actual voltage of the load."""
    )

    current_measure = Instrument.measurement(
        "MEAS:CURRent:DC?",
        """Measure the actual current of the load."""
    )

    power_measure = Instrument.measurement(
        "MEAS:POW:DC?",
        """Measure the actual power of the load, (volt X current)"""
    )

    output_enabled = Instrument.control(
        "OUTP?",
        "OUTP %d",
        """Control whether the output/operation is enabled (boolean).""",
        validator=strict_discrete_set,
        map_values=True,
        values=BOOLEAN_TO_INT,
    )

    abort = Instrument.setting(
        "ABOR",
        """abort the operation."""
    )

#################### Methods That combine functionality ####################

    def quick_load(self, load=0, auto_range=True):
        ''' Set the load to a specified value, enabling the output if necessary.
            If the load is set to zero, the output is disabled. sets the range to the right value if needed.

            Args:
                load (float): The desired load current in Amps. Default is 0.
        '''
        if load == 0:
            self.load_setpoint = load
            self.output_enabled = False
            if auto_range:
                self.set_current_range_from_load(load)
        else:
            if auto_range:
                self.load_setpoint = 0
                self.output_enabled = False
                self.set_current_range_from_load(load)
            self.load_setpoint = load
            self.output_enabled = True


    def set_current_range_from_load(self, load: float):
        if load < current_range_values['low']: # if less than low range, use low range
            self.current_range = self.Range.LOW
        elif load < current_range_values['med']: # if less than medium range, use med
            self.current_range = self.Range.MEDIUM
        else: # load > medium range
            self.current_range = self.Range.HIGH