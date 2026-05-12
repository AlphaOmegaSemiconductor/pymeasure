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
from pymeasure.adapters import ProtocolAdapter
from pymeasure.instruments.generic_types import (
    IEEE4882Mixin,
    SCPI1999Mixin,
    SCPIMixin,
    SCPIUnknownMixin,
)
from pymeasure.instruments import Instrument


class Test_SCPIMixin:
    class SCPIInstrument(SCPIMixin, Instrument):
        pass

    def test_init(self):
        inst = self.SCPIInstrument(ProtocolAdapter(), "test")
        assert inst.SCPI is False  # should not be set by the new init

    @pytest.mark.parametrize("method, write, reply", (
        ("id", "*IDN?", "xyz, abc"),
        ("complete", "*OPC?", "1"),
        ("status", "*STB?", "189"),
        ("options", "*OPT?", "a9"),
    ))
    def test_SCPI_properties(self, method, write, reply):
        with expected_protocol(
                self.SCPIInstrument,
                [(write, reply)],
                name="test") as inst:
            assert getattr(inst, method) == reply

    def test_next_error(self):
        with expected_protocol(
                self.SCPIInstrument,
                [("SYST:ERR?", '-100,"Command error"')],
                name="test") as inst:
            assert inst.next_error == [-100, '"Command error"']

    @pytest.mark.parametrize("method, write", (("clear", "*CLS"),
                                               ("reset", "*RST"),
                                               ))
    def test_SCPI_write_commands(self, method, write):
        with expected_protocol(
                self.SCPIInstrument,
                [(write, None)],
                name="test") as inst:
            getattr(inst, method)()

    def test_check_errors(self):
        with expected_protocol(
                self.SCPIInstrument,
                [("SYST:ERR?", '-100,"Command error"'),
                 ("SYST:ERR?", '-222,"Data out of range"'),
                 ("SYST:ERR?", '0,"No error"'),
                 ],
                name="test") as inst:
            assert inst.check_errors() == [[-100, '"Command error"'],
                                           [-222, '"Data out of range"']]


class Test_IEEE4882Mixin:
    class IEEEInstrument(IEEE4882Mixin, Instrument):
        pass

    def test_init(self):
        inst = self.IEEEInstrument(ProtocolAdapter(), "test")
        assert inst.SCPI is False

    @pytest.mark.parametrize("method, write, reply", (
        ("id", "*IDN?", "xyz, abc"),
        ("complete", "*OPC?", "1"),
        ("status", "*STB?", "189"),
        ("options", "*OPT?", "a9"),
    ))
    def test_legacy_properties(self, method, write, reply):
        with expected_protocol(
                self.IEEEInstrument,
                [(write, reply)],
                name="test") as inst:
            assert getattr(inst, method) == reply

    @pytest.mark.parametrize("method, write, reply, expected", (
        ("event_status", "*ESR?", "32", 32),
        ("event_status_enable", "*ESE?", "16", 16),
        ("service_request_enable", "*SRE?", "48", 48),
        ("self_test", "*TST?", "0", 0),
    ))
    def test_ieee4882_query_properties(self, method, write, reply, expected):
        with expected_protocol(
                self.IEEEInstrument,
                [(write, reply)],
                name="test") as inst:
            assert getattr(inst, method) == expected

    @pytest.mark.parametrize("attr, value, write", (
        ("event_status_enable", 16, "*ESE 16"),
        ("service_request_enable", 48, "*SRE 48"),
    ))
    def test_ieee4882_setters(self, attr, value, write):
        with expected_protocol(
                self.IEEEInstrument,
                [(write, None)],
                name="test") as inst:
            setattr(inst, attr, value)

    @pytest.mark.parametrize("attr, value", (
        ("event_status_enable", -1),
        ("event_status_enable", 256),
        ("service_request_enable", -1),
        ("service_request_enable", 256),
    ))
    def test_ieee4882_setter_out_of_range(self, attr, value):
        inst = self.IEEEInstrument(ProtocolAdapter(), "test")
        with pytest.raises(ValueError):
            setattr(inst, attr, value)

    @pytest.mark.parametrize("method, write", (
        ("clear", "*CLS"),
        ("reset", "*RST"),
        ("wait_to_continue", "*WAI"),
    ))
    def test_ieee4882_write_methods(self, method, write):
        with expected_protocol(
                self.IEEEInstrument,
                [(write, None)],
                name="test") as inst:
            getattr(inst, method)()

    def test_no_scpi_members_on_mixin(self):
        # next_error and check_errors live on SCPI1999Mixin, not IEEE4882Mixin.
        # (The Instrument base class provides deprecated fallbacks, so we check
        # the mixin class __dict__ directly rather than instance attribute lookup.)
        assert "next_error" not in IEEE4882Mixin.__dict__
        assert "check_errors" not in IEEE4882Mixin.__dict__
        assert "next_error" in SCPI1999Mixin.__dict__
        assert "check_errors" in SCPI1999Mixin.__dict__


class Test_SCPI1999Mixin:
    class SCPI1999Instrument(SCPI1999Mixin, Instrument):
        pass

    def test_inherits_ieee4882(self):
        assert issubclass(SCPI1999Mixin, IEEE4882Mixin)

    def test_has_ieee4882_member(self):
        with expected_protocol(
                self.SCPI1999Instrument,
                [("*IDN?", "xyz, abc")],
                name="test") as inst:
            assert inst.id == "xyz, abc"

    def test_has_scpi_member(self):
        with expected_protocol(
                self.SCPI1999Instrument,
                [("SYST:ERR?", '-100,"Command error"')],
                name="test") as inst:
            assert inst.next_error == [-100, '"Command error"']

    @pytest.mark.parametrize("method, write, reply, expected", (
        ("scpi_version", "SYST:VERS?", "1999.0", "1999.0"),
        ("operation_event", "STAT:OPER:EVEN?", "5", 5),
        ("operation_condition", "STAT:OPER:COND?", "9", 9),
        ("operation_enable", "STAT:OPER:ENAB?", "1024", 1024),
        ("questionable_event", "STAT:QUES:EVEN?", "3", 3),
        ("questionable_condition", "STAT:QUES:COND?", "7", 7),
        ("questionable_enable", "STAT:QUES:ENAB?", "512", 512),
    ))
    def test_scpi1999_query_properties(self, method, write, reply, expected):
        with expected_protocol(
                self.SCPI1999Instrument,
                [(write, reply)],
                name="test") as inst:
            assert getattr(inst, method) == expected

    @pytest.mark.parametrize("attr, value, write", (
        ("operation_enable", 1024, "STAT:OPER:ENAB 1024"),
        ("questionable_enable", 512, "STAT:QUES:ENAB 512"),
    ))
    def test_scpi1999_setters(self, attr, value, write):
        with expected_protocol(
                self.SCPI1999Instrument,
                [(write, None)],
                name="test") as inst:
            setattr(inst, attr, value)

    @pytest.mark.parametrize("attr, value", (
        ("operation_enable", -1),
        ("operation_enable", 65536),
        ("questionable_enable", -1),
        ("questionable_enable", 65536),
    ))
    def test_scpi1999_setter_out_of_range(self, attr, value):
        inst = self.SCPI1999Instrument(ProtocolAdapter(), "test")
        with pytest.raises(ValueError):
            setattr(inst, attr, value)

    def test_status_preset(self):
        with expected_protocol(
                self.SCPI1999Instrument,
                [("STAT:PRES", None)],
                name="test") as inst:
            inst.status_preset()


def test_scpi_mixin_alias():
    assert SCPIMixin is SCPI1999Mixin


def test_SCPIunknownMixin():
    class SCPIunknownInstrument(SCPIUnknownMixin, Instrument):
        pass

    with pytest.warns(FutureWarning):
        inst = SCPIunknownInstrument(ProtocolAdapter(), "test")
    assert inst.SCPI is False
