
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
from pymeasure.instruments import Channel
from pymeasure.instruments.validators import strict_range, strict_discrete_set
from pymeasure.instruments.values import BOOLEAN_TO_INT, BINARY, BOOLEAN_TO_ON_OFF

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class BaseScopeChannel(Channel):
    """The base class for tektronix scope channel definitions. (certain models)

    This class supports dynamic properties like :class:`Instrument`,
    but requires an :class:`Instrument` instance as a parent for communication.

    :meth:`insert_id` inserts the channel id into the command string sent to the instrument.
    The default implementation replaces the Channel's `placeholder` (default "ch")
    with the channel id in all command strings (e.g. "CHANnel{ch}:foo").

    :param parent: The instrument (an instance of :class:`~pymeasure.instruments.Instrument`)
        to which the channel belongs.
    :param id: Identifier of the channel, as it is used for the communication.
    """

    placeholder = "ch"
    channel_type = "CH"

    def __init__(self, parent, id):
        super().__init__(parent=parent, id=id)
            # super init is basically doing this
            # self.parent = parent
            # self.id = id
        self.name = f"{self.channel_type}_{id}"
                
    def insert_id(self, command):
        """Insert the channel id in a command replacing `placeholder`.

        This is the subclasses method, modify this method
            Super(Subclass this method if you want to do something else,
                like always prepending the channel id.)
        """
        return command.format_map({self.placeholder: self.id}) # Expand / modify here as needed


# ----------------------- CHANNEL CLASS -----------------------
class ScopeChannel(BaseScopeChannel):
    """
    Represents an individual scope channel.
    """
    
    enable = Channel.control(
        "SELECT:CH{ch}?", "SELECT:CH{ch} %d",
        """ A boolean property that enables (True) or disables (False) the channel. """,
        validator=strict_discrete_set,
        values=BINARY,
        map_values=True
    )

    scale = Channel.control(
        "CH{ch}:SCALE?", "CH{ch}:SCALE %g",
        """ A float property to set the vertical scale of the channel in volts/div. """,
        validator=strict_range,
        values=[1e-3, 10]
    )

    position = Channel.control(
        "CH{ch}:POSition?", "CH{ch}:POSition %g",
        """ A float property to set the vertical position of the channel. """
    )

# ----------------------- MATH CHANNEL CLASS -----------------------

#TODO if "MATH1" is used to enable disable, we should refactor the placeholder + id thing to sub common command types
    # Need to check how enable command works for math + mem channels

class MathChannel(BaseScopeChannel):
    """
    Represents a math channel.
    """
    channel_type = "MATH"
    
    function = Channel.control(
        "MATH{ch}:DEFinition?", "MATH{ch}:DEFinition %s",
        """ A property to get or set the math function (e.g., ADD, SUB, FFT). """,
        validator=strict_discrete_set,
        values=["ADD", "SUB", "MULT", "DIV", "FFT"]
    )

# ----------------------- MEMORY CHANNEL CLASS -----------------------

class MemoryChannel(BaseScopeChannel):
    """
    Represents a memory channel.
    """
    channel_type = "MEM"

    waveform_data = Channel.measurement(
        "DATA:SOURCE MEM{ch};:CURVe?",
        """ Reads the waveform data from the memory channel. """
    )



# ----------------------- Referance CHANNEL CLASS -----------------------

class MemoryChannel(BaseScopeChannel):
    """
    Represents a memory channel.
    """
    channel_type = "REF"



