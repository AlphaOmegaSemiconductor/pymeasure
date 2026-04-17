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


class Acquisition(sub_system.CommandGroupSubSystem):
    """
    Represents the acquisition system of the oscilloscope.
    
    Acquisition commands set up the modes and functions that control how the
    instrument acquires signals and processes them into waveforms. Using these
    commands for acquiring waveforms, you can do the following:
    - Start and stop acquisitions
    - Control whether each waveform is simply acquired, averaged, or enveloped
        over successive acquisitions of that waveform
    - Set the controls or conditions that start and stop acquisitions
    - Control acquisition of acquired channel waveforms
    - Set acquisition parameters
    """

    state = Instrument.measurement(
        'ACQuire?',
        """Queries the current acquisition state.
        
        Returns the current acquisition state.
        """
    )

    fastacq_palette = Instrument.control(
        'ACQuire:FASTAcq:PALEtte?', 'ACQuire:FASTAcq:PALEtte %s',
        """Sets or queries the waveform grading for fast acquisition mode.
        
        The available palettes control the color scheme used for FastAcq waveform display.
        """,
        validator=strict_discrete_set,
        values=["NORMAL", "ANALOG", "TEMPERATURE", "SPECTRAL", "INVERTED"]
    )

    fastacq_state = Instrument.control(
        'ACQuire:FASTAcq:STATE?', 'ACQuire:FASTAcq:STATE %d',
        """Sets or queries whether fast acquisition mode is active.
        
        When enabled, FastAcq provides fast waveform capture and display update rates.
        """,
        validator=strict_discrete_set,
        values=BINARY,
        map_values=True
    )

    interpolate_ratio = Instrument.measurement(
        'ACQuire:INTERPEight?',
        """Queries the interpolation ratio for real-time sampling.
        
        Returns the ratio of interpolated points to sampled points for real-time acquisitions.
        """
    )

    magnivu = Instrument.control(
        'ACQuire:MAGnivu?', 'ACQuire:MAGnivu %s',
        """Sets or queries the MagniVu state.
        
        MagniVu provides a high-speed sampling view of the signal centered around the trigger point.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    max_sample_rate = Instrument.measurement(
        'ACQuire:MAXSamplerate?',
        """Queries the maximum real-time sample rate.
        
        Returns the maximum sample rate for the current acquisition settings.
        """
    )

    min_magnivu_pretrig = Instrument.control(
        'ACQuire:MINMAGnivuPRETrig?', 'ACQuire:MINMAGnivuPRETrig %g',
        """Sets or queries the minimum MagniVu pretrigger time.
        
        Sets the minimum pretrigger time for MagniVu acquisitions in seconds.
        """
    )

    mode = Instrument.control(
        'ACQuire:MODe?', 'ACQuire:MODe %s',
        """Sets or queries the acquisition mode.
        
        Conditions:
        - Sample: Default mode that acquires and displays samples
        - PeakDetect: Captures glitches and reduces aliasing
        - HIRes: Provides higher vertical resolution
        - Average: Reduces noise by averaging multiple acquisitions
        - Envelope: Captures min/max values over multiple acquisitions
        
        Command syntax: ACQuire:MODe {SAMple|PEAKdetect|HIRes|AVErage|ENVelope}
        """,
        validator=strict_discrete_set,
        values=["SAMPLE", "SAM", "PEAKDETECT", "PEAK", "HIRES", "HIR", 
                "AVERAGE", "AVE", "ENVELOPE", "ENV"]
    )

    num_acquisitions = Instrument.measurement(
        'ACQuire:NUMACq?',
        """Queries the number of acquisitions that have occurred.
        
        Returns the number of times the acquisition system has triggered since 
        starting acquisition with the RUN/STOP or SINGLE SEQUENCE button.
        """
    )

    num_average = Instrument.control(
        'ACQuire:NUMAVg?', 'ACQuire:NUMAVg %d',
        """Sets or queries the number of acquisitions to average.
        
        When the acquisition mode is set to Average, this sets the number of 
        waveform acquisitions to average. Values range from 2 to 10240.
        """,
        validator=strict_range,
        values=(2, 10240)
    )

    num_envelope = Instrument.control(
        'ACQuire:NUMENVelope?', 'ACQuire:NUMENVelope %s',
        """Sets or queries the number of acquisitions to be enveloped.
        
        When the acquisition mode is set to Envelope, this sets the number of
        waveform acquisitions to acquire before displaying the envelope.
        Set to 'INFINITE' for continuous envelope acquisition.
        """,
        validator=strict_discrete_set,
        values=["INFINITE", "INF"] + list(range(1, 10001))
    )

    num_frames_acquired = Instrument.measurement(
        'ACQuire:NUMFRAMESACQuired?',
        """Returns the number of FastFrame frames which have been acquired.
        
        This query is only valid when FastFrame is enabled.
        """
    )

    num_saved = Instrument.control(
        'ACQuire:NUMSAVed?', 'ACQuire:NUMSAVed %d',
        """Sets or queries the minimum number of frames saved.
        
        For Roll Mode, sets the minimum number of frames to be saved during acquisition.
        """,
        validator=strict_range,
        values=(1, 2147483647)
    )

    record_length = Instrument.control(
        'ACQuire:RECOrdlength?', 'ACQuire:RECOrdlength %d',
        """Sets or queries the record length for acquisition.
        
        Specifies the number of data points in each waveform record.
        Available values depend on the oscilloscope model and memory depth.
        """
    )

    roll = Instrument.control(
        'ACQuire:ROLL?', 'ACQuire:ROLL %s',
        """Sets or queries the Roll Mode state.
        
        Roll Mode continuously scrolls waveforms across the display for slow timebase settings.
        Values: {AUTO|ON|OFF}
        """,
        validator=strict_discrete_set,
        values=["AUTO", "ON", "OFF"]
    )

    sample_rate = Instrument.measurement(
        'ACQuire:SAMPLERate?',
        """Queries the sample rate for the current acquisition.
        
        Returns the number of samples per second.
        """
    )

    sequence_count = Instrument.control(
        'ACQuire:SEQuence:COUnt?', 'ACQuire:SEQuence:COUnt %d',
        """Sets or queries the number of acquisitions for sequence mode.
        
        Specifies how many acquisitions to perform when in sequence mode.
        """,
        validator=strict_range,
        values=(1, 2147483647)
    )

    sequence_current = Instrument.measurement(
        'ACQuire:SEQuence:CURrent?',
        """Queries the current acquisition number in sequence mode.
        
        Returns which acquisition is currently being performed in the sequence.
        """
    )

    sequence_mode = Instrument.control(
        'ACQuire:SEQuence:MODe?', 'ACQuire:SEQuence:MODe %s',
        """Sets or queries whether sequence mode is on or off.
        
        When on, the oscilloscope performs a specified number of acquisitions.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    sequence_waveforms = Instrument.control(
        'ACQuire:SEQuence:NUMSEQuence?', 'ACQuire:SEQuence:NUMSEQuence %d',
        """Sets or queries the number of waveforms in sequence mode.
        
        Specifies how many waveforms to capture in sequence mode.
        """
    )

    # Start/Stop commands
    run = Instrument.setting(
        'ACQuire:STATE RUN',
        """Starts acquisitions.
        
        Starts the acquisition system and enables the TRIGGER system.
        """
    )

    stop = Instrument.setting(
        'ACQuire:STATE STOP',
        """Stops acquisitions.
        
        Stops the acquisition system and disables the TRIGGER system.
        """
    )

    state = Instrument.control(
        'ACQuire:STATE?', 'ACQuire:STATE %s',
        """Sets or queries the acquisition state.
        
        Controls whether the oscilloscope is acquiring data.
        Values: {RUN|STOP|ON|OFF|1|0}
        """,
        validator=strict_discrete_set,
        values=("RUN", "STOP", "ON", "OFF", "1", "0", 1, 0)
    )

    stop_after = Instrument.control(
        'ACQuire:STOPAfter?', 'ACQuire:STOPAfter %s',
        """Sets or queries when acquisitions stop.
        
        Conditions:
        - RUNSTOP: Acquisitions run until explicitly stopped
        - SEQUENCE: Acquisition stops after the specified number of acquisitions
        
        Command syntax: ACQuire:STOPAfter {RUNSTop|SEQuence}
        """,
        validator=strict_discrete_set,
        values=["RUNSTOP", "RUNS", "SEQUENCE", "SEQ"]
    )

    sync_samples = Instrument.control(
        'ACQuire:SYNCSAMples?', 'ACQuire:SYNCSAMples %s',
        """Sets or queries whether channels are sampled simultaneously.
        
        When ON, analog channels are sampled at the same instant.
        When OFF, channels may be sampled at slightly different times.
        """,
        validator=strict_discrete_set,
        values=BOOLEAN_TO_ON_OFF,
        map_values=True
    )
