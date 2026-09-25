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

from pymeasure.instruments.keysight.keysight_34465A import DMM34465A
from pymeasure.test import expected_protocol

# ``DMM34465A.__init__`` drains the error queue, so every protocol exchange starts here.
INIT = [("SYST:ERR?", '+0,"No error"')]


@pytest.mark.parametrize("args, kwargs, command", [
    # Defaults: a type K thermocouple, unlike the instrument's own FRTD default.
    ((), {}, "CONFigure:TEMPerature TCouple,K"),
    # Readable names, SCPI mnemonics and abbreviations all reach the same command.
    (("thermocouple",), {}, "CONFigure:TEMPerature TCouple,K"),
    (("TCouple",), {}, "CONFigure:TEMPerature TCouple,K"),
    (("tc",), {}, "CONFigure:TEMPerature TCouple,K"),
    (("thermo",), {}, "CONFigure:TEMPerature TCouple,K"),
    # The alloy is honoured and upper-cased.
    ((), {"thermocouple_type": "j"}, "CONFigure:TEMPerature TCouple,J"),
    (("thermocouple", "T"), {}, "CONFigure:TEMPerature TCouple,T"),
    # RTD and thermistor probes ignore the alloy and use their single permitted type.
    (("rtd",), {"thermocouple_type": "J"}, "CONFigure:TEMPerature RTD,85"),
    (("rtd_4wire",), {}, "CONFigure:TEMPerature FRTD,85"),
    (("FRTD",), {}, "CONFigure:TEMPerature FRTD,85"),
    (("thermistor",), {}, "CONFigure:TEMPerature THERmistor,5000"),
    (("ther",), {}, "CONFigure:TEMPerature THERmistor,5000"),
    (("thermistor_4wire",), {}, "CONFigure:TEMPerature FTHermistor,5000"),
    (("fth",), {}, "CONFigure:TEMPerature FTHermistor,5000"),
    # A resolution drags in the mandatory implied range parameter of 1.
    ((), {"resolution": 1e-6}, "CONFigure:TEMPerature TCouple,K,1,1e-06"),
    ((), {"resolution": "MAX"}, "CONFigure:TEMPerature TCouple,K,1,MAXimum"),
    ((), {"resolution": "minimum"}, "CONFigure:TEMPerature TCouple,K,1,MINimum"),
    (("rtd_4wire",), {"resolution": "def"}, "CONFigure:TEMPerature FRTD,85,1,DEFault"),
])
def test_configure_temperature(args, kwargs, command):
    with expected_protocol(DMM34465A, INIT + [(command, None)]) as dmm:
        dmm.configure_temperature(*args, **kwargs)


def test_configure_temperature_thermocouple_is_not_a_thermistor():
    """'thermocouple' must not resolve to THERmistor, whose short form it begins with."""
    with expected_protocol(
        DMM34465A, INIT + [("CONFigure:TEMPerature TCouple,K", None)]
    ) as dmm:
        dmm.configure_temperature("thermocouple")


@pytest.mark.parametrize("args, kwargs", [
    (("bogus",), {}),
    (("",), {}),
    ((), {"thermocouple_type": "Q"}),
    ((), {"resolution": "SOMETHING"}),
])
def test_configure_temperature_rejects_bad_values(args, kwargs):
    with expected_protocol(DMM34465A, INIT) as dmm:
        with pytest.raises(ValueError):
            dmm.configure_temperature(*args, **kwargs)


@pytest.mark.parametrize("value, mnemonic", [
    ("C", "C"),
    ("celsius", "C"),
    ("cel", "C"),
    ("f", "F"),
    ("fahrenheit", "F"),
    ("kelvin", "K"),
])
def test_temperature_unit_setter(value, mnemonic):
    with expected_protocol(
        DMM34465A, INIT + [(f"UNIT:TEMPerature {mnemonic}", None)]
    ) as dmm:
        dmm.temperature_unit = value


def test_temperature_unit_getter():
    with expected_protocol(DMM34465A, INIT + [("UNIT:TEMPerature?", "C")]) as dmm:
        assert dmm.temperature_unit == "C"


def test_temperature_unit_rejects_bad_value():
    with expected_protocol(DMM34465A, INIT) as dmm:
        with pytest.raises(ValueError):
            dmm.temperature_unit = "rankine"
