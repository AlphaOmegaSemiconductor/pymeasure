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
from pymeasure.instruments.values import normalize_str_to_upper # ,BOOLEAN_TO_INT, BINARY, BOOLEAN_TO_ON_OFF

# TODO: This will need to be refactored, the trigger sub system is complicated 
# TODO refactor this into primary and secondary triggers (A and B), (might want a base trigger?)
class Trigger(sub_system.CommandGroupSubSystem):
    """
    Represents the trigger system of the oscilloscope.
    
    Use the commands in the Trigger Command Group to control all aspects of
    triggering for the instrument. There are two triggers: A and B. Where appropriate,
    the command set has parallel constructions for each trigger.
    
    You can set the A or B triggers to edge mode. Edge triggering lets you display
    a waveform at or near the point where the signal passes through a voltage level
    of your choosing.
    
    You can also set A or B triggers to pulse or logic modes. With pulse triggering,
    the instrument triggers whenever it detects a pulse of a certain width or height.
    Logic triggering lets you logically combine the signals on one or more channels.
    The instrument then triggers when it detects a certain combination of signal levels.
    """

    # Force trigger
    force = Instrument.setting(
        'TRIGger:FORCe',
        """Forces a trigger event to occur.
        
        Creates an immediate trigger event, regardless of whether trigger conditions
        are met. This is useful for single-shot acquisitions.
        """
    )

    # Trigger A properties (most commonly used trigger)
    a_edge_coupling = Instrument.control(
        'TRIGger:A:EDGE:COUPling?', 'TRIGger:A:EDGE:COUPling %s',
        """Sets or queries the trigger coupling for edge trigger.
        
        Conditions:
        - DC: DC coupling (passes all signal components)
        - AC: AC coupling (blocks DC component)
        - HFRej: High frequency reject (attenuates signals above 50 kHz)
        - LFRej: Low frequency reject (attenuates signals below 50 kHz)
        - NOISErej: Reduces trigger sensitivity to reduce triggering on noise
        
        Command syntax: TRIGger:A:EDGE:COUPling {DC|AC|HFRej|LFRej|NOISErej}
        """,
        validator=strict_discrete_set,
        values=["DC", "AC", "HFREJ", "HFR", "LFREJ", "LFR", "NOISEREJ", "NOIS"]
    )

    a_edge_slope = Instrument.control(
        'TRIGger:A:EDGE:SLOpe?', 'TRIGger:A:EDGE:SLOpe %s',
        """Sets or queries the trigger slope for edge trigger.
        
        Controls whether the oscilloscope triggers on the rising or falling edge.
        Values: {RISe|FALL|EITHer}
        RISe: Trigger on rising (positive-going) edge
        FALL: Trigger on falling (negative-going) edge
        EITHer: Trigger on either edge
        """,
        validator=strict_discrete_set,
        values=["RISE", "RIS", "FALL", "EITHER", "EITH"]
    )

    a_edge_source = Instrument.control(
        'TRIGger:A:EDGE:SOUrce?', 'TRIGger:A:EDGE:SOUrce %s',
        """Sets or queries the trigger source for edge trigger.
        
        Specifies which signal to use as the trigger source.
        Examples: CH1, CH2, CH3, CH4, LINE, AUX, etc.
        """
    )

    a_holdoff_time = Instrument.control(
        'TRIGger:A:HOLDoff:TIMe?', 'TRIGger:A:HOLDoff:TIMe %g',
        """Sets or queries the trigger holdoff time.
        
        Sets the time period after a trigger during which the trigger system
        will not respond to additional trigger events. Units are seconds.
        """
    )

    a_holdoff_mode = Instrument.control(
        'TRIGger:A:HOLDoff:BY?', 'TRIGger:A:HOLDoff:BY %s',
        """Sets or queries whether trigger holdoff is based on time or events.
        
        Values: {TIMe|EVENts}
        TIMe: Holdoff by time period
        EVENts: Holdoff by number of events
        """,
        validator=strict_discrete_set,
        values=["TIME", "TIM", "EVENTS", "EVEN"]
    )

    a_level = Instrument.control(
        'TRIGger:A:LEVel?', 'TRIGger:A:LEVel %g',
        """Sets or queries the trigger level for the A trigger.
        
        Sets the voltage level through which the signal must pass to generate
        a trigger event. Units are volts.
        """
    )

    a_level_ch1 = Instrument.control(
        'TRIGger:A:LEVel:CH1?', 'TRIGger:A:LEVel:CH1 %g',
        """Sets or queries the trigger level for channel 1.
        
        Sets the voltage level for triggering on channel 1 in volts.
        """
    )

    a_level_ch2 = Instrument.control(
        'TRIGger:A:LEVel:CH2?', 'TRIGger:A:LEVel:CH2 %g',
        """Sets or queries the trigger level for channel 2.
        
        Sets the voltage level for triggering on channel 2 in volts.
        """
    )

    a_level_ch3 = Instrument.control(
        'TRIGger:A:LEVel:CH3?', 'TRIGger:A:LEVel:CH3 %g',
        """Sets or queries the trigger level for channel 3.
        
        Sets the voltage level for triggering on channel 3 in volts.
        """
    )

    a_level_ch4 = Instrument.control(
        'TRIGger:A:LEVel:CH4?', 'TRIGger:A:LEVel:CH4 %g',
        """Sets or queries the trigger level for channel 4.
        
        Sets the voltage level for triggering on channel 4 in volts.
        """
    )

    a_mode = Instrument.control(
        'TRIGger:A:MODe?', 'TRIGger:A:MODe %s',
        """Sets or queries the trigger mode.
        
        Values: {AUTO|NORMal}
        AUTO: Automatically triggers periodically if no trigger event detected
        NORMal: Triggers only when trigger conditions are met
        """,
        validator=strict_discrete_set,
        set_process = normalize_str_to_upper,
        values=["AUTO", "NORMAL", "NORM"]
    )

    a_type = Instrument.control(
        'TRIGger:A:TYPe?', 'TRIGger:A:TYPe %s',
        """Sets or queries the type of A trigger.
        
        Sets what type of event will trigger the oscilloscope.
        Common values: {EDGE|PULSEWidth|RUNT|LOGic|SETHold|TRANsition|BUS}
        EDGE: Edge trigger (most common)
        PULSEWidth: Trigger on pulse width
        RUNT: Trigger on runt pulses
        LOGic: Logic pattern trigger
        SETHold: Setup and hold trigger
        TRANsition: Rise/fall time trigger
        BUS: Serial bus trigger
        """,
        validator=strict_discrete_set,
        set_process = normalize_str_to_upper,
        values=["EDGE", "PULSEWIDTH", "PULSE", "RUNT", "LOGIC", "LOG",
                "SETHOLD", "SETH", "TRANSITION", "TRAN", "BUS"]
    )

    # Pulse width trigger properties
    a_pulsewidth_highlimit = Instrument.control(
        'TRIGger:A:PULSEWidth:HIGHLimit?', 'TRIGger:A:PULSEWidth:HIGHLimit %g',
        """Sets or queries the upper limit for pulse width trigger.
        
        Sets or queries the upper limit to use, in seconds, when triggering on detection
        of a pulse whose duration is inside or outside a range of two values.
        """
    )

    a_pulsewidth_lowlimit = Instrument.control(
        'TRIGger:A:PULSEWidth:LOWLimit?', 'TRIGger:A:PULSEWidth:LOWLimit %g',
        """Sets or queries the lower limit for pulse width trigger.
        
        Sets or queries the lower limit to use, in seconds, when triggering on detection
        of a pulse whose duration is inside or outside a range of two values.
        """
    )

    a_pulsewidth_polarity = Instrument.control(
        'TRIGger:A:PULSEWidth:POLarity?', 'TRIGger:A:PULSEWidth:POLarity %s',
        """Sets or queries the polarity for pulse width trigger.
        
        Values: {POSitive|NEGative}
        POSitive: Trigger on positive pulses
        NEGative: Trigger on negative pulses
        """,
        validator=strict_discrete_set,
        set_process = normalize_str_to_upper,
        values=["POSITIVE", "POS", "NEGATIVE", "NEG"]
    )

    a_pulsewidth_source = Instrument.control(
        'TRIGger:A:PULSEWidth:SOUrce?', 'TRIGger:A:PULSEWidth:SOUrce %s',
        """Sets or queries the source waveform for pulse width trigger.
        
        Specifies which channel to monitor for pulse width triggering.
        """
    )

    a_pulsewidth_when = Instrument.control(
        'TRIGger:A:PULSEWidth:WHEn?', 'TRIGger:A:PULSEWidth:WHEn %s',
        """Sets or queries when to trigger based on pulse width.
        
        Sets or queries to trigger when a pulse is detected with a width (duration)
        that is less than, greater than, equal to, or unequal to a specified value.
        Values: {LESSthan|MOREthan|EQual|UNEQual|WIThin|OUTside}
        """,
        validator=strict_discrete_set,
        set_process = normalize_str_to_upper,
        values=["LESSTHAN", "LESS", "MORETHAN", "MORE", "EQUAL", "EQ",
                "UNEQUAL", "UNEQ", "WITHIN", "WITH", "OUTSIDE", "OUTS"]
    )

    # Trigger B properties (secondary trigger)
    b_edge_coupling = Instrument.control(
        'TRIGger:B:EDGE:COUPling?', 'TRIGger:B:EDGE:COUPling %s',
        """Sets or queries the B trigger coupling for edge trigger.
        
        Same options as A trigger coupling.
        """,
        validator=strict_discrete_set,
        set_process = normalize_str_to_upper,
        values=["DC", "AC", "HFREJ", "HFR", "LFREJ", "LFR", "NOISEREJ", "NOIS"]
    )

    b_edge_slope = Instrument.control(
        'TRIGger:B:EDGE:SLOpe?', 'TRIGger:B:EDGE:SLOpe %s',
        """Sets or queries the B trigger slope for edge trigger.
        
        Same options as A trigger slope.
        """,
        validator=strict_discrete_set,
        set_process = normalize_str_to_upper,
        values=["RISE", "RIS", "FALL", "EITHER", "EITH"]
    )

    b_edge_source = Instrument.control(
        'TRIGger:B:EDGE:SOUrce?', 'TRIGger:B:EDGE:SOUrce %s',
        """Sets or queries the B trigger source for edge trigger.
        
        Specifies which signal to use as the B trigger source.
        """
    )

    b_level = Instrument.control(
        'TRIGger:B:LEVel?', 'TRIGger:B:LEVel %g',
        """Sets or queries the trigger level for the B trigger.
        
        Sets the voltage level through which the signal must pass to generate
        a B trigger event. Units are volts.
        """
    )

    b_type = Instrument.control(
        'TRIGger:B:TYPe?', 'TRIGger:B:TYPe %s',
        """Sets or queries the type of B trigger.
        
        Same options as A trigger type.
        """,
        validator=strict_discrete_set,
        set_process = normalize_str_to_upper,
        values=["EDGE", "PULSEWIDTH", "PULSE", "RUNT", "LOGIC", "LOG",
                "SETHOLD", "SETH", "TRANSITION", "TRAN", "BUS"]
    )

    # Trigger state and frequency
    state = Instrument.measurement(
        'TRIGger:STATE?',
        """Returns the current state of the trigger system.
        
        Returns: {ARMED|AUTO|READY|SAVE|TRIGGER}
        ARMED: Trigger armed and waiting for trigger event
        AUTO: Auto trigger mode active
        READY: Ready to accept trigger
        SAVE: Trigger system saving data
        TRIGGER: Trigger event detected
        """
    )

    frequency = Instrument.measurement(
        'TRIGger:FREQuency?',
        """Returns the trigger frequency.
        
        Returns the rate at which trigger events are occurring, in Hz.
        """
    )

    # Set trigger to 50% automatically
    set_level = Instrument.setting(
        'TRIGger:A SETLevel',
        """Sets the A trigger level automatically to 50% of the signal range.
        
        Automatically adjusts the trigger level to the midpoint of the signal
        amplitude on the selected source.
        """
    )

    b_set_level = Instrument.setting(
        'TRIGger:B SETLevel',
        """Sets the B trigger level automatically to 50% of the signal range.
        
        Automatically adjusts the B trigger level to the midpoint of the signal
        amplitude on the selected source.
        """
    )

    b_reset = Instrument.setting(
        'TRIGger:B:RESET',
        """Resets the B trigger to its default settings.
        
        Returns all B trigger settings to factory defaults.
        """
    )
