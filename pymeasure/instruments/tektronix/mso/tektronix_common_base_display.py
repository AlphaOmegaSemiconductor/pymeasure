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


class Display(sub_system.CommandGroupSubSystem):
    """
    Represents the display control system of the oscilloscope.
    
    Display commands control general instrument settings, such as the intensity of the
    graticule, stacked or overlay display mode, and the fastacq color palette. Display
    commands also control how and where waveforms are shown, their position on screen,
    and zoom settings applied to the view. These commands can:
    - Turn on or off the display of channels
    - Set the selected source
    - Control waveform display modes
    - Adjust display intensity and persistence
    - Manage views and windows
    """

    # General display properties
    annotations = Instrument.control(
        'DISplay:ANNOTATIONs?', 'DISplay:ANNOTATIONs %s',
        """Sets or queries the state of display annotations.
        
        Controls whether annotations are displayed on screen.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    clock = Instrument.control(
        'DISplay:CLOCk?', 'DISplay:CLOCk %s',
        """Sets or queries the display of the date and time.
        
        Controls whether the date/time clock is displayed.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    colors_mathref = Instrument.control(
        'DISplay:COLors:MATHRef?', 'DISplay:COLors:MATHRef %s',
        """Sets or queries the color scheme for math and reference waveforms.
        
        Values: {DEFAULT|INHERIT}
        DEFAULT: Uses default color scheme
        INHERIT: Math/ref waveforms inherit colors from their source channels
        """,
        validator=strict_discrete_set,
        values=["DEFAULT", "INHERIT"]
    )

    colors_palette = Instrument.control(
        'DISplay:COLors:PALETte?', 'DISplay:COLors:PALETte %s',
        """Sets or queries the color palette for the display.
        
        Values: {NORMal|INVerted|MONOchrome|MONOGReen|MONOBlue|MONORed}
        """,
        validator=strict_discrete_set,
        values=["NORMAL", "NORM", "INVERTED", "INV", "MONOCHROME", "MON", 
                "MONOGREEN", "MONOG", "MONOBLUE", "MONOB", "MONORED", "MONOR"]
    )

    format = Instrument.control(
        'DISplay:FORMat?', 'DISplay:FORMat %s',
        """Sets or queries the display format.
        
        Controls how waveforms are arranged on the display.
        Values: {YT|XY|XYZ}
        YT: Voltage versus time (standard oscilloscope display)
        XY: Voltage versus voltage (Lissajous pattern)
        XYZ: Three-dimensional display
        """,
        validator=strict_discrete_set,
        values=["YT", "XY", "XYZ"]
    )

    # Global channel state controls
    ch1_state = Instrument.control(
        'DISplay:GLObal:CH1:STATE?', 'DISplay:GLObal:CH1:STATE %s',
        """Sets or queries the display mode (on or off) of channel 1.
        
        Globally enables or disables display of channel 1 across all views.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    ch2_state = Instrument.control(
        'DISplay:GLObal:CH2:STATE?', 'DISplay:GLObal:CH2:STATE %s',
        """Sets or queries the display mode (on or off) of channel 2.
        
        Globally enables or disables display of channel 2 across all views.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    ch3_state = Instrument.control(
        'DISplay:GLObal:CH3:STATE?', 'DISplay:GLObal:CH3:STATE %s',
        """Sets or queries the display mode (on or off) of channel 3.
        
        Globally enables or disables display of channel 3 across all views.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    ch4_state = Instrument.control(
        'DISplay:GLObal:CH4:STATE?', 'DISplay:GLObal:CH4:STATE %s',
        """Sets or queries the display mode (on or off) of channel 4.
        
        Globally enables or disables display of channel 4 across all views.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    # Intensity settings
    intensity = Instrument.measurement(
        'DISplay:INTENSITy?',
        """Returns the waveform and graticule saturation levels.
        
        Returns the current intensity settings for display elements.
        """
    )

    backlight = Instrument.control(
        'DISplay:INTENSITy:BACKLight?', 'DISplay:INTENSITy:BACKLight %g',
        """Sets or queries the waveform backlight intensity settings.
        
        Controls the display backlight brightness level.
        Range: 0 to 100
        """,
        validator=strict_range,
        values=(0, 100)
    )

    autodim_enable = Instrument.control(
        'DISplay:INTENSITy:BACKLight:AUTODim:ENAble?', 
        'DISplay:INTENSITy:BACKLight:AUTODim:ENAble %s',
        """Sets or queries the state of the display auto-dim feature.
        
        When enabled, the display automatically dims after a period of inactivity.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    autodim_time = Instrument.control(
        'DISplay:INTENSITy:BACKLight:AUTODim:TIMe?', 
        'DISplay:INTENSITy:BACKLight:AUTODim:TIMe %d',
        """Sets or queries the auto-dim timeout in minutes.
        
        Sets the amount of time, in minutes, to wait for no user interface activity
        before automatically dimming the display.
        """,
        validator=strict_range,
        values=(1, 1440)  # 1 minute to 24 hours
    )

    graticule = Instrument.control(
        'DISplay:INTENSITy:GRATicule?', 'DISplay:INTENSITy:GRATicule %g',
        """Sets or queries the graticule intensity.
        
        Controls the brightness of the graticule lines.
        Range: 0 to 100
        """,
        validator=strict_range,
        values=(0, 100)
    )

    # Persistence settings
    persistence = Instrument.control(
        'DISplay:PERSistence?', 'DISplay:PERSistence %s',
        """Sets or queries display persistence setting.
        
        Controls how long waveform points remain visible on screen.
        Values: {OFF|AUTO|INFPersist|VARpersist|CLEAR}
        OFF: No persistence
        AUTO: Automatic persistence
        INFPersist: Infinite persistence
        VARpersist: Variable persistence (use VARpersist command to set time)
        CLEAR: Clear persistence data
        """,
        validator=strict_discrete_set,
        values=["OFF", "AUTO", "INFPERSIST", "INFP", "VARPERSIST", "VARP", "CLEAR"]
    )

    persistence_reset = Instrument.setting(
        'DISplay:PERSistence:RESET',
        """Clears the persistence data.
        
        Removes all accumulated persistence points from the display.
        """
    )

    var_persist = Instrument.control(
        'DISplay:VARpersist?', 'DISplay:VARpersist %g',
        """Sets or queries the persistence decay time.
        
        When persistence is set to VARpersist, this sets the decay time in seconds.
        Range: 0.5 to 10 seconds
        """,
        validator=strict_range,
        values=(0.5, 10)
    )

    # Plot view controls
    plot_view1_state = Instrument.control(
        'DISplay:PLOTView1?', 'DISplay:PLOTView1 %s',
        """Sets or queries the state of plot view 1.
        
        Controls whether plot view 1 is displayed.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    # Reference waveform global states
    ref1_state = Instrument.control(
        'DISplay:GLObal:REF1:STATE?', 'DISplay:GLObal:REF1:STATE %s',
        """Sets or queries the display mode (on or off) of reference 1.
        
        Globally enables or disables display of reference waveform 1.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    ref2_state = Instrument.control(
        'DISplay:GLObal:REF2:STATE?', 'DISplay:GLObal:REF2:STATE %s',
        """Sets or queries the display mode (on or off) of reference 2.
        
        Globally enables or disables display of reference waveform 2.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    ref3_state = Instrument.control(
        'DISplay:GLObal:REF3:STATE?', 'DISplay:GLObal:REF3:STATE %s',
        """Sets or queries the display mode (on or off) of reference 3.
        
        Globally enables or disables display of reference waveform 3.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    ref4_state = Instrument.control(
        'DISplay:GLObal:REF4:STATE?', 'DISplay:GLObal:REF4:STATE %s',
        """Sets or queries the display mode (on or off) of reference 4.
        
        Globally enables or disables display of reference waveform 4.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    # Selected view controls
    select_source = Instrument.control(
        'DISplay:SELect:SOUrce?', 'DISplay:SELect:SOUrce %s',
        """Sets or queries the selected source waveform in the waveform view.
        
        Selects which waveform is active for adjustments and measurements.
        Examples: CH1, CH2, MATH1, REF1, etc.
        """
    )

    select_view = Instrument.control(
        'DISplay:SELect:VIEW?', 'DISplay:SELect:VIEW %s',
        """Sets or queries the selected view.
        
        Selects which view is active for adjustments.
        """
    )

    # Spectrum view display controls  
    spectrogram = Instrument.control(
        'DISplay:SPECView1?', 'DISplay:SPECView1 %s',
        """Sets or queries whether the Spectrum View 1 window is displayed.
        
        Controls display of the spectrum analysis view.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    # Style settings
    style = Instrument.control(
        'DISplay:STYle?', 'DISplay:STYle %s',
        """Sets or queries the waveform display style.
        
        Controls how waveform samples are connected on screen.
        Values: {VECtors|DOTs}
        VECtors: Connect sample points with lines
        DOTs: Display only the sample points
        """,
        validator=strict_discrete_set,
        values=["VECTORS", "VEC", "DOTS", "DOT"]
    )

    # View style (stacked vs overlay)
    viewstyle = Instrument.control(
        'DISplay:VIEWStyle?', 'DISplay:VIEWStyle %s',
        """Sets or queries the waveform layout style used by the display.
        
        Controls whether waveforms are overlaid or stacked.
        Values: {OVERlay|STACked}
        OVERlay: All waveforms share the same graticule
        STACked: Each waveform has its own graticule
        """,
        validator=strict_discrete_set,
        values=["OVERLAY", "OVER", "STACKED", "STAC"]
    )

    # Waveform display enable
    waveform = Instrument.control(
        'DISplay:WAVEform?', 'DISplay:WAVEform %s',
        """Globally enables or disables the waveform display.
        
        Controls whether any waveforms are displayed.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    # Waveform view controls (for channel-specific display in views)
    def ch_state_in_view(self, view: int, channel: int, state: bool = None):
        """
        Sets or queries the state of a channel in a specific waveform view.
        
        Args:
            view: View number (1, 2, etc.)
            channel: Channel number (1-4)
            state: True to enable, False to disable, None to query
        
        Returns:
            Current state if querying
        """
        cmd_base = f'DISplay:WAVEView{view}:CH{channel}:STATE'
        if state is None:
            return self.parent.ask(f'{cmd_base}?')
        else:
            self.parent.write(f'{cmd_base} {"ON" if state else "OFF"}')

    def ch_vertical_position_in_view(self, view: int, channel: int, position: float = None):
        """
        Sets or queries the vertical position of a channel in a specific waveform view.
        
        Args:
            view: View number (1, 2, etc.)
            channel: Channel number (1-4)
            position: Vertical position in divisions, None to query
        
        Returns:
            Current position if querying
        """
        cmd_base = f'DISplay:WAVEView{view}:CH{channel}:VERTical:POSition'
        if position is None:
            return float(self.parent.ask(f'{cmd_base}?'))
        else:
            self.parent.write(f'{cmd_base} {position}')

    def ch_vertical_scale_in_view(self, view: int, channel: int, scale: float = None):
        """
        Sets or queries the vertical scale of a channel in a specific waveform view.
        
        Args:
            view: View number (1, 2, etc.)
            channel: Channel number (1-4)
            scale: Vertical scale in volts per division, None to query
        
        Returns:
            Current scale if querying
        """
        cmd_base = f'DISplay:WAVEView{view}:CH{channel}:VERTical:SCAle'
        if scale is None:
            return float(self.parent.ask(f'{cmd_base}?'))
        else:
            self.parent.write(f'{cmd_base} {scale}')
