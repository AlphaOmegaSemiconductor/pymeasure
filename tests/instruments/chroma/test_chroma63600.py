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

from pymeasure.test import expected_protocol

from pymeasure.instruments.chroma.Chroma_63600_electronic_load_mainframe import Chroma63600


def test_init():
    with expected_protocol(
        Chroma63600,
        [],
    ):
        pass  # Verify the channels build without any communication.


def test_channels_created():
    with expected_protocol(Chroma63600, []) as inst:
        assert set(inst.channels.keys()) == {1, 2, 3, 4, 5}
        assert inst.ch_2 is inst.channels[2]


def test_channel_select_prefix_on_measure():
    with expected_protocol(
        Chroma63600,
        [(b"CHAN 2;:MEAS:VOLT?", b"12.5")],
    ) as inst:
        assert inst.ch_2.voltage == 12.5


def test_setpoints_target_selected_channel():
    with expected_protocol(
        Chroma63600,
        [
            (b"CHAN 1;:CURR 5", None),
            (b"CHAN 3;:VOLT 24", None),
        ],
    ) as inst:
        inst.ch_1.current_setpoint = 5
        inst.ch_3.voltage_setpoint = 24


def test_mode_set_and_query():
    with expected_protocol(
        Chroma63600,
        [
            (b"CHAN 4;:MODE CC", None),
            (b"CHAN 4;:MODE?", b"CC"),
        ],
    ) as inst:
        inst.ch_4.mode = "CC"
        assert inst.ch_4.mode == "CC"


def test_load_enabled_maps_bool():
    with expected_protocol(
        Chroma63600,
        [
            (b"CHAN 5;:LOAD 1", None),
            (b"CHAN 5;:LOAD?", b"0"),
        ],
    ) as inst:
        inst.ch_5.load_enabled = True
        assert inst.ch_5.load_enabled is False
