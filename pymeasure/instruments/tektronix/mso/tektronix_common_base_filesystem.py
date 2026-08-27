
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

from pymeasure.instruments import HelpMixin, Instrument, sub_system
from pymeasure.instruments.validators import strict_range, strict_discrete_set


class FileSystem(HelpMixin, sub_system.CommandGroupSubSystem):
    """
    Represents the file system of the oscilloscope.
    """
    _help_important = ("cwd", "dir", "read_file")

    @staticmethod # do we want to use this maybe?
    def quoted_string(input_str: str) -> str:
        return f'"{input_str}"'

    delete = Instrument.setting(
        'FILESystem:DELEte "%s"',
        """ A string property to set the path of a file to delete from the
        instrument file system. """,
    )

    read_file = Instrument.setting(
        'FILESystem:READFile "%s"',
        """ A string property to set the path of a file to read from the instrument
        file system.

        This only moves the file into the instrument output buffer; a separate read
        is needed to retrieve the contents.
        """,
    )

    mkdir = Instrument.setting(
        'FILESystem:MKDir "%s"',
        """ A string property to set the path of a directory to create on the
        instrument file system. """,
    )

    cwd = Instrument.control(
        'FILESystem:CWD?', "FILESystem:CWD %s",
        """ A string property to set the current working directory on the
        instrument file system. """,
    )

    dir = Instrument.measurement(
        'FILESystem:DIR?',
        """ A property to get a listing of the current working directory on the
        instrument file system. """,
    )
    
