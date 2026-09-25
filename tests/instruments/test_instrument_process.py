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

import pytest

from pymeasure.instruments.process import normalize_channel_source, preprocess_input_enum
from pymeasure.instruments.values import str_enum_from_values


@pytest.mark.parametrize("source, expected", [
    (1, "CH1"),
    (4, "CH4"),
    (58, "CH58"),
    ("1", "CH1"),
    (" 2 ", "CH2"),
    ("CH1", "CH1"),
    ("ch3", "CH3"),
    ("aux", "AUX"),
    ("line", "LINE"),
    (" AUX ", "AUX"),
])
def test_normalize_channel_source(source, expected):
    assert normalize_channel_source(source) == expected


WAVEFORM = str_enum_from_values("Waveform", ["SINusoid", "SQUare"])
SHAPES = str_enum_from_values("Shapes", {"memory": "EMEM", "file": "EFIL"})
# A probe pair where one member's readable name begins with the other's SCPI short form.
PROBES = str_enum_from_values("Probes", {"thermistor": "THERmistor",
                                         "thermocouple": "TCouple"})


@pytest.mark.parametrize("value, expected", [
    ("sin", WAVEFORM.SINUSOID),
    ("SIN", WAVEFORM.SINUSOID),
    ("SINusoid", WAVEFORM.SINUSOID),
    # The lenient rule accepts any string starting with the short form.
    ("Sinusoidal", WAVEFORM.SINUSOID),
    ("SQUARE", WAVEFORM.SQUARE),
    ("TRI", "TRI"),
    (50, 50),
    (float("inf"), float("inf")),
])
def test_preprocess_input_enum_lenient(value, expected):
    assert preprocess_input_enum(WAVEFORM)(value) == expected


@pytest.mark.parametrize("value, expected", [
    ("memory", SHAPES.MEMORY),
    ("mem", SHAPES.MEMORY),
    ("EMEM", SHAPES.MEMORY),
    ("me", "me"),
])
def test_preprocess_input_enum_matches_member_names(value, expected):
    assert preprocess_input_enum(SHAPES)(value) == expected


@pytest.mark.parametrize("value, expected", [
    ("sin", WAVEFORM.SINUSOID),
    ("sinus", WAVEFORM.SINUSOID),
    ("SINusoid", WAVEFORM.SINUSOID),
    # Strict matching requires a genuine abbreviation, so an over-long word is declined.
    ("Sinusoidal", "Sinusoidal"),
    # ...and anything shorter than the mandatory short form.
    ("si", "si"),
])
def test_preprocess_input_enum_strict(value, expected):
    assert preprocess_input_enum(WAVEFORM, strict_abbreviation=True)(value) == expected


def test_preprocess_input_enum_lenient_captures_longer_name():
    """The default rule resolves 'thermocouple' to THERmistor -- the case strict fixes."""
    assert preprocess_input_enum(PROBES)("thermocouple") is PROBES.THERMISTOR


@pytest.mark.parametrize("value, expected", [
    ("thermocouple", PROBES.THERMOCOUPLE),
    ("tc", PROBES.THERMOCOUPLE),
    ("TCouple", PROBES.THERMOCOUPLE),
    ("thermistor", PROBES.THERMISTOR),
    ("ther", PROBES.THERMISTOR),
    ("THERmistor", PROBES.THERMISTOR),
])
def test_preprocess_input_enum_strict_resolves_colliding_names(value, expected):
    assert preprocess_input_enum(PROBES, strict_abbreviation=True)(value) is expected
