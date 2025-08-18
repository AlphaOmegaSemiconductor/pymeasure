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
# from pymeasure.instruments.validators import strict_range, strict_discrete_set
from .keysight_common_base import VoltageChannel

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


MFG = "Keysight"
MODEL = "E36312A"

class E36312A(SCPIMixin, Instrument):
    f""" Represents the {MFG} {MODEL} Power supply
    interface for interacting with the instrument.

    .. code-block:: python

        supply = {MFG}{MODEL}(resource)
        supply.ch_1.voltage_setpoint=10
        supply.ch_1.current_setpoint=0.1
        supply.ch_1.output_enabled=True
        print(supply.ch_1.voltage)
    """

    ch_1 = Instrument.ChannelCreator(VoltageChannel, 1)

    ch_2 = Instrument.ChannelCreator(VoltageChannel, 2)

    ch_3 = Instrument.ChannelCreator(VoltageChannel, 3)

    def __init__(self, adapter, name=f"{MFG} {MODEL}", **kwargs):
        super().__init__(
            adapter, name, **kwargs
        )
        # self._channel_alies = dict(P6V=self.ch_1,
        #                           P25V=self.ch_2,
        #                           P25V=self.ch_3,)
        self.channels[1].voltage_setpoint_values = [0, 6]
        self.channels[1].current_limit_values = [0, 5]

        self.channels[2].voltage_setpoint_values = [0, 25]
        self.channels[2].current_limit_values = [0, 1]

        self.channels[3].voltage_setpoint_values = [0, 25]
        self.channels[3].current_limit_values = [0, 1]
