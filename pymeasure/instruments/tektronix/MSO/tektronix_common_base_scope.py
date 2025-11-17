
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

from pymeasure.instruments import Instrument, SCPIMixin #, SCPIUnknownMixin #TODO determine which of these to use
# from pymeasure.instruments.validators import strict_range, strict_discrete_set
# from pymeasure.instruments.values import BOOLEAN_TO_INT, BINARY, BOOLEAN_TO_ON_OFF

from .tektronix_common_base_acquisition import Acquisition
from .tektronix_common_base_channel import ScopeChannel, MathChannel, MemoryChannel
from .tektronix_common_base_cursor import Cursor
from .tektronix_common_base_display import Display
from .tektronix_common_base_filesystem import FileSystem
from .tektronix_common_base_horizontal import Horizontal
from .tektronix_common_base_math import Math
from .tektronix_common_base_measurement import Measurement
from .tektronix_common_base_trigger import Trigger
from .tektronix_common_base_waveform_transfer import WaveformTransfer


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

        ## Setup Channels

        self.channels = tuple(ScopeChannel(self, i+1) for i in range(self.analog_channels))  # analog channels
        for channel in self.channels:
            setattr(self, channel.name.lower(), channel)

        self.math_channels = tuple(MathChannel(self, i+1) for i in range(self.math_channels))  # math channels
        for math_channel in self.math_channels:
            setattr(self, math_channel.name.lower(), math_channel)

        self.memory_channels = tuple(MemoryChannel(self, i+1) for i in range(self.memory_channels))  # memory channels
        for memory_channel in self.memory_channels:
            setattr(self, memory_channel.name.lower(), memory_channel)

        ## Setup command groups

        self.acquisition = Acquisition(self)
        self.cursor = Cursor(self)
        self.display = Display(self)
        self.file_system = FileSystem(self)
        self.horizontal = Horizontal(self)
        self.math = Math(self)
        self.measure = Measurement(self)
        self.trigger = Trigger(self)
        self.waveforms = WaveformTransfer(self)

        self.setup_screenshot_dir()


    def setup_screenshot_dir(self, 
                            dir_path: str = "C:/temp", 
                            hook_log: Callable|None = hook, 
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
                            hook_log: Callable|None = hook, 
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
                        hook_log: Callable|None = hook,
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

