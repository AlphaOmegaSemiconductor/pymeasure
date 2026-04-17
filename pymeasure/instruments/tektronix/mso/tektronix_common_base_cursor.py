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


class Cursor(sub_system.CommandGroupSubSystem):
    """
    Represents the cursor measurement system of the oscilloscope.
    
    Use the commands in the Cursor Command Group to control the cursor display
    and readout. You can use these commands to control the setups for each cursor,
    such as waveform source and cursor position. Cursor functions include:
    - Off: Shuts off the display of all cursors
    - Vertical bars: Traditional horizontal unit readouts
    - Horizontal bars: Traditional vertical unit readouts
    - Waveform cursors: Measure specific points on waveforms
    - Screen cursors: Independent positioning on the display
    """

    # Main cursor controls
    function = Instrument.control(
        'CURSor:FUNCtion?', 'CURSor:FUNCtion %s',
        """Sets or queries the cursor function (type).
        
        Controls what type of cursors are displayed.
        Values: {OFF|VBArs|HBArs|SCREEN|WAVEform}
        OFF: No cursors displayed
        VBArs: Vertical bar cursors for time measurements
        HBArs: Horizontal bar cursors for amplitude measurements
        SCREEN: Screen-based cursors
        WAVEform: Waveform tracking cursors
        """,
        validator=strict_discrete_set,
        values=["OFF", "VBARS", "VBAR", "HBARS", "HBAR", "SCREEN", "SCRE", "WAVEFORM", "WAVE"]
    )

    mode = Instrument.control(
        'CURSor:MODe?', 'CURSor:MODe %s',
        """Sets or queries the cursor tracking mode.
        
        Controls whether cursors are independent or track together.
        Values: {INDependent|TRACk}
        INDependent: Cursors can be positioned independently
        TRACk: Cursors track together maintaining constant spacing
        """,
        validator=strict_discrete_set,
        values=["INDEPENDENT", "IND", "TRACK", "TRAC"]
    )

    state = Instrument.control(
        'CURSor:STATE?', 'CURSor:STATE %s',
        """Sets or queries whether cursors are displayed.
        
        Enables or disables cursor display.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    # Horizontal bar cursors (amplitude measurements)
    hbars_position1 = Instrument.control(
        'CURSor:HBArs:POSITION1?', 'CURSor:HBArs:POSITION1 %g',
        """Sets or queries the vertical position of horizontal bar cursor 1.
        
        Sets the position in vertical units (typically volts).
        This cursor measures amplitude.
        """
    )

    hbars_position2 = Instrument.control(
        'CURSor:HBArs:POSITION2?', 'CURSor:HBArs:POSITION2 %g',
        """Sets or queries the vertical position of horizontal bar cursor 2.
        
        Sets the position in vertical units (typically volts).
        This cursor measures amplitude.
        """
    )

    hbars_units = Instrument.measurement(
        'CURSor:HBArs:UNIts?',
        """Returns the units for horizontal bar cursors.
        
        Returns the measurement units (e.g., "V" for volts).
        """
    )

    hbars_delta = Instrument.measurement(
        'CURSor:HBArs:DELTa?',
        """Returns the difference between the two horizontal bar cursors.
        
        Returns the voltage difference between cursor 1 and cursor 2.
        """
    )

    # Vertical bar cursors (time measurements)
    vbars_position1 = Instrument.control(
        'CURSor:VBArs:POSITION1?', 'CURSor:VBArs:POSITION1 %g',
        """Sets or queries the horizontal position of vertical bar cursor 1.
        
        Sets the position in horizontal units (typically seconds).
        This cursor measures time.
        """
    )

    vbars_position2 = Instrument.control(
        'CURSor:VBArs:POSITION2?', 'CURSor:VBArs:POSITION2 %g',
        """Sets or queries the horizontal position of vertical bar cursor 2.
        
        Sets the position in horizontal units (typically seconds).
        This cursor measures time.
        """
    )

    vbars_units = Instrument.measurement(
        'CURSor:VBArs:UNIts?',
        """Returns the units for vertical bar cursors.
        
        Returns the measurement units (e.g., "s" for seconds).
        """
    )

    vbars_delta = Instrument.measurement(
        'CURSor:VBArs:DELTa?',
        """Returns the time difference between the two vertical bar cursors.
        
        Returns the time delta between cursor 1 and cursor 2.
        """
    )

    vbars_alternate = Instrument.control(
        'CURSor:VBArs:ALTERNATE?', 'CURSor:VBArs:ALTERNATE %s',
        """Sets or queries the vertical bar cursor readout selection.
        
        Specifies alternate readout formats for vertical cursors.
        Values may include HEX or other format options.
        """
    )

    # Screen cursors
    screen_axposition = Instrument.control(
        'CURSor:SCREEN:AXPOSition?', 'CURSor:SCREEN:AXPOSition %g',
        """Sets or queries screen cursor A X position.
        
        Sets the horizontal position of screen cursor A.
        Range: 0 to screen width in pixels.
        """
    )

    screen_ayposition = Instrument.control(
        'CURSor:SCREEN:AYPOSition?', 'CURSor:SCREEN:AYPOSition %g',
        """Sets or queries screen cursor A Y position.
        
        Sets the vertical position of screen cursor A.
        Range: 0 to screen height in pixels.
        """
    )

    screen_bxposition = Instrument.control(
        'CURSor:SCREEN:BXPOSition?', 'CURSor:SCREEN:BXPOSition %g',
        """Sets or queries screen cursor B X position.
        
        Sets the horizontal position of screen cursor B.
        Range: 0 to screen width in pixels.
        """
    )

    screen_byposition = Instrument.control(
        'CURSor:SCREEN:BYPOSition?', 'CURSor:SCREEN:BYPOSition %g',
        """Sets or queries screen cursor B Y position.
        
        Sets the vertical position of screen cursor B.
        Range: 0 to screen height in pixels.
        """
    )

    # Waveform cursors
    waveform_asource = Instrument.control(
        'CURSor:WAVEform:ASOUrce?', 'CURSor:WAVEform:ASOUrce %s',
        """Sets or queries the source for waveform cursor A.
        
        Specifies which waveform cursor A tracks.
        Examples: CH1, CH2, MATH1, REF1
        """
    )

    waveform_bsource = Instrument.control(
        'CURSor:WAVEform:BSOUrce?', 'CURSor:WAVEform:BSOUrce %s',
        """Sets or queries the source for waveform cursor B.
        
        Specifies which waveform cursor B tracks.
        Examples: CH1, CH2, MATH1, REF1
        """
    )

    waveform_aposition = Instrument.control(
        'CURSor:WAVEform:APOSition?', 'CURSor:WAVEform:APOSition %g',
        """Sets or queries the position of waveform cursor A.
        
        Sets the position along the waveform in horizontal units.
        """
    )

    waveform_bposition = Instrument.control(
        'CURSor:WAVEform:BPOSition?', 'CURSor:WAVEform:BPOSition %g',
        """Sets or queries the position of waveform cursor B.
        
        Sets the position along the waveform in horizontal units.
        """
    )

    waveform_avposition = Instrument.measurement(
        'CURSor:WAVEform:AVPOSition?',
        """Returns the vertical value at waveform cursor A position.
        
        Returns the amplitude value where cursor A intersects the waveform.
        """
    )

    waveform_bvposition = Instrument.measurement(
        'CURSor:WAVEform:BVPOSition?',
        """Returns the vertical value at waveform cursor B position.
        
        Returns the amplitude value where cursor B intersects the waveform.
        """
    )

    # XY cursors (for XY display mode)
    xy_polar_radius = Instrument.measurement(
        'CURSor:XY:POLar:RADIUS?',
        """Returns the polar radius for XY cursors.
        
        Returns the radius value in polar coordinates for XY display mode.
        """
    )

    xy_polar_theta = Instrument.measurement(
        'CURSor:XY:POLar:THETA?',
        """Returns the polar angle for XY cursors.
        
        Returns the theta value in degrees for XY display mode.
        """
    )

    xy_polar_delta = Instrument.measurement(
        'CURSor:XY:POLar:DELTA?',
        """Returns the polar delta for XY cursors.
        
        Returns the difference in polar coordinates between two cursor positions.
        """
    )

    xy_product = Instrument.measurement(
        'CURSor:XY:PRODuct?',
        """Returns the product of X and Y cursor positions.
        
        Returns X*Y for the cursor position in XY mode.
        """
    )

    xy_ratio = Instrument.measurement(
        'CURSor:XY:RATio?',
        """Returns the ratio of cursor positions.
        
        Returns the ratio Y/X for the cursor position in XY mode.
        """
    )

    xy_readout = Instrument.control(
        'CURSor:XY:READOUT?', 'CURSor:XY:READOUT %s',
        """Sets or queries the XY cursor readout format.
        
        Controls what values are displayed for XY cursors.
        Values: {RECTangular|POLar|PRODuct|RATio}
        RECTangular: X and Y values
        POLar: Radius and angle
        PRODuct: X*Y
        RATio: Y/X
        """,
        validator=strict_discrete_set,
        values=["RECTANGULAR", "RECT", "POLAR", "POL", "PRODUCT", "PROD", "RATIO", "RAT"]
    )

    xy_rectangular_x = Instrument.measurement(
        'CURSor:XY:RECTangular:X:POSition?',
        """Returns the X position for XY rectangular cursors.
        
        Returns the X coordinate value in XY display mode.
        """
    )

    xy_rectangular_y = Instrument.measurement(
        'CURSor:XY:RECTangular:Y:POSition?',
        """Returns the Y position for XY rectangular cursors.
        
        Returns the Y coordinate value in XY display mode.
        """
    )

    # DDT (delta V over delta T) measurements
    ddt = Instrument.measurement(
        'CURSor:DDT?',
        """Returns the delta V over delta T cursor readout value.
        
        Returns the slope (dV/dT) between cursor positions.
        Useful for measuring slew rates.
        """
    )

    # One over delta (frequency from period)
    one_over_delta = Instrument.measurement(
        'CURSor:ONEOVERDELTa?',
        """Returns one over delta cursor readout value.
        
        Returns 1/ΔT which gives frequency when measuring time periods.
        """
    )

    # Cursor utility methods
    def set_cursor_positions(self, cursor1_pos: float, cursor2_pos: float, cursor_type: str = "VBARS"):
        """
        Sets both cursor positions.
        
        Args:
            cursor1_pos: Position for cursor 1
            cursor2_pos: Position for cursor 2
            cursor_type: Type of cursor ("VBARS" or "HBARS")
        """
        if cursor_type.upper() in ["VBARS", "VBAR"]:
            self.vbars_position1 = cursor1_pos
            self.vbars_position2 = cursor2_pos
        elif cursor_type.upper() in ["HBARS", "HBAR"]:
            self.hbars_position1 = cursor1_pos
            self.hbars_position2 = cursor2_pos

    def get_cursor_measurements(self):
        """
        Gets all cursor measurement values.
        
        Returns:
            Dictionary containing cursor positions and delta values
        """
        cursor_func = self.function
        results = {"function": cursor_func}
        
        if cursor_func in ["VBARS", "VBAR"]:
            results["position1"] = self.vbars_position1
            results["position2"] = self.vbars_position2
            results["delta"] = self.vbars_delta
            results["units"] = self.vbars_units
            results["frequency"] = self.one_over_delta
        elif cursor_func in ["HBARS", "HBAR"]:
            results["position1"] = self.hbars_position1
            results["position2"] = self.hbars_position2
            results["delta"] = self.hbars_delta
            results["units"] = self.hbars_units
        elif cursor_func in ["WAVEFORM", "WAVE"]:
            results["a_position"] = self.waveform_aposition
            results["b_position"] = self.waveform_bposition
            results["a_value"] = self.waveform_avposition
            results["b_value"] = self.waveform_bvposition
            results["ddt"] = self.ddt
        
        return results

    def center_cursors(self):
        """
        Centers both cursors on the display.
        """
        self.function = "VBARS"
        # Assuming 10 divisions horizontally, center at 25% and 75%
        center = 0  # Center of time axis
        span = float(self.parent.ask('HORizontal:SCAle?')) * 10  # Total time span
        self.vbars_position1 = center - span * 0.25
        self.vbars_position2 = center + span * 0.25
