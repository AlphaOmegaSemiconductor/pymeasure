
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


class FileSystem(sub_system.CommandGroupSubSystem):
    """
    Represents the trigger system of the oscilloscope.
    """

    @staticmethod # do we want to use this maybe?
    def quoted_string(input_str: str) -> str:
        return f'"{input_str}"'

    delete = Instrument.setting(
        'FILESystem:DELEte "%s"',
        """ command to delete a file on the filesystem: FILESystem:DELEte <file_path>""",
    )

    read_file = Instrument.setting(
        'FILESystem:READFile "%s"',
        """ command to read a file on the filesystem, this only moves it to the buffer, you must send another command to read the file, based on size or something...: FILESystem:READFile <file_path>""",
    )

    mkdir = Instrument.setting(
        'FILESystem:MKDir "%s"',
        """ command to delete a file on the filesystem: FILESystem:MKDir <dir_path>""",
    )

    cwd = Instrument.control(
        'FILESystem:CWD?', "FILESystem:CWD %s",
        """ command to delete a file on the filesystem: FILESystem:MKDir <dir_path>""",
    )
    
    dir = Instrument.measurement(
        'FILESystem:DIR?',
        """ command to delete a file on the filesystem: FILESystem:MKDir <dir_path>""",
    )
    
