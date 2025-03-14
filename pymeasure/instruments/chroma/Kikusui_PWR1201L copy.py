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
from pymeasure.instruments.values import BOOLEAN_TO_INT
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

MFG = "Kikusui"
MODEL = "PWR1201L"

class PWR1201L(SCPIMixin, Instrument):
    f""" Represents the {MFG} {MODEL} Power supply
    interface for interacting with the instrument.

    .. code-block:: python
        from pymeasure.instruments import {MFG}
        supply = {MFG}.{MODEL}(resource)
        supply.voltage_setpoint=10
        supply.current_setpoint=0.1
        supply.output_enabled=True
        print(supply.voltage)
    """

    RATED_OUTPUT_VOLTAGE = 40 # volts 
    RATED_OUTPUT_CURRENT = 120 # amps 

    def __init__(self, adapter, name=f"{MFG} {MODEL}", **kwargs):
        super().__init__(
            adapter, name, **kwargs
        )
        self.reset()

    ###############
    # Voltage (V) #
    ###############

    voltage_setpoint = Instrument.control(
        "VOLT?",
        "VOLT %g",
        """Control the output voltage of this channel, range depends on channel.""",
        validator=strict_range,
        values=[0, 40],
        dynamic=True,
    )

    voltage_measure = Instrument.measurement(
        "MEASure:VOLTage?",
        """Measure actual voltage of this channel."""
    )

    voltage_limit_auto = Instrument.control(
        "VOLT:LIM:AUTO?",
        "VOLT:LIM:AUTO %d",
        """Enables or disables the voltage limit setting""",
        validator=strict_discrete_set,
        map_values=True,
        values=BOOLEAN_TO_INT,
    )

    voltage_uvp = Instrument.control(
        "VOLT:LIM:LOW?",
        "VOLT:LIM:LOW %g",
        """Sets the UnderVoltage protection limit trip point""",
        validator=strict_range,
        values=[0, 1.05*RATED_OUTPUT_VOLTAGE], # 0 to 105% of rated output
    )

    voltage_ovp = Instrument.control(
        "VOLT:PROT:LEV?",
        "VOLT:PROT:LEV %g",
        """Sets the OverVoltage protection limit trip point""",
        validator=strict_range,
        values=[0.10*RATED_OUTPUT_VOLTAGE, 1.12*RATED_OUTPUT_VOLTAGE], # 10 to 112% of rated output
    )

    voltage_ocp_hysteresis = Instrument.control(
        "VOLT:PROT:DEL?",
        "VOLT:PROT:DEL %g",
        """detection time of OCP, 0 seconds by default. """,
        validator=strict_range,
        values=[0, 2.0], # 10 to 112% of rated output
    )
    

    ###############
    # Current (A) #
    ###############

    current_limit = Instrument.control(
        "CURR?",
        "CURR %g",
        """Control the current limit of this channel, range depends on channel.""",
        validator=strict_range,
        values=[0, 1.05*RATED_OUTPUT_CURRENT],
        dynamic=True,
    )

    current_measure = Instrument.measurement(
        "MEAS:CURRent?",
        """Measure the actual current of this channel."""
    )

    current_limit_auto = Instrument.control(
        "CURR:LIM:AUTO?",
        "CURR:LIM:AUTO %d",
        """Enables or disables the current limit setting""",
        validator=strict_discrete_set,
        map_values=True,
        values=BOOLEAN_TO_INT,
    )

    current_ocp = Instrument.control(
        "CURR:PROT:LEV?",
        "CURR:PROT:LEV %g",
        """Enables or disables the urrent limit setting""",
        validator=strict_range,
        values=[0.10*RATED_OUTPUT_CURRENT, 1.12*RATED_OUTPUT_CURRENT], # 10 to 112% of rated output
    )

    current_ocp_hysteresis = Instrument.control(
        "CURR:PROT:DEL?",
        "CURR:PROT:DEL %g",
        """detection time of OCP, 0 seconds by default. """,
        validator=strict_range,
        values=[0, 2.0], # 10 to 112% of rated output
    )
    
    ###############
    # Control     #
    ###############

    output_enabled = Instrument.control(
        "OUTPut?",
        "OUTPut %d",
        """Control whether the channel output is enabled (boolean).""",
        validator=strict_discrete_set,
        map_values=True,
        values={True: 1, False: 0},
    )