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

from enum import Enum, StrEnum

#TODO make these singletons and frozen?
class RANGE_ENUM_LMH(StrEnum):
    '''
    Enum class for range settings with low, medium, high options
    '''
    LOW = 'LOW'
    MEDIUM = 'MED'
    HIGH = 'HIGH'

class RANGE_ENUM_LH(StrEnum):
    '''
    Enum class for range settings with low, medium, high options
    '''
    LOW = 'LOW'
    HIGH = 'HIGH'

class RANGE: # Deprecated?
    LOW = 'LOW'
    MEDIUM = 'MED'
    HIGH = 'HIGH'

# Predefined value maps for sinstruemnts to use
# "A list, tuple, range, or dictionary of valid values, that can be used as to map values if map_values is True"

BINARY = (0, 1)
BOOLEAN = (False, True)

# Primitive Constantants
BOOLEAN_TO_INT = {True: 1, False: 0}
BOOLEAN_TO_STR = {True: "True", False: "FALSE"}
BOOLEAN_TO_ON_OFF = {True: "ON", False: "OFF"}

normalize_str_to_upper = lambda input_str: input_str.upper()