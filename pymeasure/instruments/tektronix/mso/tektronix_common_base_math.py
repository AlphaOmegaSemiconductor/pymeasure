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
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

from pymeasure.instruments import Instrument, sub_system
from pymeasure.instruments.validators import strict_range, strict_discrete_set
from pymeasure.instruments.values import BOOLEAN_TO_INT, BINARY, BOOLEAN_TO_ON_OFF


class Math(sub_system.CommandGroupSubSystem):
    """
    Represents the math waveform system of the oscilloscope.
    
    Use the commands in the Math Command Group to create and define math waveforms.
    Use the available math functions to define your math waveform. The math waveform
    you create depends on sources listed in the math expression. Math expressions can
    be simple (e.g., CH1) or complex (100+ characters with many sources and functions).
    """

    # Add/delete math waveforms
    def add_math(self):
        """
        Adds a new math waveform.
        
        Returns:
            Math waveform identifier (e.g., "MATH1")
        """
        return self.parent.ask('MATH:ADDNew')

    def delete_math(self, math_id: str):
        """
        Deletes a specific math waveform.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
        """
        self.parent.write(f'MATH:DELete "{math_id}"')

    def delete_all(self):
        """
        Deletes all math waveforms.
        """
        self.parent.write('MATH:DELete ALL')

    list = Instrument.measurement(
        'MATH:LIST?',
        """Lists all currently defined math waveforms.
        
        Returns a comma-separated list of all math waveform identifiers.
        """
    )

    # Math waveform properties (using dynamic properties for specific math waveform)
    def get_math_define(self, math_id: str):
        """
        Gets the math expression for a specific math waveform.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
        
        Returns:
            Math expression string
        """
        return self.parent.ask(f'MATH:{math_id}:DEFine?')

    def set_math_define(self, math_id: str, expression: str):
        """
        Sets the math expression for a specific math waveform.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
            expression: Math expression (e.g., "CH1+CH2", "CH1*CH2", "FFT(CH1)")
        """
        self.parent.write(f'MATH:{math_id}:DEFine "{expression}"')

    def get_math_type(self, math_id: str):
        """
        Gets the math type for a specific math waveform.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
        
        Returns:
            Math type (e.g., "DUAL", "FFT", "ADVANCED", "SPECTRUM")
        """
        return self.parent.ask(f'MATH:{math_id}:TYPe?')

    def set_math_type(self, math_id: str, math_type: str):
        """
        Sets the math type for a specific math waveform.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
            math_type: Type of math operation
                      Values: {DUAL|FFT|ADVanced|SPECtrum}
        """
        self.parent.write(f'MATH:{math_id}:TYPe {math_type}')

    # Vertical settings
    def get_math_vertical_scale(self, math_id: str):
        """
        Gets the vertical scale for a specific math waveform.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
        
        Returns:
            Vertical scale value
        """
        return float(self.parent.ask(f'MATH:{math_id}:VERTical:SCAle?'))

    def set_math_vertical_scale(self, math_id: str, scale: float):
        """
        Sets the vertical scale for a specific math waveform.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
            scale: Vertical scale value
        """
        self.parent.write(f'MATH:{math_id}:VERTical:SCAle {scale}')

    def get_math_vertical_position(self, math_id: str):
        """
        Gets the vertical position for a specific math waveform.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
        
        Returns:
            Vertical position in divisions
        """
        return float(self.parent.ask(f'MATH:{math_id}:VERTical:POSition?'))

    def set_math_vertical_position(self, math_id: str, position: float):
        """
        Sets the vertical position for a specific math waveform.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
            position: Vertical position in divisions
        """
        self.parent.write(f'MATH:{math_id}:VERTical:POSition {position}')

    def get_math_vertical_units(self, math_id: str):
        """
        Gets the vertical units for a specific math waveform.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
        
        Returns:
            Vertical units string
        """
        return self.parent.ask(f'MATH:{math_id}:VUNit?')

    def set_math_vertical_units(self, math_id: str, units: str):
        """
        Sets custom vertical units for a specific math waveform.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
            units: Custom units string (e.g., "V", "A", "W")
        """
        self.parent.write(f'MATH:{math_id}:VUNit "{units}"')

    # Label settings
    def get_math_label(self, math_id: str):
        """
        Gets the label for a specific math waveform.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
        
        Returns:
            Label string
        """
        return self.parent.ask(f'MATH:{math_id}:LABel:NAMe?')

    def set_math_label(self, math_id: str, label: str):
        """
        Sets the label for a specific math waveform.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
            label: Label text
        """
        self.parent.write(f'MATH:{math_id}:LABel:NAMe "{label}"')

    # FFT settings
    def configure_fft(self, math_id: str, source: str, window: str = "HANNING", 
                     vertical_scale: str = "LINEAR"):
        """
        Configures FFT settings for a math waveform.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
            source: Source channel (e.g., "CH1")
            window: FFT window type
                   Values: {RECTangular|HAMming|HANning|BLAckmanharris}
            vertical_scale: FFT vertical scale
                          Values: {LINear|DBM}
        """
        self.set_math_type(math_id, "FFT")
        self.parent.write(f'MATH:{math_id}:SPECTral:SOUrce {source}')
        self.parent.write(f'MATH:{math_id}:SPECTral:WINdow {window}')
        # Note: Use appropriate command for vertical scale based on your scope model

    def get_fft_horizontal_scale(self, math_id: str):
        """
        Gets the FFT horizontal scale.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
        
        Returns:
            Horizontal scale in Hz/div
        """
        return float(self.parent.ask(f'MATH:{math_id}:HORizontal:SCAle?'))

    def set_fft_horizontal_scale(self, math_id: str, scale: float):
        """
        Sets the FFT horizontal scale.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
            scale: Horizontal scale in Hz/div
        """
        self.parent.write(f'MATH:{math_id}:HORizontal:SCAle {scale}')

    def get_fft_horizontal_position(self, math_id: str):
        """
        Gets the FFT horizontal position (center frequency).
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
        
        Returns:
            Center frequency in Hz
        """
        return float(self.parent.ask(f'MATH:{math_id}:HORizontal:POSition?'))

    def set_fft_horizontal_position(self, math_id: str, position: float):
        """
        Sets the FFT horizontal position (center frequency).
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
            position: Center frequency in Hz
        """
        self.parent.write(f'MATH:{math_id}:HORizontal:POSition {position}')

    # Spectral settings
    def get_spectral_center(self, math_id: str):
        """
        Gets the spectral center frequency.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
        
        Returns:
            Center frequency in Hz
        """
        return float(self.parent.ask(f'MATH:{math_id}:SPECTral:CENTer?'))

    def set_spectral_center(self, math_id: str, frequency: float):
        """
        Sets the spectral center frequency.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
            frequency: Center frequency in Hz
        """
        self.parent.write(f'MATH:{math_id}:SPECTral:CENTer {frequency}')

    def get_spectral_span(self, math_id: str):
        """
        Gets the spectral frequency span.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
        
        Returns:
            Frequency span in Hz
        """
        return float(self.parent.ask(f'MATH:{math_id}:SPECTral:SPAN?'))

    def set_spectral_span(self, math_id: str, span: float):
        """
        Sets the spectral frequency span.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
            span: Frequency span in Hz
        """
        self.parent.write(f'MATH:{math_id}:SPECTral:SPAN {span}')

    def get_spectral_window(self, math_id: str):
        """
        Gets the spectral window function.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
        
        Returns:
            Window type string
        """
        return self.parent.ask(f'MATH:{math_id}:SPECTral:WINdow?')

    def set_spectral_window(self, math_id: str, window: str):
        """
        Sets the spectral window function.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
            window: Window function type
                   Values: {RECTangular|HAMming|HANning|BLAckmanharris|KAIser|GAUSsian}
        """
        self.parent.write(f'MATH:{math_id}:SPECTral:WINdow {window}')

    # Filter settings (for advanced math)
    def configure_filter(self, math_id: str, filter_type: str, cutoff_freq: float):
        """
        Configures filter settings for advanced math.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
            filter_type: Type of filter
                        Values: {LPASs|HPASs|BPASs|BSTop}
                        (Low pass, High pass, Band pass, Band stop)
            cutoff_freq: Cutoff frequency in Hz
        """
        self.parent.write(f'MATH:{math_id}:FILTer:TYPe {filter_type}')
        self.parent.write(f'MATH:{math_id}:FILTer:CFReq {cutoff_freq}')

    def get_filter_type(self, math_id: str):
        """
        Gets the filter type for advanced math.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
        
        Returns:
            Filter type string
        """
        return self.parent.ask(f'MATH:{math_id}:FILTer:TYPe?')

    def get_filter_cutoff(self, math_id: str):
        """
        Gets the filter cutoff frequency.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
        
        Returns:
            Cutoff frequency in Hz
        """
        return float(self.parent.ask(f'MATH:{math_id}:FILTer:CFReq?'))

    # Averaging settings
    def get_average_mode(self, math_id: str):
        """
        Gets the averaging mode for a math waveform.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
        
        Returns:
            Average mode (ON or OFF)
        """
        return self.parent.ask(f'MATH:{math_id}:AVG:MODE?')

    def set_average_mode(self, math_id: str, mode: str):
        """
        Sets the averaging mode for a math waveform.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
            mode: Averaging mode (ON or OFF)
        """
        self.parent.write(f'MATH:{math_id}:AVG:MODE {mode}')

    def get_average_weight(self, math_id: str):
        """
        Gets the number of acquisitions for averaging.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
        
        Returns:
            Number of averages
        """
        return int(self.parent.ask(f'MATH:{math_id}:AVG:WEIGht?'))

    def set_average_weight(self, math_id: str, weight: int):
        """
        Sets the number of acquisitions for averaging.
        
        Args:
            math_id: Math identifier (e.g., "MATH1")
            weight: Number of acquisitions to average (2-10000)
        """
        self.parent.write(f'MATH:{math_id}:AVG:WEIGht {weight}')

    # Convenience methods for common math operations
    def create_add(self, source1: str, source2: str, label: str = None):
        """
        Creates a math waveform that adds two sources.
        
        Args:
            source1: First source (e.g., "CH1")
            source2: Second source (e.g., "CH2")
            label: Optional label for the math waveform
        
        Returns:
            Math waveform identifier
        """
        math_id = self.add_math()
        self.set_math_define(math_id, f"{source1}+{source2}")
        if label:
            self.set_math_label(math_id, label)
        return math_id

    def create_subtract(self, source1: str, source2: str, label: str = None):
        """
        Creates a math waveform that subtracts two sources.
        
        Args:
            source1: First source (e.g., "CH1")
            source2: Second source (e.g., "CH2")
            label: Optional label for the math waveform
        
        Returns:
            Math waveform identifier
        """
        math_id = self.add_math()
        self.set_math_define(math_id, f"{source1}-{source2}")
        if label:
            self.set_math_label(math_id, label)
        return math_id

    def create_multiply(self, source1: str, source2: str, label: str = None):
        """
        Creates a math waveform that multiplies two sources.
        
        Args:
            source1: First source (e.g., "CH1")
            source2: Second source (e.g., "CH2")
            label: Optional label for the math waveform
        
        Returns:
            Math waveform identifier
        """
        math_id = self.add_math()
        self.set_math_define(math_id, f"{source1}*{source2}")
        if label:
            self.set_math_label(math_id, label)
        return math_id

    def create_fft(self, source: str, window: str = "HANNING", label: str = None):
        """
        Creates an FFT math waveform.
        
        Args:
            source: Source channel (e.g., "CH1")
            window: FFT window type (RECTANGULAR, HAMMING, HANNING, BLACKMANHARRIS)
            label: Optional label for the math waveform
        
        Returns:
            Math waveform identifier
        """
        math_id = self.add_math()
        self.configure_fft(math_id, source, window)
        if label:
            self.set_math_label(math_id, label)
        return math_id

    def create_integral(self, source: str, label: str = None):
        """
        Creates an integral math waveform.
        
        Args:
            source: Source channel (e.g., "CH1")
            label: Optional label for the math waveform
        
        Returns:
            Math waveform identifier
        """
        math_id = self.add_math()
        self.set_math_define(math_id, f"INTG({source})")
        if label:
            self.set_math_label(math_id, label)
        return math_id

    def create_derivative(self, source: str, label: str = None):
        """
        Creates a derivative math waveform.
        
        Args:
            source: Source channel (e.g., "CH1")
            label: Optional label for the math waveform
        
        Returns:
            Math waveform identifier
        """
        math_id = self.add_math()
        self.set_math_define(math_id, f"DIFF({source})")
        if label:
            self.set_math_label(math_id, label)
        return math_id
