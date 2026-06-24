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

from dataclasses import dataclass

import pytest

from pymeasure.instruments.specs import SCPI_ID, InstrumentSpecs, scpi_id_parser


# --- scpi_id_parser ---

def test_scpi_id_parser_good_string():
    result = scpi_id_parser("TEKTRONIX,AFG31052,C013513,SCPI:99.0 FV:1.6.1")
    assert result == {
        "manufacturer": "TEKTRONIX",
        "model_num": "AFG31052",
        "serial_num": "C013513",
        "software_rev": "SCPI:99.0 FV:1.6.1",
    }


def test_scpi_id_parser_strips_whitespace():
    result = scpi_id_parser(" TEKTRONIX , AFG31052 , C013513 , 1.6.1 ")
    assert result["manufacturer"] == "TEKTRONIX"
    assert result["model_num"] == "AFG31052"
    assert result["serial_num"] == "C013513"
    assert result["software_rev"] == "1.6.1"


def test_scpi_id_parser_short_string_all_none():
    result = scpi_id_parser("TEKTRONIX,AFG31052,C013513")
    assert all(value is None for value in result.values())


@pytest.mark.parametrize("bad", ["", None])
def test_scpi_id_parser_empty_or_none_all_none(bad):
    result = scpi_id_parser(bad)
    assert all(value is None for value in result.values())
    assert set(result) == {"manufacturer", "model_num", "serial_num", "software_rev"}


# --- SCPI_ID dataclass ---

def test_scpi_id_from_id_model_num():
    scpi_id = SCPI_ID.from_id("TEKTRONIX,AFG31052,C013513,SCPI:99.0 FV:1.6.1")
    assert scpi_id.model_num == "AFG31052"
    assert scpi_id.manufacturer == "TEKTRONIX"


def test_scpi_id_from_id_short_string_all_none():
    scpi_id = SCPI_ID.from_id("only,two")
    assert scpi_id == SCPI_ID()


def test_scpi_id_is_frozen():
    scpi_id = SCPI_ID.from_id("TEKTRONIX,AFG31052,C013513,1.6.1")
    with pytest.raises(Exception):
        scpi_id.model_num = "AFG31101"


def test_scpi_id_dict_round_trip():
    scpi_id = SCPI_ID.from_id("TEKTRONIX,AFG31052,C013513,1.6.1")
    assert SCPI_ID.from_dict(scpi_id.to_dict()) == scpi_id


def test_scpi_id_validate_true_when_complete():
    assert SCPI_ID.from_id("TEKTRONIX,AFG31052,C013513,1.6.1").validate() is True


def test_scpi_id_validate_false_when_incomplete():
    assert SCPI_ID(manufacturer="TEKTRONIX").validate() is False
    assert SCPI_ID().validate() is False


# --- InstrumentSpecs base + from_registry ---

@dataclass(frozen=True)
class _DummySpecs(InstrumentSpecs):
    model_num: str = ""
    channels: int = 0


_REGISTRY = {s.model_num: s for s in (
    _DummySpecs("MODEL-A", 1),
    _DummySpecs("MODEL-B", 2),
)}


def test_normalize_model():
    assert InstrumentSpecs.normalize_model("  model-a ") == "MODEL-A"


def test_from_registry_resolves_case_insensitively():
    spec = _DummySpecs.from_registry("model-a", _REGISTRY)
    assert spec.channels == 1
    assert spec is _REGISTRY["MODEL-A"]


def test_from_registry_unknown_lists_supported():
    with pytest.raises(KeyError) as exc:
        _DummySpecs.from_registry("MODEL-Z", _REGISTRY)
    message = str(exc.value)
    assert "MODEL-A" in message and "MODEL-B" in message


def test_to_dict_contains_subclass_fields():
    assert _DummySpecs("MODEL-A", 1).to_dict() == {"model_num": "MODEL-A", "channels": 1}
