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
import numpy as np
from typing import Union, Tuple, Dict, Any

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

from pymeasure.instruments import Instrument, sub_system
from pymeasure.instruments.validators import strict_range, strict_discrete_set
from pymeasure.instruments.values import BOOLEAN_TO_INT, BINARY, BOOLEAN_TO_ON_OFF


class WaveformTransfer(sub_system.CommandGroupSubSystem):
    """
    Represents the waveform transfer system of the oscilloscope.
    
    Use the commands in the Waveform Transfer Command Group to transfer waveform
    data points from the instrument. Waveform data points are a collection of values
    that define a waveform. Before transferring waveform data, you must specify the
    data format, record length, and waveform source.
    
    Data formats supported:
    - ASCII: Human-readable but slow
    - RIBinary: Signed integer, MSB first
    - SRIBinary: Signed integer, LSB first
    - RFBinary: Floating point, MSB first
    - SRFBinary: Floating point, LSB first
    """

    # Data format settings
    data_encoding = Instrument.control(
        'DATa:ENCdg?', 'DATa:ENCdg %s',
        """Sets or queries the format for waveform data transfer.
        
        Conditions:
        - ASCii: ASCII format (slow but human-readable)
        - RIBinary: Signed integer data, most significant byte first
        - SRIBinary: Signed integer data, least significant byte first (PC-friendly)
        - RFBinary: Floating point data, most significant byte first
        - SRFBinary: Floating point data, least significant byte first (PC-friendly)
        
        Command syntax: DATa:ENCdg {ASCii|RIBinary|SRIBinary|RFBinary|SRFBinary}
        """,
        validator=strict_discrete_set,
        values=["ASCII", "ASC", "RIBINARY", "RIB", "SRIBINARY", "SRI", 
                "RFBINARY", "RFB", "SRFBINARY", "SRF"]
    )

    data_source = Instrument.control(
        'DATa:SOUrce?', 'DATa:SOUrce %s',
        """Sets or queries the source for waveform data transfer.
        
        Specifies which waveform to transfer.
        Examples: CH1, CH2, MATH1, REF1, etc.
        Multiple sources can be specified separated by commas.
        """
    )

    data_start = Instrument.control(
        'DATa:STARt?', 'DATa:STARt %d',
        """Sets or queries the starting data point for waveform transfer.
        
        Specifies the first data point to transfer.
        Range: 1 to record length
        """,
        validator=strict_range,
        values=(1, 2147483647)
    )

    data_stop = Instrument.control(
        'DATa:STOP?', 'DATa:STOP %d',
        """Sets or queries the ending data point for waveform transfer.
        
        Specifies the last data point to transfer.
        Range: 1 to record length
        """,
        validator=strict_range,
        values=(1, 2147483647)
    )

    data_width = Instrument.control(
        'WFMOutpre:BYT_Nr?', 'WFMOutpre:BYT_Nr %d',
        """Sets or queries the data width for waveform transfer.
        
        Specifies the number of bytes per data point.
        Values: {1|2|4|8}
        1: 8-bit signed integer
        2: 16-bit signed integer
        4: 32-bit signed integer or floating point
        8: 64-bit floating point
        """,
        validator=strict_discrete_set,
        values=[1, 2, 4, 8]
    )

    # Waveform preamble information
    def get_waveform_preamble(self) -> Dict[str, Any]:
        """
        Gets the waveform formatting data.
        
        Returns:
            Dictionary containing waveform preamble information including:
            - byte_num: Number of bytes per data point
            - bit_num: Number of bits per data point
            - encoding: Data encoding format
            - bin_format: Binary format
            - byte_order: Byte order (MSB or LSB first)
            - num_points: Number of points in waveform
            - point_format: Format of each point (Y or ENV)
            - x_incr: Horizontal increment between points
            - x_zero: Time of first point
            - x_offset: Horizontal offset
            - y_mult: Vertical scale factor
            - y_zero: Vertical offset factor
            - y_offset: Vertical position
            - x_unit: Horizontal units
            - y_unit: Vertical units
        """
        preamble_str = self.parent.ask('WFMOutpre?')
        # Parse the preamble string - format is semicolon delimited
        values = preamble_str.split(';')
        
        preamble = {}
        preamble['byte_num'] = int(self.parent.ask('WFMOutpre:BYT_Nr?'))
        preamble['bit_num'] = int(self.parent.ask('WFMOutpre:BIT_Nr?'))
        preamble['encoding'] = self.parent.ask('WFMOutpre:ENCdg?')
        preamble['bin_format'] = self.parent.ask('WFMOutpre:BN_Fmt?')
        preamble['byte_order'] = self.parent.ask('WFMOutpre:BYT_Or?')
        preamble['num_points'] = int(self.parent.ask('WFMOutpre:NR_Pt?'))
        preamble['point_format'] = self.parent.ask('WFMOutpre:PT_Fmt?')
        preamble['x_incr'] = float(self.parent.ask('WFMOutpre:XINcr?'))
        preamble['x_zero'] = float(self.parent.ask('WFMOutpre:XZEro?'))
        preamble['pt_offset'] = int(self.parent.ask('WFMOutpre:PT_Off?'))
        preamble['y_mult'] = float(self.parent.ask('WFMOutpre:YMUlt?'))
        preamble['y_zero'] = float(self.parent.ask('WFMOutpre:YZEro?'))
        preamble['y_offset'] = float(self.parent.ask('WFMOutpre:YOFf?'))
        preamble['x_unit'] = self.parent.ask('WFMOutpre:XUNit?')
        preamble['y_unit'] = self.parent.ask('WFMOutpre:YUNit?')
        
        return preamble

    # Individual preamble queries
    wfm_byte_num = Instrument.measurement(
        'WFMOutpre:BYT_Nr?',
        """Returns the number of bytes per waveform point.
        
        Indicates how many bytes represent each data point in the waveform.
        """
    )

    wfm_bit_num = Instrument.measurement(
        'WFMOutpre:BIT_Nr?',
        """Returns the number of bits per waveform point.
        
        Returns the number of bits per waveform point that outgoing waveforms contain.
        """
    )

    wfm_encoding = Instrument.measurement(
        'WFMOutpre:ENCdg?',
        """Returns the type of encoding for outgoing waveforms.
        
        Returns: ASCii, BINary, etc.
        """
    )

    wfm_binary_format = Instrument.measurement(
        'WFMOutpre:BN_Fmt?',
        """Returns the format of binary data for the waveform.
        
        Returns: RI (signed integer) or RP (positive integer) or FP (floating point)
        """
    )

    wfm_byte_order = Instrument.measurement(
        'WFMOutpre:BYT_Or?',
        """Returns the byte order of waveform points.
        
        Returns: MSB (most significant byte first) or LSB (least significant byte first)
        """
    )

    wfm_num_points = Instrument.measurement(
        'WFMOutpre:NR_Pt?',
        """Returns the number of points in the waveform.
        
        Returns the number of points for the waveform transmitted in response to a
        CURVe? query.
        """
    )

    wfm_point_format = Instrument.measurement(
        'WFMOutpre:PT_Fmt?',
        """Returns the point format for the waveform.
        
        Returns: Y (normal waveform) or ENV (envelope waveform with min/max pairs)
        """
    )

    wfm_x_increment = Instrument.measurement(
        'WFMOutpre:XINcr?',
        """Returns the horizontal sampling interval.
        
        Returns the horizontal interval between data points in seconds.
        """
    )

    wfm_x_zero = Instrument.measurement(
        'WFMOutpre:XZEro?',
        """Returns the time of the first waveform point.
        
        Returns the time coordinate of the first point in the waveform, relative to
        the trigger.
        """
    )

    wfm_point_offset = Instrument.measurement(
        'WFMOutpre:PT_Off?',
        """Returns the trigger point within the waveform record.
        
        Returns the data point number that corresponds to the trigger point.
        """
    )

    wfm_y_multiplier = Instrument.measurement(
        'WFMOutpre:YMUlt?',
        """Returns the vertical scale factor.
        
        Returns the vertical scale factor per digitizing level of the waveform.
        """
    )

    wfm_y_zero = Instrument.measurement(
        'WFMOutpre:YZEro?',
        """Returns the vertical offset factor.
        
        Returns the vertical offset of the waveform in vertical units.
        """
    )

    wfm_y_offset = Instrument.measurement(
        'WFMOutpre:YOFf?',
        """Returns the vertical position.
        
        Returns the vertical position of the waveform in digitizing levels.
        """
    )

    wfm_x_unit = Instrument.measurement(
        'WFMOutpre:XUNit?',
        """Returns the horizontal units.
        
        Returns the horizontal units of the waveform (typically "s" for seconds).
        """
    )

    wfm_y_unit = Instrument.measurement(
        'WFMOutpre:YUNit?',
        """Returns the vertical units.
        
        Returns the vertical units of the waveform (e.g., "V" for volts).
        """
    )

    # Waveform data transfer
    def get_curve_data(self) -> Union[np.ndarray, bytes]:
        """
        Transfers waveform data from the instrument.
        
        Returns:
            Waveform data as numpy array (if numeric) or bytes (if raw binary)
        """
        encoding = self.data_encoding
        
        if encoding.upper().startswith('ASC'):
            # ASCII data
            data_str = self.parent.ask('CURVe?')
            values = [float(x) for x in data_str.split(',')]
            return np.array(values)
        else:
            # Binary data
            self.parent.write('CURVe?')
            # Read binary block - format is #NXXXXXXXXDATA where N is number of digits
            # in XXXXXXXX which specifies the number of bytes
            header = self.parent.read(2)  # Read #N
            if not header.startswith('#'):
                raise ValueError(f"Invalid binary block header: {header}")
            
            num_digits = int(header[1])
            num_bytes = int(self.parent.read(num_digits))
            data_bytes = self.parent.read_bytes(num_bytes)
            
            # Convert based on format
            byte_width = self.wfm_byte_num
            byte_order = self.wfm_byte_order
            
            if byte_order.upper() == 'MSB':
                endian = '>'  # Big endian
            else:
                endian = '<'  # Little endian
            
            if byte_width == 1:
                dtype = f'{endian}i1'
            elif byte_width == 2:
                dtype = f'{endian}i2'
            elif byte_width == 4:
                if 'FP' in self.wfm_binary_format:
                    dtype = f'{endian}f4'
                else:
                    dtype = f'{endian}i4'
            elif byte_width == 8:
                dtype = f'{endian}f8'
            else:
                raise ValueError(f"Unsupported byte width: {byte_width}")
            
            data = np.frombuffer(data_bytes, dtype=dtype)
            return data

    def get_scaled_waveform(self, source: str = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Gets scaled waveform data with time axis.
        
        Args:
            source: Waveform source (e.g., "CH1"). If None, uses current data source.
        
        Returns:
            Tuple of (time_array, voltage_array)
        """
        if source:
            self.data_source = source
        
        # Get preamble for scaling information
        preamble = self.get_waveform_preamble()
        
        # Get raw curve data
        raw_data = self.get_curve_data()
        
        # Scale the data
        y_mult = preamble['y_mult']
        y_zero = preamble['y_zero']
        y_offset = preamble['y_offset']
        
        voltage = (raw_data - y_offset) * y_mult + y_zero
        
        # Create time axis
        x_incr = preamble['x_incr']
        x_zero = preamble['x_zero']
        pt_offset = preamble['pt_offset']
        
        num_points = len(voltage)
        time = np.arange(num_points) * x_incr + x_zero
        
        return time, voltage

    def setup_fast_transfer(self):
        """
        Configures settings for fastest waveform transfer.
        
        Sets binary format with appropriate byte order for the host system.
        """
        import sys
        
        # Use signed integer binary format
        if sys.byteorder == 'little':
            self.data_encoding = 'SRIBINARY'  # LSB first for PCs
        else:
            self.data_encoding = 'RIBINARY'   # MSB first
        
        # Use 2-byte data for good balance of speed and resolution
        self.data_width = 2

    def setup_ascii_transfer(self):
        """
        Configures settings for ASCII waveform transfer.
        
        Slower but human-readable and platform-independent.
        """
        self.data_encoding = 'ASCII'

    def save_waveform_csv(self, filename: str, source: str = None):
        """
        Saves waveform data to a CSV file.
        
        Args:
            filename: Path to save the CSV file
            source: Waveform source (e.g., "CH1")
        """
        import csv
        
        time, voltage = self.get_scaled_waveform(source)
        
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Time (s)', f'Voltage ({self.wfm_y_unit})'])
            for t, v in zip(time, voltage):
                writer.writerow([t, v])
        
        logger.info(f"Waveform saved to {filename}")

    def get_multiple_waveforms(self, sources: list) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
        """
        Gets scaled waveform data for multiple sources.
        
        Args:
            sources: List of waveform sources (e.g., ["CH1", "CH2", "MATH1"])
        
        Returns:
            Dictionary with source as key and (time, voltage) tuple as value
        """
        waveforms = {}
        for source in sources:
            time, voltage = self.get_scaled_waveform(source)
            waveforms[source] = (time, voltage)
        return waveforms

    # Utility methods for common operations
    def get_waveform_statistics(self, source: str = None) -> Dict[str, float]:
        """
        Calculates basic statistics for a waveform.
        
        Args:
            source: Waveform source (e.g., "CH1")
        
        Returns:
            Dictionary with min, max, mean, std, peak-to-peak values
        """
        time, voltage = self.get_scaled_waveform(source)
        
        stats = {
            'min': float(np.min(voltage)),
            'max': float(np.max(voltage)),
            'mean': float(np.mean(voltage)),
            'std': float(np.std(voltage)),
            'peak_to_peak': float(np.max(voltage) - np.min(voltage)),
            'rms': float(np.sqrt(np.mean(voltage**2)))
        }
        return stats
