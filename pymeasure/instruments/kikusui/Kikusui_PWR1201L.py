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


class PWR1201L(SCPIMixin, Instrument):
    """ Represents the Keysight E36312A Power supply
    interface for interacting with the instrument.

    .. code-block:: python

        supply = PWR1201L(resource)
        supply.voltage_setpoint=10
        supply.current_setpoint=0.1
        supply.output_enabled=True
        print(supply.voltage)
    """

    def __init__(self, adapter, name="Kikusui PWR1201L", **kwargs):
        super().__init__(
            adapter, name, **kwargs
        )


    voltage_setpoint = Instrument.control(
        "VOLT?",
        "VOLT %g",
        """Control the output voltage of this channel, range depends on channel.""",
        validator=strict_range,
        values=[0, 40],
        dynamic=True,
    )

    current_limit = Instrument.control(
        "CURR?",
        "CURR %g",
        """Control the current limit of this channel, range depends on channel.""",
        validator=strict_range,
        values=[0, 140],
        dynamic=True,
    )

    voltage = Instrument.measurement(
        "MEASure:VOLTage?",
        """Measure actual voltage of this channel."""
    )

    current = Instrument.measurement(
        "MEAS:CURRent?",
        """Measure the actual current of this channel."""
    )

    output_enabled = Instrument.control(
        "OUTPut?",
        "OUTPut %d",
        """Control whether the channel output is enabled (boolean).""",
        validator=strict_discrete_set,
        map_values=True,
        values={True: 1, False: 0},
    )