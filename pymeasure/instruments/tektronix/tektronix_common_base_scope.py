
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
import pathlib
from pymeasure.instruments import Instrument, Channel, SCPIMixin, SCPIUnknownMixin #TODO determine which of these to use
from pymeasure.instruments.validators import strict_range, strict_discrete_set
from pymeasure.instruments.values import BOOLEAN_TO_INT, BINARY, BOOLEAN_TO_ON_OFF
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

MFG = "Tektronix"
MODEL = "Base Scope"

path_file_save_location = pathlib.Path(r'C:\scope_captures\\')
class TektronixBaseScope(SCPIUnknownMixin, Instrument):
    f""" Represents the {MFG} {MODEL} Oscilloscope 
    and provides a high-level interface for interacting with the instrument.
    """
    analog_channels = 8
    math_channels = 4
    memory_channels = 8
    def __init__(self, adapter, name=f"{MFG} {MODEL} Oscilloscope", **kwargs):
        super().__init__(
            adapter,
            name,
            **kwargs
        )

        self.channels = (ScopeChannel(self, i+1) for i in range(self.analog_channels))  # analog channels
        for channel in self.channels:
            setattr(self, channel.id.lower(), channel)

        self.math_channels = (MathChannel(self, i+1) for i in range(self.math_channels))  # math channels
        for math_channel in self.math_channels:
            setattr(self, math_channel.id.lower(), math_channel)

        self.memory_channels = (MemoryChannel(self, i+1) for i in range(self.memory_channels))  # memory channels
        for memory_channel in self.memory_channels:
            setattr(self, memory_channel.id.lower(), memory_channel)

        self.trigger = Trigger(self)
        self.display = Display(self)
        self.screen_capture = ScreenCapture(self)



    # def capture(self):
    #     dt = datetime.now()
    #     fileName = dt.strftime("%Y%m%d_%H%M%S.png")
    #     image = self.screen_capture.capture_2
    #     image_file = open(file_save_default_location + fileName, "wb")
    #     image_file.write(image)
    #     image_file.close()
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

FILE_FORMATS = ["PNG", "JPEG", "TIFF", "BMP"]
class ScreenCapture:
    """
    Represents the screen capture functionality.
    """
    def __init__(self, parent):
        self.parent = parent


    capture_format = Instrument.control(
        "HARDCopy:FORMat?", "HARDCopy:FORMat %s",
        """ A property to get or set the screen capture format (PNG, JPEG, TIFF, BMP). """,
        validator=strict_discrete_set,
        values=FILE_FORMATS
    )

    image_save_format = Instrument.control(
        "SAVe:IMAGe:FILEFormat ?", "SAVe:IMAGe:FILEFormat %s",
        """ A property to get or set the screen capture format (PNG, JPEG, TIFF, BMP). """,
        validator=strict_discrete_set,
        values=FILE_FORMATS
    )

    image_ink_saver = Instrument.control(
        "SAVe:IMAGe:INKSaver ?", "SAVe:IMAGe:INKSaver %s",
        """ A boolean property that enables (True) or disables (False) ink saver when capturing the screen.""",
        validator=strict_discrete_set,
        map_values=True,
        values=BOOLEAN_TO_ON_OFF,
    )

    def capture_2(self, filename="screenshot.png"): #TODO figure out which of these works
        """ Captures the current screen and saves it to the specified file. """
        self.write("HARDCopy STARt")
        img_data = scope.read_raw()
        return img_data

    def capture(self, filename="screenshot.png"): #TODO make a top level capture method that implements all the controls
        """ Captures the current screen and saves it to the specified file. """
        self.parent.write("HARDCopy:IMMediate")
        img_data = self.parent.adapter.read_bytes(1024 * 1024)  # Read binary data
        return img_data
        # with open(filename, "wb") as f:
        #     f.write(data)

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



