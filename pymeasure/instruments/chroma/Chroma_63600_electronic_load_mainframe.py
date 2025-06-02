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
from pymeasure.instruments.validators import truncated_range, strict_discrete_set # , strict_range
from pymeasure.instruments.values import BOOLEAN_TO_INT
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

MFG = "Chroma"
MODEL = "63600"


class Chroma63600Channel(Channel):
    """ Represents a single channel (module) in the Chroma 63600 mainframe. """

    voltage = Channel.measurement("MEAS:VOLT?", "Reads the voltage in volts")
    current = Channel.measurement("MEAS:CURR?", "Reads the current in amps")
    power = Channel.measurement("MEAS:POWE?", "Reads the power in watts")
    resistance = Channel.measurement("MEAS:RES?", "Reads the resistance in ohms")

    mode = Channel.setting(
        "MODE %s",
        """Sets the operation mode: CC, CV, CW, CR""",
        validator=strict_discrete_set,
        values=["CC", "CV", "CW", "CR"]
    )

    current_setpoint = Channel.control(
        "CURR?", "CURR %g",
        """Sets or gets the current setpoint (Amps)""",
        validator=truncated_range,
        values=[0, 100]
    )

    voltage_setpoint = Channel.control(
        "VOLT?", "VOLT %g",
        """Sets or gets the voltage setpoint (Volts)""",
        validator=truncated_range,
        values=[0, 500]
    )

    power_setpoint = Channel.control(
        "POWE?", "POWE %g",
        """Sets or gets the power setpoint (Watts)""",
        validator=truncated_range,
        values=[0, 1000]
    )

    load_enabled = Channel.control(
        "LOAD?", "LOAD %d",
        """Enable (1) or disable (0) the load""",
        validator=strict_discrete_set,
        values=[0, 1],
        map_values=True
    )

class Chroma63600(SCPIMixin, Instrument):
    """ Driver for Chroma 63600 Series Programmable DC Electronic Load Mainframe """

    channels = Instrument.ChannelCreator(Chroma63600Channel, ("CHAN1", "CHAN2", "CHAN3", "CHAN4", "CHAN5"))

    idn = Instrument.measurement("*IDN?", "Returns the device identification string")
    error = Instrument.measurement("SYST:ERR?", "Reads the error queue")

if __name__ == "__main__":
    chroma = Chroma63600("GPIB::10")  # Connect to the mainframe

    # Select and operate on channel 2
    channel2 = chroma.channels.CHAN2
    print(f"Module 2 ID: {chroma.idn}")  # Get device ID

    channel2.mode = "CC"  # Set constant current mode
    channel2.current_setpoint = 5.0  # Set 5A current
    channel2.load_enabled = 1  # Turn on the load

    print(f"Voltage: {channel2.voltage}V, Current: {channel2.current}A, Power: {channel2.power}W")

    channel2.load_enabled = 0  # Turn off the load
