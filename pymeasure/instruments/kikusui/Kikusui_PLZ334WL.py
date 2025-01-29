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

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

MFG = "Kikusui"
MODEL = "PLZ334WL"

class PLZ334WL(SCPIMixin, Instrument):
    f""" Represents the {MFG} {MODEL} Power supply
    interface for interacting with the instrument.

    .. code-block:: python
        from pymeasure.instruments import {MFG}
        load = {MFG}.{MODEL}(resource)
        load.current_setpoint=10
        load.output_enabled=True
        print(load.voltage_measure)
    """

    def __init__(self, adapter, name=f"{MFG} {MODEL}", **kwargs):
        super().__init__(
            adapter, name, **kwargs
        )

    load = current_setpoint = Instrument.control(
        "CURR?",
        "CURR %g",
        """Control the load current, accuray depends on range setting.""",
        validator=strict_range,
        values=[0, 240],
        dynamic=True,
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
        "MEAS:CURRent:DC?",
        """Measure the actual power of the load, volt X current"""
    )


    output_enabled = Instrument.control(
        "OUTP:STAT ?",
        "OUTP:STAT %s",
        """Control whether the Output is enabled (boolean).""",
        validator=strict_discrete_set,
        map_values=True,
        values={True: 'ON', False: 'OFF'},
    )
