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
from pymeasure.instruments.values import BOOLEAN_TO_INT, RANGE
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

MFG = "Kikusui"
MODEL = "PLZ1205W"

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
    Range = RANGE

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

    current_range = Instrument.control(
        "CURR:RANG?", "CURR:RANG %s",
        """ Controls the DC current range.""",
        validator=strict_discrete_set,
        values=["LOW", "MED", "HIGH"]
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


#TODO fix this?
    # def load_adv(self, load=0, soak_time=0.5, auto_range=True):
    #     ret = dict(load=load, soak_time=soak_time)
    #     if auto_range:
    #         self.output_enabled = False
    #         self.set_current_range_from_load(load)

    #     ret['current_range_setting'] = self.current_range

    #     if self.output_enabled:
    #         self.load_setpoint = load
    #         if load == 0:
    #             self.output_enabled = False
    #     else:
    #         self.set_current_range_from_load(load)
    #         self.load_setpoint = load
    #         if not load == 0:
    #             self.output_enabled = True




    def quick_load(self, load=0):
        if self.output_enabled:
            self.load_setpoint = load
            if load == 0:
                self.output_enabled = False
        else:
            self.set_current_range_from_load(load)
            self.load_setpoint = load
            if not load == 0:
                self.output_enabled = True

    def set_current_range_from_load(self, load: int):
        if load<1: #Set the load range to 1A if the load is less than 1A
            self.current_range = self.Range.LOW
        elif load>10: #Set the load range to 100A if the load is greater than 10A
            # ELoad1.write("CURR:RANG HIGH")
            self.current_range = self.Range.HIGH
        else:    #load is between 1 and 10A
            # ELoad1.write("CURR:RANG MED")
            self.current_range = self.Range.MEDIUM