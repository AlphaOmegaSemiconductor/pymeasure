
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
import time

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

from pymeasure.instruments import Instrument, Channel, SCPIMixin #, SCPIUnknownMixin #TODO determine which of these to use
from pymeasure.instruments.validators import strict_range, strict_discrete_set
from pymeasure.instruments.values import BOOLEAN_TO_INT, BINARY, BOOLEAN_TO_ON_OFF
from .tektronix_common_base_channel import ScopeChannel, MathChannel, MemoryChannel

MFG = "Tektronix"
MODEL = "Base Scope"


path_file_save_dir = pathlib.Path.home() / r"Pictures\scope_capture"
# path_file_save_dir = pathlib.Path(r'C:\scope_captures\\')
class TektronixBaseScope(SCPIMixin, Instrument):
    f""" Represents the {MFG} {MODEL} Oscilloscope 
    and provides a high-level interface for interacting with the instrument.
    
    This base should apply to:
        4 Series MSO (MSO44, MSO46, MSO44B, MSO46B)
        5 Series MSO (MSO54, MSO56, MSO58, MSO54B, MSO56B, MSO58B, MSO58LP)
        6 Series MSO (MSO64, MSO64B, MSO66B, MSO68B)
        6 Series Low Profile Digitizer (LPD64)
    
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
        self._screen_capture = ScreenCapture(self)


    def save_screenshot(self, filename, 
                        save_dir:str | pathlib.Path | None = None, 
                        suffix:str='.png',
                        #, bg_color="white", save_waveform=False, metadata=None):
                        ) -> dict[str, any]:
        """
        Capture a screenshot from the connected oscilloscope and save it
        
        Args:
            save_dir (str or Path): Directory to save the screenshot
            filename (str): Filename for the screenshot (with suffix)
            bg_color (str): Background color ("white" or "black")
            save_waveform (bool): Whether to save waveform data
            metadata (dict): Optional metadata to save
            
        Returns:
            str: Path to the saved file
        """
        if not(suffix.startswith('.')):
            suffix = f".{suffix}"
        
        # Create full path and ensure directory exists
        save_path = save_dir or path_file_save_dir
        save_path = pathlib.Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        file_path = save_path / f"{filename}{suffix}"
        
        try:
            img_data = self.capture_screenshot()
            
            # Wait a moment for the scope to generate the image
            with open(file_path, "wb") as file:
                # file = open(fileName, "wb") # Save image data to local disk
                file.write(img_data)
                file.close()
            
            return {"file_path":file_path, "img_data":img_data}
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            raise


    def capture_screenshot(self, *args, **kwargs): #, save_dir=None, filename=None, suffix='.png', bg_color="white", save_waveform=False, metadata=None):
        ''' Returns an image of the scope screen, does not save it to disk. use save_screenshot() for that'''
        try:
            return self._get_screenshot_hack()
        except Exception as e:
            logger.error(f"_get_screenshot_hack had error {e}, we will retry once, before rasing. but still need to root cause this at some point?")
            time.sleep(1)
            return self._get_screenshot_hack()
                


    def _get_screenshot_hack(self):
        ''' This method works when and AI cant figure it out'''
        #Screen Capture on Tektronix Windows Scope
        self.write('SAVE:IMAGe \"C:/Temp.png\"') # Take a scope shot
        
        # self.ask('*OPC?') # Wait for instrument to finish writing image to disk
        time.sleep(0.1)
        
        self.write('FILESystem:READFile "C:/Temp.png"') # Read temp image file from instrument
        
        img_data = self.adapter.connection.read_raw(1024*1024) # return that read...
        time.sleep(0.05)
        self.adapter.write('FILESystem:DELEte "C:/Temp.png"') # Remove the Temp.png file
        time.sleep(0.05)
        
        return img_data

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

# # ----------------------- CHANNEL CLASS -----------------------

# class ScopeChannel(Channel):
#     """
#     Represents an individual scope channel.
#     """

#     def __init__(self, parent, number):
#         super().__init__(parent, f"CH_{number}")
#         self.number = number
#         self._parent = parent

#     enable = Channel.control(
#         "SELECT:CH{self.number}?", "SELECT:CH{self.number} %d",
#         """ A boolean property that enables (True) or disables (False) the channel. """,
#         validator=strict_discrete_set,
#         values=BINARY,
#         map_values=True
#     )

#     scale = Channel.control(
#         "CH{self.number}:SCALE?", "CH{self.number}:SCALE %g",
#         """ A float property to set the vertical scale of the channel in volts/div. """,
#         validator=strict_range,
#         values=[1e-3, 10]
#     )

#     position = Channel.control(
#         "CH{self.number}:POSition?", "CH{self.number}:POSition %g",
#         """ A float property to set the vertical position of the channel. """
#     )


# # ----------------------- MATH CHANNEL CLASS -----------------------

# class MathChannel(Channel):
#     """
#     Represents a math channel.
#     """

#     def __init__(self, parent, number):
#         super().__init__(parent, f"MATH_{number}")
#         self.number = number

#     function = Channel.control(
#         "MATH{self.number}:DEFinition?", "MATH{self.number}:DEFinition %s",
#         """ A property to get or set the math function (e.g., ADD, SUB, FFT). """,
#         validator=strict_discrete_set,
#         values=["ADD", "SUB", "MULT", "DIV", "FFT"]
#     )

# # ----------------------- MEMORY CHANNEL CLASS -----------------------

# class MemoryChannel(Channel):
#     """
#     Represents a memory channel.
#     """

#     def __init__(self, parent, number):
#         super().__init__(parent, f"MEM_{number}")
#         self.number = number

#     waveform_data = Channel.measurement(
#         "DATA:SOURCE MEM{self.number};:CURVe?",
#         """ Reads the waveform data from the memory channel. """
#     )