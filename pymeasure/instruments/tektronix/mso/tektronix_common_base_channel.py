
#
# This file is part of the PyMeasure package.
#
# Copyright (c) 2013-2024 PyMeasure Developers
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
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

from pymeasure.instruments import Channel
from pymeasure.instruments.validators import strict_range, strict_discrete_set
from pymeasure.instruments.process import set_processor_dict_map
from pymeasure.instruments.values import DICTS, TUPLES


class BaseScopeChannel(Channel):
    '''The base class for tektronix scope channel definitions. (certain models)

    This class supports dynamic properties like :class:`Instrument`,
    but requires an :class:`Instrument` instance as a parent for communication.

    :meth:`insert_id` inserts the channel id into the command string sent to the instrument.
    The default implementation replaces the Channel's `placeholder` (default 'ch')
    with the channel id in all command strings (e.g. 'CHANnel{ch}:foo').

    :param parent: The instrument (an instance of :class:`~pymeasure.instruments.Instrument`)
        to which the channel belongs.
    :param id: Identifier of the channel, as it is used for the communication.
    '''

    placeholder_id = 'ch'
    channel_type = 'CH'
    placeholder_channel_type = "ch_type"

    def __init__(self, parent, id):
        super().__init__(parent=parent, id=id)
            # super init is basically doing this
            # self.parent = parent
            # self.id = id
        self.name = f'{self.channel_type}_{id}'
                
    def insert_id(self, command):
        '''Insert the channel id in a command replacing `placeholder`.

        This is the subclasses method, modify this method
            Super(Subclass this method if you want to do something else,
                like always prepending the channel id.)
        '''
        return command.format_map({self.placeholder_id: self.id, self.placeholder_channel_type : self.channel_type}) # Expand / modify here as needed


    label_name = Channel.control(
        '{ch_type}{ch}:LABel:NAMe?', '{ch_type}{ch}:LABel:NAMe "%s"',
        ''' A float property to set the vertical scale of the channel in volts/div. ''',
        # validator=strict_range, #TODO validate and truncate strings to match "<QString> is an alphanumeric character string, ranging from 1 through 32 characters in length.""
    )

    label_x = Channel.control(
        '{ch_type}{ch}:LABel:XPOS?', '{ch_type}{ch}:LABel:XPOS %g',
        ''' A float property to set the vertical scale of the channel in volts/div. ''',
        validator=strict_range,
        values=[0, 1720]
    )

    label_y = Channel.control(
        '{ch_type}{ch}:LABel:YPOS?', '{ch_type}{ch}:LABel:YPOS %g',
        ''' A float property to set the vertical scale of the channel in volts/div. ''',
        validator=strict_range,
        values=[-1200, 1200]
    )

# ----------------------- CHANNEL CLASS -----------------------
class ScopeChannel(BaseScopeChannel):
    '''
    Represents an individual scope channel.
    '''
    channel_type = 'CH'
    TERMINATION_SETTINGS = {50:50, 'min':50, 10e6:10e6, 'max':10e6}
    
    enable = Channel.control(
        'SELECT:{ch_type}{ch}?', 'SELECT:{ch_type}{ch} %d',
        ''' A boolean property that enables (True) or disables (False) the channel. ''',
        validator=strict_discrete_set,
        values=TUPLES.BINARY,
        map_values=True
    )

    clipping = Channel.measurement(
        '{ch_type}{ch}:CLIPping?',
        ''' Queries whether the specified channel's input signal is clipping (exceeding) the channel A/D converter range. ''',
        values=DICTS.BOOLEAN_TO_INT,
        map_values=True
    )

    coupling = Channel.control(
        '{ch_type}{ch}:COUPling?', '{ch_type}{ch}:COUPling %s',
        ''' A boolean property that enables (True) or disables (False) the channel. ''',
        validator=strict_discrete_set,
        values=["AC", "DC" "DCR"],
        # map_values=True
    )

    invert = Channel.control(
        '{ch_type}{ch}:INVert?', '{ch_type}{ch}:INVert %s',
        ''' A boolean property that enables (True) or disables (False) the channel. ''',
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_ON_OFF,
        map_values=True
    )

    termination = Channel.control(
        'CH{ch}:TERmination?', 'CH{ch}:TERmination %g',
        ''' This command sets or queries the input termination for the specified analog
        channel. values returned are in Ohms. Options are 50 Ohms and 1 MOhm (1,000,000 ohms)
        mapped to "min" and "max" ''',
        preprocess_input=set_processor_dict_map(TERMINATION_SETTINGS),
        validator=strict_discrete_set,
        values=TERMINATION_SETTINGS,
        map_values=True
    )    
    
    scale = Channel.control(
        'CH{ch}:SCALE?', 'CH{ch}:SCALE %g',
        ''' A float property to set the vertical scale of the channel in volts/div. ''',
        validator=strict_range,
        values=[1e-3, 100]
    )

    bandwidth = Channel.control(
        'CH{ch}:BANdwidth?', 'CH{ch}:BANdwidth %g',
        ''' A float property to set the vertical scale of the channel in volts/div. ''',
        validator=strict_range, # should we accept 10-1000 and treat that as being in MHz?
        values=[10e6, 1000e6], # TODO "FUL also works, refactor with composite validator? "
    )

    offset = Channel.control(
        'CH{ch}:OFFSet?', 'CH{ch}:OFFSet %g',
        ''' A float property to set the vertical position of the channel. '''
    )

    position = Channel.control(
        'CH{ch}:POSition?', 'CH{ch}:POSition %g',
        ''' A float property to set the vertical position of the channel. '''
    )

    probe = Channel.measurement(
        'CH{ch}:PRObe?',
        ''' This query-only command returns all information concerning the probe 
        that is attached to the specified channel. 
        ''',
        cast=str, # DO we want to enable parsing? 
    )

    probe_units = Channel.measurement(
        'CH{ch}:PRObe:UNIts?',
        ''' This query-only command returns a string describing the units of measure 
        for the probe attached to the specified channel. 
        ''',
        cast=str, # DO we want to enable parsing? 
    )

    alternate_units = Channel.control(
        'CH{ch}:PROBEFunc:EXTUnits?', 'CH{ch}:PROBEFunc:EXTUnits %s',
        ''' This command sets the unit of measurement for the external attenuator of the
        specified channel. The channel is specified by x. The alternate units are used if
        they are enabled. Use the CH<x>:PROBEFunc:EXTUnits:STATE command to
        enable or disable the alternate units. ''',
        # validator= is a string? pre defined list of units?,
        cast=str,
    )   

    alternate_units_enable = Channel.control(
        'CH{ch}:PROBEFunc:EXTUnits:STATE?', 'CH{ch}:PROBEFunc:EXTUnits:STATE %s',
        ''' This command sets the unit of measurement for the external attenuator of the
        specified channel. The channel is specified by x. The alternate units are used if
        they are enabled. Use the CH<x>:PROBEFunc:EXTUnits:STATE command to
        enable or disable the alternate units. ''',
        validator=strict_discrete_set,
        values=DICTS.BOOLEAN_TO_ON_OFF,
        map_values=True,
    )   

# ----------------------- MATH CHANNEL CLASS -----------------------

#TODO if 'MATH1' is used to enable disable, we should refactor the placeholder + id thing to sub common command types
    # Need to check how enable command works for math + mem channels

class MathChannel(BaseScopeChannel):
    '''
    Represents a math channel.
    '''
    channel_type = 'MATH'
    
    function = Channel.control(
        'MATH{ch}:DEFinition?', 'MATH{ch}:DEFinition %s',
        ''' A property to get or set the math function (e.g., ADD, SUB, FFT). ''',
        validator=strict_discrete_set,
        values=['ADD', 'SUB', 'MULT', 'DIV', 'FFT']
    )

# ----------------------- MEMORY CHANNEL CLASS -----------------------

class MemoryChannel(BaseScopeChannel):
    '''
    Represents a memory channel.
    '''
    channel_type = 'MEM'

    waveform_data = Channel.measurement(
        'DATA:SOURCE MEM{ch};:CURVe?',
        ''' Reads the waveform data from the memory channel. '''
    )



# ----------------------- Reference CHANNEL CLASS -----------------------
# What is this again? check the instrument data sheet, might be something we forgot to implement here
class ReferenceChannel(BaseScopeChannel):
    '''
    Represents a memory channel.
    '''
    channel_type = 'REF'



