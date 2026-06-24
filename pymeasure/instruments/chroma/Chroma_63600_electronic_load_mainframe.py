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

from pymeasure.instruments import Instrument, Channel, SCPIMixin
from pymeasure.instruments.validators import truncated_range, strict_discrete_set
from pymeasure.instruments.values import DICTS

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class Chroma63600Channel(Channel):
    """Represents a single channel (load module) in the Chroma 63600 mainframe.

    Each command is prefixed with a ``CHAN <id>`` selection (see :meth:`insert_id`),
    so the mainframe routes it to this channel's module before executing it.
    """

    voltage = Channel.measurement("MEAS:VOLT?", """Measure the voltage in volts.""")
    current = Channel.measurement("MEAS:CURR?", """Measure the current in amps.""")
    power = Channel.measurement("MEAS:POWE?", """Measure the power in watts.""")
    resistance = Channel.measurement("MEAS:RES?", """Measure the resistance in ohms.""")

    mode = Channel.control(
        "MODE?", "MODE %s",
        """Control the operation mode ('CC', 'CV', 'CW', or 'CR').""",
        validator=strict_discrete_set,
        values=["CC", "CV", "CW", "CR"],
    )

    current_setpoint = Channel.control(
        "CURR?", "CURR %g",
        """Control the current setpoint in amps.""",
        validator=truncated_range,
        values=[0, 100],
    )

    voltage_setpoint = Channel.control(
        "VOLT?", "VOLT %g",
        """Control the voltage setpoint in volts.""",
        validator=truncated_range,
        values=[0, 500],
    )

    power_setpoint = Channel.control(
        "POWE?", "POWE %g",
        """Control the power setpoint in watts.""",
        validator=truncated_range,
        values=[0, 1000],
    )

    load_enabled = Channel.control(
        "LOAD?", "LOAD %d",
        """Control whether the load is enabled (bool).""",
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_INT,
        map_values=True,
    )

    def insert_id(self, command):
        """Prepend the channel selection so the command targets this module."""
        return f"CHAN {self.id};:{command}"


class Chroma63600(SCPIMixin, Instrument):
    """Driver for the Chroma 63600 Series Programmable DC Electronic Load Mainframe.

    The mainframe holds up to five load modules, exposed as channels ``ch_1`` to
    ``ch_5`` (also reachable via the ``channels`` collection):

    .. code-block:: python

        load = Chroma63600("GPIB::10")
        ch = load.ch_2                  # or load.channels[2]

        ch.mode = "CC"                  # constant-current mode
        ch.current_setpoint = 5.0       # 5 A
        ch.load_enabled = True
        print(ch.voltage, ch.current, ch.power)
        ch.load_enabled = False
    """

    channels = Instrument.MultiChannelCreator(Chroma63600Channel, list(range(1, 6)))

    def __init__(self, adapter, name="Chroma 63600 Electronic Load", **kwargs):
        super().__init__(adapter, name, **kwargs)
