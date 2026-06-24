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

from dataclasses import FrozenInstanceError

import pytest

from pymeasure.instruments.values import (
    DICTS,
    ENUMS,
    NORMAL_INVERTED_ENUM,
    RANGE_ENUM_LH,
    RANGE_ENUM_LMH,
    TUPLES,
)


def test_tuples_group_contents():
    assert TUPLES.BINARY == (0, 1)
    assert TUPLES.BOOLEAN == (False, True)


def test_dicts_group_contents():
    assert DICTS.BOOLEAN_TO_INT == {True: 1, False: 0}
    assert DICTS.BOOLEAN_TO_STR == {True: "True", False: "FALSE"}
    assert DICTS.BOOLEAN_TO_ON_OFF == {True: "ON", False: "OFF"}


def test_enums_group_references_shared_classes():
    assert ENUMS.RANGE_ENUM_LMH is RANGE_ENUM_LMH
    assert ENUMS.RANGE_ENUM_LH is RANGE_ENUM_LH
    assert ENUMS.NORMAL_INVERTED_ENUM is NORMAL_INVERTED_ENUM


@pytest.mark.parametrize("group", [TUPLES, DICTS, ENUMS])
def test_groups_are_frozen(group):
    with pytest.raises(FrozenInstanceError):
        group.BINARY = "mutated"
