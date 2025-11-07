
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
from pymeasure.instruments import Channel
from pymeasure.instruments.validators import strict_range, strict_discrete_set
from pymeasure.instruments.values import BOOLEAN_TO_INT, BINARY, BOOLEAN_TO_ON_OFF

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# ----------------------- CHANNEL CLASS -----------------------

class ScopeChannel(Channel):
    """
    Represents an individual scope channel.
    """

    def __init__(self, parent, number):
        super().__init__(parent, f"CH_{number}")
        self.number = number
        self._parent = parent

    enable = Channel.control(
        "SELECT:CH{self.number}?", "SELECT:CH{self.number} %d",
        """ A boolean property that enables (True) or disables (False) the channel. """,
        validator=strict_discrete_set,
        values=BINARY,
        map_values=True
    )

    scale = Channel.control(
        "CH{self.number}:SCALE?", "CH{self.number}:SCALE %g",
        """ A float property to set the vertical scale of the channel in volts/div. """,
        validator=strict_range,
        values=[1e-3, 10]
    )

    position = Channel.control(
        "CH{self.number}:POSition?", "CH{self.number}:POSition %g",
        """ A float property to set the vertical position of the channel. """
    )

# ----------------------- MATH CHANNEL CLASS -----------------------

class MathChannel(Channel):
    """
    Represents a math channel.
    """

    def __init__(self, parent, number):
        super().__init__(parent, f"MATH_{number}")
        self.number = number

    function = Channel.control(
        "MATH{self.number}:DEFinition?", "MATH{self.number}:DEFinition %s",
        """ A property to get or set the math function (e.g., ADD, SUB, FFT). """,
        validator=strict_discrete_set,
        values=["ADD", "SUB", "MULT", "DIV", "FFT"]
    )

# ----------------------- MEMORY CHANNEL CLASS -----------------------

class MemoryChannel(Channel):
    """
    Represents a memory channel.
    """

    def __init__(self, parent, number):
        super().__init__(parent, f"MEM_{number}")
        self.number = number

    waveform_data = Channel.measurement(
        "DATA:SOURCE MEM{self.number};:CURVe?",
        """ Reads the waveform data from the memory channel. """
    )



