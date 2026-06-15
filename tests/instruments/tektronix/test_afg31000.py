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
from pymeasure.instruments.tektronix.afg31000 import (
    AFG31000, AFG31000Channel, AFG31000Sequence, AFG31000SequenceElement,
    AFG31000Memory,
)
from pymeasure.instruments.channel import Channel
from pymeasure.instruments.sub_instrument import SubInstrument
from pymeasure.instruments.values import InstrumentStrEnum

# Construction calls ``reset()``, which writes ``*RST`` before any test traffic.
RESET = ("*RST", None)


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
    with expected_protocol(AFG31000, [RESET]) as inst:
        with pytest.raises(ValueError):
            inst.trigger_source = "INVALID"


# --- Sequence sub-instrument and element-channel tests ---

def test_sequence_types():
    assert issubclass(AFG31000Sequence, SubInstrument)
    assert issubclass(AFG31000SequenceElement, Channel)


def test_sequence_element_dict_is_one_based():
    with expected_protocol(AFG31000, [RESET]) as inst:
        elements = inst.sequence.element
        assert isinstance(elements, dict)
        assert len(elements) == AFG31000Sequence.NUM_ELEMENTS
        assert min(elements) == 1
        assert max(elements) == AFG31000Sequence.NUM_ELEMENTS
        assert isinstance(elements[1], AFG31000SequenceElement)
        assert elements[1].id == 1


def test_sequence_length_round_trip():
    with expected_protocol(
        AFG31000,
        [RESET, ("sequence:length 2", None), ("sequence:length?", "2")],
    ) as inst:
        inst.sequence.length = 2
        assert inst.sequence.length == 2


def test_sequence_length_rejects_out_of_range():
    with expected_protocol(AFG31000, [RESET]) as inst:
        with pytest.raises(ValueError):
            inst.sequence.length = 257


def test_sequence_new():
    with expected_protocol(AFG31000, [RESET, ("sequence:new", None)]) as inst:
        inst.sequence.new()


def test_sequence_run_control():
    with expected_protocol(
        AFG31000,
        [
            RESET,
            ("seqcontrol:rmode SEQuence", None),
            ("seqcontrol:state 1", None),
            ("seqcontrol:rstate?", "1"),
            ("seqcontrol:run:immediate", None),
            ("seqcontrol:stop:immediate", None),
            ("seqcontrol:reset:immediate", None),
        ],
    ) as inst:
        inst.sequence.run_mode = "SEQuence"
        inst.sequence.state = True
        assert inst.sequence.running is True
        inst.sequence.run()
        inst.sequence.stop()
        inst.sequence.reset()


def test_sequence_source_scale_and_offset():
    with expected_protocol(
        AFG31000,
        [
            RESET,
            ("seqcontrol:source1:scale 50", None),
            ("seqcontrol:source2:offset?", "0.1"),
        ],
    ) as inst:
        inst.sequence.set_source_scale(50, channel=1)
        assert inst.sequence.source_offset(channel=2) == 0.1


def test_sequence_element_properties():
    with expected_protocol(
        AFG31000,
        [
            RESET,
            ("sequence:elem1:loop:count 100", None),
            ("sequence:elem1:goto:state 1", None),
            ("sequence:elem1:goto:index 6", None),
            ("sequence:elem2:jtarget:type INDex", None),
            ("sequence:elem3:jump:slope?", "POS"),
            ('sequence:elem1:waveform1 "P:/Pulse1000.tfwx"', None),
            ("sequence:elem1:waveform2?", "M:/Sine.tfwx"),
        ],
    ) as inst:
        inst.sequence.element[1].loop_count = 100
        inst.sequence.element[1].goto_state = True
        inst.sequence.element[1].goto_index = 6
        inst.sequence.element[2].jump_target_type = "INDex"
        assert inst.sequence.element[3].jump_slope == "POS"
        inst.sequence.element[1].set_waveform("P:/Pulse1000.tfwx", channel=1)
        assert inst.sequence.element[1].waveform(channel=2) == "M:/Sine.tfwx"


def test_sequence_element_rejects_out_of_range():
    with expected_protocol(AFG31000, [RESET]) as inst:
        with pytest.raises(ValueError):
            inst.sequence.element[1].goto_index = 0
        with pytest.raises(ValueError):
            inst.sequence.element[1].loop_count = 2_000_000


# --- Memory sub-instrument tests ---

def test_memory_types():
    assert issubclass(AFG31000Memory, SubInstrument)


def test_memory_is_wired():
    with expected_protocol(AFG31000, [RESET]) as inst:
        assert isinstance(inst.memory, AFG31000Memory)


def test_memory_usb_delete_matches_manual_example():
    # MMEMORY:DELETE "U:/TEK001.TFWX"  <->  instrument.memory.usb_delete = 'TEK001.TFWX'
    with expected_protocol(
        AFG31000,
        [RESET, ('mmemory:delete "U:/TEK001.TFWX"', None)],
    ) as inst:
        inst.memory.usb_delete = "TEK001.TFWX"


def test_memory_internal_delete_keeps_relative_subpath():
    with expected_protocol(
        AFG31000,
        [RESET, ('mmemory:delete "M:/sub/TEK001.TFWX"', None)],
    ) as inst:
        inst.memory.memory_delete = "sub/TEK001.TFWX"


def test_memory_write_commands_have_no_read_only_alias():
    # P: is read-only, so write commands only get usb_/memory_ forms.
    for command in ("delete", "make_directory", "save_sequence", "save_setup"):
        assert hasattr(AFG31000Memory, f"usb_{command}")
        assert hasattr(AFG31000Memory, f"memory_{command}")
        assert not hasattr(AFG31000Memory, f"read_only_memory_{command}")


def test_memory_read_commands_have_all_three_aliases():
    for command in ("change_directory", "open_sequence", "recall_setup"):
        assert hasattr(AFG31000Memory, f"usb_{command}")
        assert hasattr(AFG31000Memory, f"memory_{command}")
        assert hasattr(AFG31000Memory, f"read_only_memory_{command}")


def test_memory_open_sequence_all_three_drives():
    with expected_protocol(
        AFG31000,
        [
            RESET,
            ('mmemory:open:sequence "U:/AFGseq.seq"', None),
            ('mmemory:open:sequence "M:/AFGseq.seq"', None),
            ('mmemory:open:sequence "P:/AFGseq.seq"', None),
        ],
    ) as inst:
        inst.memory.usb_open_sequence = "AFGseq.seq"
        inst.memory.memory_open_sequence = "AFGseq.seq"
        inst.memory.read_only_memory_open_sequence = "AFGseq.seq"


def test_memory_make_directory():
    with expected_protocol(
        AFG31000,
        [RESET, ('mmemory:mdirectory "M:/sample"', None)],
    ) as inst:
        inst.memory.memory_make_directory = "sample"


def test_memory_current_directory_query_strips_quotes():
    with expected_protocol(
        AFG31000,
        [RESET, ("mmemory:cdirectory?", '"U:/AFG/WORK0"')],
    ) as inst:
        assert inst.memory.current_directory == "U:/AFG/WORK0"


def test_memory_change_directory():
    with expected_protocol(
        AFG31000,
        [RESET, ('mmemory:cdirectory "U:/AFG/WORK0"', None)],
    ) as inst:
        inst.memory.usb_change_directory = "AFG/WORK0"


def test_memory_load_trace_from_predefined_drive():
    with expected_protocol(
        AFG31000,
        [RESET, ('mmemory:load:trace ememory2,"P:/Sine.tfwx"', None)],
    ) as inst:
        inst.memory.read_only_memory_load_trace("Sine.tfwx", edit_memory=2)


def test_memory_store_state_is_usb_and_internal_only():
    assert hasattr(AFG31000Memory, "usb_store_state")
    assert hasattr(AFG31000Memory, "memory_store_state")
    assert not hasattr(AFG31000Memory, "read_only_memory_store_state")
    with expected_protocol(
        AFG31000,
        [RESET, ('mmemory:store:state 1,"M:/test1.tfs"', None)],
    ) as inst:
        inst.memory.memory_store_state(1, "test1.tfs")


def test_memory_lock_round_trip():
    with expected_protocol(
        AFG31000,
        [
            RESET,
            ('mmemory:lock:state "M:/setup1.tfs",1', None),
            ('mmemory:lock:state? "M:/setup1.tfs"', "1"),
        ],
    ) as inst:
        inst.memory.memory_set_lock("setup1.tfs", True)
        assert inst.memory.memory_lock_state("setup1.tfs") is True


def test_setup_memory_save_and_recall():
    with expected_protocol(
        AFG31000,
        [RESET, ("*SAV 2", None), ("*RCL 2", None)],
    ) as inst:
        inst.memory.save(2)
        inst.memory.recall(2)


def test_setup_memory_valid_query():
    with expected_protocol(
        AFG31000,
        [RESET, ("memory:state:valid? 0", "1")],
    ) as inst:
        assert inst.memory.setup_valid(0) is True


def test_setup_memory_save_rejects_out_of_range():
    with expected_protocol(AFG31000, [RESET]) as inst:
        with pytest.raises(ValueError):
            inst.memory.save(5)


def test_setup_recall_last_auto_round_trip():
    with expected_protocol(
        AFG31000,
        [
            RESET,
            ("memory:state:recall:auto 1", None),
            ("memory:state:recall:auto?", "1"),
        ],
    ) as inst:
        inst.memory.recall_last_auto = True
        assert inst.memory.recall_last_auto is True
