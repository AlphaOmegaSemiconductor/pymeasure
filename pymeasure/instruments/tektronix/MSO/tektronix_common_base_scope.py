
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
from typing import Callable

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

from pymeasure.instruments import Instrument, Channel, SCPIMixin #, SCPIUnknownMixin #TODO determine which of these to use
from pymeasure.instruments.validators import strict_range, strict_discrete_set
from pymeasure.instruments.values import BOOLEAN_TO_INT, BINARY, BOOLEAN_TO_ON_OFF
from .tektronix_common_base_channel import ScopeChannel, MathChannel, MemoryChannel

MFG = "Tektronix"
MODEL = "Base Scope"

def hook(msg, payload):
    print(msg, " : ", payload)


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
    
    PIXELS_PER_VERTICAL_DIVISION = 94 # pretty sure this is right
    
    def __init__(self, adapter, name=f"{MFG} {MODEL} Oscilloscope", **kwargs):
        super().__init__(
            adapter,
            name,
            **kwargs
        )

        self.channels = tuple(ScopeChannel(self, i+1) for i in range(self.analog_channels))  # analog channels
        for channel in self.channels:
            setattr(self, channel.name.lower(), channel)

        self.math_channels = tuple(MathChannel(self, i+1) for i in range(self.math_channels))  # math channels
        for math_channel in self.math_channels:
            setattr(self, math_channel.name.lower(), math_channel)

        self.memory_channels = tuple(MemoryChannel(self, i+1) for i in range(self.memory_channels))  # memory channels
        for memory_channel in self.memory_channels:
            setattr(self, memory_channel.name.lower(), memory_channel)

        self.trigger = Trigger(self)
        self.display = Display(self)
        # self._screen_capture = ScreenCapture(self) # Does not work at all

        self.setup_screenshot_dir()


    def setup_screenshot_dir(self, 
                            dir_path: str = "C:/temp", 
                            hook_log=None
                            ) -> None:
        """Create temp directory and clear any existing files."""
        # Create directory on scope (will not error if it already exists)
        try:
            self.write(f'FILESystem:MKDir "{dir_path}"')
            if hook_log: hook_log('info', f"Scope temp directory ready: {dir_path}")
        except Exception as e:
            if hook_log: hook_log('error', f"Note: {e} (directory may already exist)")
        # Clear all files in the temp directory
        self.clear_temp_directory(dir_path)


    def clear_temp_directory(self, 
                            scope_temp_dir: str="C:/temp", 
                            hook_log=None
                            ) -> None:
        """
        Delete all files in the scope's temp directory.
        
        Args:
            scope: PyVISA instrument object
            scope_temp_dir: Path to temp directory on scope filesystem
        """
        try:
            # Get directory listing
            self.write(f'FILESystem:CWD "{scope_temp_dir}"')
            dir_contents = self.ask('FILESystem:DIR?').strip()
            
            if dir_contents and dir_contents != '""':
                # Parse the directory listing (format may vary by scope model)
                # Typically returns comma-separated list of files
                files = [f.strip('"') for f in dir_contents.split(',') if f.strip()]
                
                for filename in files:
                    if filename and filename not in ['.', '..']:
                        file_path = f"{scope_temp_dir}/{filename}"
                        self.write(f'FILESystem:DELEte "{file_path}"')
                        if hook_log: hook_log('info', f"Deleted from scope: {file_path}")
            else:
                if hook_log: hook_log('info', f"Scope temp directory is empty: {scope_temp_dir}")
                
        except Exception as e:
            if hook_log: hook_log('error', f"Error clearing scope temp directory: {e}")


    def save_screenshot(self, filename, 
                        save_dir:str | pathlib.Path | None = None, 
                        suffix:str='.png',
                        #, bg_color="white", save_waveform=False, metadata=None):
                        hook_log=None,
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


    def capture_screenshot(self, hook_log: Callable|None = hook, 
                           *args, **kwargs): #, save_dir=None, filename=None, suffix='.png', bg_color="white", save_waveform=False, metadata=None):
        ''' Returns an image of the scope screen, does not save it to disk. use save_screenshot() for that'''
        try:
            return self._get_screenshot_hack()
        except Exception as e:
            msg=f"_get_screenshot_hack had error {e}, we will retry once, before rasing. but still need to root cause this at some point?"
            logger.error(msg)
            if hook_log: hook_log("error", msg)
            time.sleep(1)
            return self._get_screenshot_hack()
                


    def _get_screenshot_hack(self):
        ''' This is based on tektronix's own provided example code, wild
        https://www.tek.com/en/support/faqs/how-save-and-transfer-screenshot-4-5-or-6-series-mso

        now use a unique filename to prevent accidental read errors, setup will mk temp dir and clean up on connect
        
        '''
        #Screen Capture on Tektronix Windows Scope
        filename = f"C:/temp/{time.time_ns()}.png" 
        write_str =f'SAVE:IMAGe "{filename}"' # Take a scope shot
        self.write(write_str) # Take a scope shot
        
        self.ask('*OPC?') # Wait for instrument to finish writing image to disk
        # self.adapter.connection.query('*OPC?') # Wait for instrument to finish writing image to disk
        # time.sleep(0.1)
        
        write_str = f'FILESystem:READFile "{filename}"'
        self.write(write_str) # Read temp image file from instrument
        
        img_data = self.adapter.connection.read_raw(1024*1024) # return that read...
        # time.sleep(0.05)
        write_str = f'FILESystem:DELEte "{filename}"'
        self.adapter.write(write_str) # Remove the Temp.png file
        # time.sleep(0.05)
        
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

# ----------------------- File System CLASS -----------------------

class FileSystem:
    """
    Represents the trigger system of the oscilloscope.
    """
    

    def __init__(self, parent):
        self.parent = parent

    @staticmethod # do we want to use this maybe?
    def quoted_string(input_str: str) -> str:
        return f'"{input_str}"'

    delete = Instrument.setting(
        'FILESystem:DELEte "%s"',
        """ command to delete a file on the filesystem: FILESystem:DELEte <file_path>""",
    )

    read_file = Instrument.setting(
        'FILESystem:READFile "%s"',
        """ command to read a file on the filesystem, this only moves it to the buffer, you must send another command to read the file, based on size or something...: FILESystem:READFile <file_path>""",
    )

    mkdir = Instrument.setting(
        'FILESystem:MKDir "%s"',
        """ command to delete a file on the filesystem: FILESystem:MKDir <dir_path>""",
    )

    cwd = Instrument.control(
        'FILESystem:CWD?', "FILESystem:CWD %s",
        """ command to delete a file on the filesystem: FILESystem:MKDir <dir_path>""",
    )
    
    dir = Instrument.measurement(
        'FILESystem:DIR?',
        """ command to delete a file on the filesystem: FILESystem:MKDir <dir_path>""",
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
        self.parent.write("HARDCopy STARt")
        img_data = self.read_raw()
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