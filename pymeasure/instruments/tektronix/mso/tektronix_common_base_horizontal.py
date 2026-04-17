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


class Horizontal(sub_system.CommandGroupSubSystem):
    """
    Represents the horizontal (timebase) system of the oscilloscope.
    
    Horizontal commands control the time base of the instrument. You can set the
    time per division (or time per point) of the main time base. You can use the
    Horizontal commands to do the following:
    - Set the scale, horizontal position and reference, and units of the time base
    - Get the screen resolution, time of first point and time of last point, or get all
        the horizontal settings
    - Enable or disable the display of the time base
    """

    # Query all settings
    settings = Instrument.measurement(
        'HORizontal?',
        """Queries the current horizontal settings.
        
        Returns all current horizontal settings including scale, position, and other parameters.
        """
    )

    # Time base properties
    acquisition_duration = Instrument.measurement(
        'HORizontal:ACQDURATION?',
        """Returns the time base duration.
        
        Returns the duration of the acquisition window in seconds.
        """
    )

    delay_mode = Instrument.control(
        'HORizontal:DELay:MODe?', 'HORizontal:DELay:MODe %s',
        """Sets or queries the horizontal delay mode.
        
        Controls whether horizontal delay is enabled.
        Values: {ON|OFF|1|0}
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    delay_time = Instrument.control(
        'HORizontal:DELay:TIMe?', 'HORizontal:DELay:TIMe %g',
        """Sets or queries the horizontal delay time (position) that is used when delay is on.
        
        Sets the horizontal delay in seconds. This is the time from the trigger point
        to the center of the screen.
        """
    )

    divisions = Instrument.measurement(
        'HORizontal:DIVisions?',
        """Returns the number of graticule divisions over which the waveform is displayed.
        
        Typically returns 10 for most oscilloscope displays.
        """
    )

    # FastFrame properties
    fastframe_count = Instrument.control(
        'HORizontal:FASTframe:COUNt?', 'HORizontal:FASTframe:COUNt %d',
        """Sets or queries the number of frames to acquire in FastFrame mode.
        
        Specifies how many frames to capture when FastFrame is enabled.
        Range depends on available memory and record length.
        """,
        validator=strict_range,
        values=(1, 1000000)
    )

    fastframe_max_frames = Instrument.measurement(
        'HORizontal:FASTframe:MAXFrames?',
        """Returns the maximum number of frames for the current configuration.
        
        The maximum depends on record length and available memory.
        """
    )

    fastframe_multiply = Instrument.control(
        'HORizontal:FASTframe:MULtipleframes?', 'HORizontal:FASTframe:MULtipleframes %s',
        """Sets or queries whether multiple FastFrame frames can be selected.
        
        When enabled, allows selection of multiple frames for display and analysis.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    fastframe_ref_frame = Instrument.control(
        'HORizontal:FASTframe:REFframe?', 'HORizontal:FASTframe:REFframe %d',
        """Sets or queries which FastFrame frame is the reference frame.
        
        The reference frame is used for measurements and cursors.
        """
    )

    fastframe_ref_include = Instrument.control(
        'HORizontal:FASTframe:REFInclude?', 'HORizontal:FASTframe:REFInclude %s',
        """Sets or queries whether the reference frame is included in calculations.
        
        Controls whether the reference frame is included when calculating FastFrame summaries.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    fastframe_selected = Instrument.control(
        'HORizontal:FASTframe:SELECTED?', 'HORizontal:FASTframe:SELECTED %d',
        """Sets or queries which FastFrame frame is selected for display.
        
        Selects which captured frame to display on screen.
        """
    )

    fastframe_sequence_state = Instrument.control(
        'HORizontal:FASTframe:SEQuence?', 'HORizontal:FASTframe:SEQuence %s',
        """Sets or queries whether FastFrame sequence mode is enabled.
        
        When enabled, captures multiple frames in sequence.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    fastframe_state = Instrument.control(
        'HORizontal:FASTframe:STATE?', 'HORizontal:FASTframe:STATE %s',
        """Sets or queries whether FastFrame acquisition mode is enabled.
        
        FastFrame allows capturing multiple triggered acquisitions in rapid sequence.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    fastframe_sumframe = Instrument.control(
        'HORizontal:FASTframe:SUMFrame?', 'HORizontal:FASTframe:SUMFrame %s',
        """Sets or queries the FastFrame summary frame mode.
        
        Controls what type of summary frame is created from captured frames.
        Values: {NONe|AVErage|ENVelope}
        """,
        validator=strict_discrete_set,
        values=["NONE", "NON", "AVERAGE", "AVE", "ENVELOPE", "ENV"]
    )

    fastframe_timestamp_all = Instrument.measurement(
        'HORizontal:FASTframe:TIMEStamp:ALL?',
        """Returns the timestamps of all FastFrame frames.
        
        Returns a list of trigger timestamps for all captured frames.
        """
    )

    fastframe_timestamp_between = Instrument.measurement(
        'HORizontal:FASTframe:TIMEStamp:BETWeen?',
        """Returns the time between the reference and selected frames.
        
        Returns the time difference in seconds.
        """
    )

    fastframe_timestamp_ref = Instrument.measurement(
        'HORizontal:FASTframe:TIMEStamp:REFerence?',
        """Returns the timestamp of the FastFrame reference frame.
        
        Returns the trigger timestamp for the reference frame.
        """
    )

    fastframe_timestamp_selected = Instrument.measurement(
        'HORizontal:FASTframe:TIMEStamp:SELECTED?',
        """Returns the timestamp of the selected FastFrame frame.
        
        Returns the trigger timestamp for the currently selected frame.
        """
    )

    fastframe_track = Instrument.control(
        'HORizontal:FASTframe:TRACk?', 'HORizontal:FASTframe:TRACk %s',
        """Sets or queries whether FastFrame tracking is enabled.
        
        When enabled, live and reference frames track together.
        """,
        validator=strict_discrete_set,
        values=["LIVE", "REFERENCE", "ALL"]
    )

    fastframe_xzero_selected = Instrument.measurement(
        'HORizontal:FASTframe:XZEro:SELECTED?',
        """Returns the sub-sample time between the trigger sample and actual trigger.
        
        Returns the sub-sample time between the trigger sample (designated by PT_OFF)
        and the occurrence of the actual trigger for the waveform specified by the
        DATa:SOUrce command for the selected frame.
        """
    )

    # History properties
    history_cstats = Instrument.control(
        'HORizontal:HISTory:CSTAts?', 'HORizontal:HISTory:CSTAts %s',
        """Sets or queries the history cumulative statistics type.
        
        Controls what type of statistics are calculated across history.
        """,
        validator=strict_discrete_set,
        values=["MEAN", "MINIMUM", "MAXIMUM", "STDDEV"]
    )

    history_overlay = Instrument.control(
        'HORizontal:HISTory:OVERlay?', 'HORizontal:HISTory:OVERlay %s',
        """Sets or queries whether all acquisitions in history are overlaid in the waveform view.
        
        When enabled, displays all history acquisitions overlaid on screen.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    history_ref_acq = Instrument.control(
        'HORizontal:HISTory:REF:ACQ?', 'HORizontal:HISTory:REF:ACQ %d',
        """Sets or queries the reference acquisition in History.
        
        Selects which history acquisition is the reference for comparisons.
        """
    )

    history_ref_include = Instrument.control(
        'HORizontal:HISTory:REF:INClude?', 'HORizontal:HISTory:REF:INClude %s',
        """Sets or queries whether the history reference acquisition is included.
        
        Controls whether the history reference acquisition is included in the user
        interface history badge or not.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    history_selected = Instrument.control(
        'HORizontal:HISTory:SELected?', 'HORizontal:HISTory:SELected %d',
        """Sets or queries the selected acquisition in History.
        
        Selects which history acquisition to display.
        """
    )

    history_state = Instrument.control(
        'HORizontal:HISTory:STATe?', 'HORizontal:HISTory:STATe %s',
        """Sets or queries the state of History.
        
        Controls whether history mode is enabled.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    history_timestamp_delta = Instrument.measurement(
        'HORizontal:HISTory:TIMEStamp:DELTa?',
        """Returns the difference between the timestamps of history reference and selected acquisitions.
        
        Returns the time difference in seconds.
        """
    )

    history_timestamp_reference = Instrument.measurement(
        'HORizontal:HISTory:TIMEStamp:REFerence?',
        """Returns the timestamp of the history reference acquisition.
        """
    )

    history_timestamp_selected = Instrument.measurement(
        'HORizontal:HISTory:TIMEStamp:SELected?',
        """Returns the timestamp of the history selected acquisition.
        """
    )

    # Main timebase properties
    main_interp_ratio = Instrument.measurement(
        'HORizontal:MAIn:INTERPRatio?',
        """Returns the interpolation ratio of the main timebase.
        
        Returns the ratio of interpolated points to sampled points.
        """
    )

    position = Instrument.control(
        'HORizontal:POSition?', 'HORizontal:POSition %g',
        """Sets or queries the horizontal position as a percentage of the screen.
        
        Sets the horizontal position of the trigger point on the screen.
        Range: 0 to 100 (left to right across screen).
        """,
        validator=strict_range,
        values=(0, 100)
    )

    pre_record_time = Instrument.measurement(
        'HORizontal:PRERECORDTIMe?',
        """Returns the time from the beginning of the record to the trigger point.
        
        Returns the pre-trigger time in seconds.
        """
    )

    roll_mode = Instrument.control(
        'HORizontal:ROLL?', 'HORizontal:ROLL %s',
        """Sets or queries whether Roll Mode is enabled.
        
        Controls the Roll Mode for slow timebase settings.
        Values: {AUTO|ON|OFF}
        """,
        validator=strict_discrete_set,
        values=["AUTO", "ON", "OFF"]
    )

    sample_rate = Instrument.control(
        'HORizontal:SAMPLERate?', 'HORizontal:SAMPLERate %g',
        """Sets or queries the horizontal sample rate.
        
        Sets the number of samples per second.
        """
    )

    scale = Instrument.control(
        'HORizontal:SCAle?', 'HORizontal:SCAle %g',
        """Sets or queries the horizontal scale (time per division).
        
        Sets the time per division for the horizontal axis.
        Units are seconds per division.
        """
    )

    # Triggering properties
    trigger_position = Instrument.control(
        'HORizontal:TRIGger:POSition?', 'HORizontal:TRIGger:POSition %g',
        """Sets or queries the trigger position on screen.
        
        Sets where the trigger appears on the horizontal axis as a percentage.
        Range: 0 to 100 (left to right).
        """,
        validator=strict_range,
        values=(0, 100)
    )

    units = Instrument.control(
        'HORizontal:UNITs?', 'HORizontal:UNIts %s',
        """Sets or queries the horizontal units.
        
        Sets the units for the horizontal axis.
        Values: {SEConds|HERtz}
        """,
        validator=strict_discrete_set,
        values=["SECONDS", "SEC", "HERTZ", "HER", "HZ"]
    )

    # Zoom properties
    zoom_scale = Instrument.control(
        'HORizontal:ZOOM:SCAle?', 'HORizontal:ZOOM:SCAle %g',
        """Sets or queries the zoom window horizontal scale.
        
        Sets the time per division for the zoom window.
        """
    )

    zoom_position = Instrument.control(
        'HORizontal:ZOOM:POSition?', 'HORizontal:ZOOM:POSition %g',
        """Sets or queries the zoom window horizontal position.
        
        Sets the center position of the zoom window as a percentage.
        """
    )
