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

from pymeasure.instruments import Instrument, SCPIUnknownMixin, Channel
from pymeasure.instruments.instrument import InstrumentException
from pymeasure.instruments.validators import strict_discrete_set, strict_range

MFG = "Tektronix"
MODEL = "MSO58"

class MSO58(SCPIUnknownMixin, Instrument):
    f""" Represents the {MFG} {MODEL} Oscilloscope 
    and provides a high-level interface for interacting with the instrument.
    """


    def __init__(self, adapter, name=f"{MFG} {MODEL} Oscilloscope", **kwargs):
        super().__init__(
            adapter,
            name,
            **kwargs
        )

        self.channels = [ScopeChannel(self, i+1) for i in range(8)]  # 8 analog channels
        self.trigger = Trigger(self)
        self.display = Display(self)
        self.screen_capture = ScreenCapture(self)
        self.math_channels = [MathChannel(self, i+1) for i in range(4)]  # 4 math channels
        self.memory_channels = [MemoryChannel(self, i+1) for i in range(10)]  # Up to 10 memory channels


# ----------------------- CHANNEL CLASS -----------------------

class ScopeChannel(Channel):
    """
    Represents an individual scope channel.
    """

    def __init__(self, parent, number):
        super().__init__(parent, f"CH{number}")
        self.number = number

    enable = Channel.control(
        "SELECT:CH{self.number}?", "SELECT:CH{self.number} %d",
        """ A boolean property that enables (True) or disables (False) the channel. """,
        validator=strict_discrete_set,
        values=[0, 1],
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

# ----------------------- TRIGGER CLASS -----------------------

class Trigger:
    """
    Represents the trigger system of the oscilloscope.
    """

    def __init__(self, parent):
        self.parent = parent

    mode = Instrument.control(
        "TRIGger:MODE?", "TRIGger:MODE %s",
        """ A property to get or set the trigger mode (e.g., EDGE, PULSE, VIDEO). """,
        validator=strict_discrete_set,
        values=["EDGE", "PULSE", "VIDEO", "RUNT", "WIDTH", "TIMEOUT"]
    )

    level = Instrument.control(
        "TRIGger:LEVel?", "TRIGger:LEVel %g",
        """ A property to get or set the trigger level in volts. """
    )

# ----------------------- DISPLAY CLASS -----------------------

class Display:
    """
    Represents the display settings of the oscilloscope.
    """

    def __init__(self, parent):
        self.parent = parent

    grid_style = Instrument.control(
        "DISplay:GRIDstyle?", "DISplay:GRIDstyle %s",
        """ A property to get or set the grid style (FULL, AXES, NONE). """,
        validator=strict_discrete_set,
        values=["FULL", "AXES", "NONE"]
    )

    background_color = Instrument.control(
        "DISplay:PALETte:COLor?", "DISplay:PALETte:COLor %s",
        """ A property to get or set the display background color (WHITE or BLACK). """,
        validator=strict_discrete_set,
        values=["WHITE", "BLACK"]
    )

# ----------------------- SCREEN CAPTURE CLASS -----------------------

class ScreenCapture:
    """
    Represents the screen capture functionality.
    """

    def __init__(self, parent):
        self.parent = parent

    format = Instrument.control(
        "HARDCopy:FORMat?", "HARDCopy:FORMat %s",
        """ A property to get or set the screen capture format (PNG, JPEG, TIFF, BMP). """,
        validator=strict_discrete_set,
        values=["PNG", "JPEG", "TIFF", "BMP"]
    )

    def capture(self, filename="screenshot.png"):
        """ Captures the current screen and saves it to the specified file. """
        self.parent.write("HARDCopy:IMMediate")
        data = self.parent.adapter.read_bytes(1024 * 1024)  # Read binary data
        with open(filename, "wb") as f:
            f.write(data)

# ----------------------- MATH CHANNEL CLASS -----------------------

class MathChannel(Channel):
    """
    Represents a math channel.
    """

    def __init__(self, parent, number):
        super().__init__(parent, f"MATH{number}")
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
        super().__init__(parent, f"MEM{number}")
        self.number = number

    waveform_data = Channel.measurement(
        "DATA:SOURCE MEM{self.number};:CURVe?",
        """ Reads the waveform data from the memory channel. """
    )
