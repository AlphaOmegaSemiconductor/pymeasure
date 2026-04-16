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

from pymeasure.test import expected_protocol
from pymeasure.instruments.tektronix.afg31000 import AFG31000, AFG31000Channel
from pymeasure.instruments.values import InstrumentStrEnum


# --- InstrumentStrEnum membership tests (no hardware needed) ---

def test_constants_are_instrument_str_enums():
    assert issubclass(AFG31000Channel.VOLTAGE_UNITS, InstrumentStrEnum)
    assert issubclass(AFG31000Channel.BURST_MODES, InstrumentStrEnum)
    assert issubclass(AFG31000Channel.SWEEP_TYPES, InstrumentStrEnum)
    assert issubclass(AFG31000Channel.MOD_SOURCES, InstrumentStrEnum)
    assert issubclass(AFG31000Channel.POLARITY, InstrumentStrEnum)
    assert issubclass(AFG31000.TRIGGER_SOURCES, InstrumentStrEnum)


def test_member_names_are_uppercased():
    assert AFG31000Channel.BURST_MODES.TRIGGERED == "TRIGgered"
    assert AFG31000Channel.BURST_MODES.GATED == "GATed"
    assert AFG31000Channel.BURST_MODES.INFINITY == "INFinity"
    assert AFG31000Channel.SWEEP_TYPES.LINEAR == "LINear"
    assert AFG31000Channel.SWEEP_TYPES.LOGARITHMIC == "LOGarithmic"
    assert AFG31000Channel.MOD_SOURCES.INTERNAL == "INTernal"
    assert AFG31000Channel.POLARITY.NORMAL == "NORMal"
    assert AFG31000Channel.POLARITY.INVERTED == "INVerted"


def test_containment_by_original_value():
    assert "VPP" in AFG31000Channel.VOLTAGE_UNITS
    assert "VRMS" in AFG31000Channel.VOLTAGE_UNITS
    assert "DBM" in AFG31000Channel.VOLTAGE_UNITS
    assert "TRIGgered" in AFG31000Channel.BURST_MODES
    assert "LINear" in AFG31000Channel.SWEEP_TYPES
    assert "INTernal" in AFG31000Channel.MOD_SOURCES
    assert "NORMal" in AFG31000Channel.POLARITY
    assert "INTernal" in AFG31000.TRIGGER_SOURCES
    assert "MAN" in AFG31000.TRIGGER_SOURCES


def test_wrong_case_not_contained():
    assert "vpp" not in AFG31000Channel.VOLTAGE_UNITS
    assert "TRIGGERED" not in AFG31000Channel.BURST_MODES
    assert "linear" not in AFG31000Channel.SWEEP_TYPES


def test_str_returns_original_value():
    assert str(AFG31000Channel.BURST_MODES.TRIGGERED) == "TRIGgered"
    assert str(AFG31000Channel.SWEEP_TYPES.LINEAR) == "LINear"
    assert str(AFG31000Channel.POLARITY.NORMAL) == "NORMal"


# --- Property round-trip tests via expected_protocol ---

def test_voltage_unit_set():
    with expected_protocol(
        AFG31000,
        [("source1:voltage:unit VPP", None)],
    ) as inst:
        inst.ch1.voltage_unit = "VPP"


def test_voltage_unit_get():
    with expected_protocol(
        AFG31000,
        [("source1:voltage:unit?", "VRMS")],
    ) as inst:
        assert inst.ch1.voltage_unit == "VRMS"


def test_voltage_unit_rejects_invalid():
    with expected_protocol(AFG31000, []) as inst:
        with pytest.raises(ValueError):
            inst.ch1.voltage_unit = "INVALID"


def test_burst_mode_set():
    with expected_protocol(
        AFG31000,
        [("source1:burst:mode TRIGgered", None)],
    ) as inst:
        inst.ch1.burst_mode = "TRIGgered"


def test_sweep_type_set():
    with expected_protocol(
        AFG31000,
        [("source1:sweep:type LINear", None)],
    ) as inst:
        inst.ch1.sweep_type = "LINear"


def test_output_polarity_set():
    with expected_protocol(
        AFG31000,
        [("source1:output:polarity NORMal", None)],
    ) as inst:
        inst.ch1.output_polarity = "NORMal"


def test_trigger_source_set():
    with expected_protocol(
        AFG31000,
        [("trigger:source INTernal", None)],
    ) as inst:
        inst.trigger_source = "INTernal"


def test_trigger_source_rejects_invalid():
    with expected_protocol(AFG31000, []) as inst:
        with pytest.raises(ValueError):
            inst.trigger_source = "INVALID"
