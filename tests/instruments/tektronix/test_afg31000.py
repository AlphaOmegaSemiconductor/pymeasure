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
    AFG31000Memory, AFG31000Specs, AFG31000_MODELS,
)
from pymeasure.instruments.channel import Channel
from pymeasure.instruments.sub_instrument import SubInstrument
from pymeasure.instruments.values import InstrumentStrEnum, Choices
from pymeasure.instruments.process import preprocess_input_enum


def _afg(comm_pairs, *, model="AFG31021", **kwargs):
    """``expected_protocol`` wrapper for :class:`AFG31000`.

    Defaults to the lowest-spec model (1-channel ``AFG31021``) and passes it via
    the ``model`` kwarg so construction skips the ``*IDN?`` query — keeping the
    comm-pair protocol focused on the command under test. These existing tests
    only ever use ``ch1``, so a 1-channel default is sufficient.
    """
    return expected_protocol(AFG31000, comm_pairs, model=model, **kwargs)


# --- InstrumentStrEnum membership tests (no hardware needed) ---

def test_constants_are_instrument_str_enums():
    assert issubclass(AFG31000Channel.choices.voltage_unit, InstrumentStrEnum)
    assert issubclass(AFG31000Channel.choices.burst_mode, InstrumentStrEnum)
    assert issubclass(AFG31000Channel.choices.sweep_spacing, InstrumentStrEnum)
    assert issubclass(AFG31000Channel.choices.am_source, InstrumentStrEnum)
    assert issubclass(AFG31000Channel.choices.output_polarity, InstrumentStrEnum)
    assert issubclass(AFG31000.choices.trigger_source, InstrumentStrEnum)


def test_member_names_are_uppercased():
    assert AFG31000Channel.choices.burst_mode.TRIGGERED == "TRIGgered"
    assert AFG31000Channel.choices.burst_mode.GATED == "GATed"
    assert AFG31000Channel.choices.burst_mode.INFINITY == "INFinity"
    assert AFG31000Channel.choices.sweep_spacing.LINEAR == "LINear"
    assert AFG31000Channel.choices.sweep_spacing.LOGARITHMIC == "LOGarithmic"
    assert AFG31000Channel.choices.am_source.INTERNAL == "INTernal"
    assert AFG31000Channel.choices.output_polarity.NORMAL == "NORMal"
    assert AFG31000Channel.choices.output_polarity.INVERTED == "INVerted"


def test_containment_by_original_value():
    assert "VPP" in AFG31000Channel.choices.voltage_unit
    assert "VRMS" in AFG31000Channel.choices.voltage_unit
    assert "DBM" in AFG31000Channel.choices.voltage_unit
    assert "TRIGgered" in AFG31000Channel.choices.burst_mode
    assert "LINear" in AFG31000Channel.choices.sweep_spacing
    assert "INTernal" in AFG31000Channel.choices.am_source
    assert "NORMal" in AFG31000Channel.choices.output_polarity
    assert "INTernal" in AFG31000.choices.trigger_source
    assert "MAN" in AFG31000.choices.trigger_source


def test_wrong_case_not_contained():
    assert "vpp" not in AFG31000Channel.choices.voltage_unit
    assert "TRIGGERED" not in AFG31000Channel.choices.burst_mode
    assert "linear" not in AFG31000Channel.choices.sweep_spacing


def test_str_returns_original_value():
    assert str(AFG31000Channel.choices.burst_mode.TRIGGERED) == "TRIGgered"
    assert str(AFG31000Channel.choices.sweep_spacing.LINEAR) == "LINear"
    assert str(AFG31000Channel.choices.output_polarity.NORMAL) == "NORMal"


# --- SHAPES name/value resolution via preprocess_input_enum ---

def test_shape_resolves_value_short_form():
    proc = preprocess_input_enum(AFG31000Channel.choices.shape)
    assert proc("EMEM") is AFG31000Channel.choices.shape.MEMORY
    assert proc("emem") is AFG31000Channel.choices.shape.MEMORY


@pytest.mark.parametrize("value", ["memory", "MEMORY", "Memory", "mem", "memo"])
def test_shape_resolves_human_readable_name(value):
    proc = preprocess_input_enum(AFG31000Channel.choices.shape)
    assert proc(value) is AFG31000Channel.choices.shape.MEMORY


def test_shape_name_below_floor_returns_unchanged():
    # 'me' is shorter than the 3-char floor, so it is not resolved to a member.
    proc = preprocess_input_enum(AFG31000Channel.choices.shape)
    assert proc("me") == "me"


def test_shape_short_name_matches_in_full():
    # 'dc' is only 2 chars; the floor is capped at the name length so it still matches.
    proc = preprocess_input_enum(AFG31000Channel.choices.shape)
    assert proc("dc") is AFG31000Channel.choices.shape.DC


def test_shape_set_by_name():
    with _afg(
        [("source1:function:shape EMEM", None)],
    ) as inst:
        inst.ch1.shape = "memory"


def test_shape_set_by_name_abbreviation():
    with _afg(
        [("source1:function:shape EMEM", None)],
    ) as inst:
        inst.ch1.shape = "mem"


def test_shape_get_returns_scpi_mnemonic():
    with _afg(
        [("source1:function:shape?", "EMEM")],
    ) as inst:
        assert inst.ch1.shape == "EMEM"


# --- Case-insensitive enum member access (independent of Choices) ---

def test_enum_member_access_case_insensitive():
    assert AFG31000Channel.choices.shape.square is AFG31000Channel.choices.shape.SQUARE
    assert AFG31000Channel.choices.shape.Square is AFG31000Channel.choices.shape.SQUARE
    assert AFG31000Channel.choices.shape.SQUARE.value == "SQU"


def test_enum_member_access_unknown_still_raises():
    with pytest.raises(AttributeError):
        AFG31000Channel.choices.shape.not_a_member


# --- Choices container ---

def test_choices_expose_property_named_enums():
    assert issubclass(AFG31000Channel.choices.shape, InstrumentStrEnum)
    assert issubclass(AFG31000.choices.trigger_source, InstrumentStrEnum)
    assert AFG31000Sequence.choices.run_mode.SEQUENCE == "SEQuence"


def test_choices_shared_enum_is_aliased():
    # am/fm/pm modulation sources all reference the one MOD_SOURCES enum.
    assert AFG31000Channel.choices.am_source is AFG31000Channel.choices.fm_source
    assert AFG31000Channel.choices.am_source is AFG31000Channel.choices.pm_source


def test_choices_member_access_exact_and_case_insensitive():
    assert AFG31000Channel.choices.shape.SQUARE == "SQU"
    assert AFG31000Channel.choices.shape.square is AFG31000Channel.choices.shape.SQUARE


def test_choices_repr_lists_properties_and_members():
    text = repr(AFG31000Channel.choices)
    assert "shape" in text
    assert "SQUARE" in text


def test_choices_accessible_from_instance():
    with _afg([]) as inst:
        assert inst.ch1.choices.shape is AFG31000Channel.choices.shape


def test_choices_set_shape_end_to_end():
    with _afg(
        [("source1:function:shape SQU", None)],
    ) as inst:
        inst.ch1.shape = inst.ch1.choices.shape.square


def test_choices_unknown_attribute_raises():
    with pytest.raises(AttributeError):
        AFG31000Channel.choices.not_a_property


def test_choices_is_immutable():
    with pytest.raises(AttributeError):
        AFG31000Channel.choices.shape = "anything"
    with pytest.raises(AttributeError):
        del AFG31000Channel.choices.shape


def test_choices_subclass_of_base():
    assert issubclass(AFG31000Channel.choices, Choices)


def test_sequence_element_choices_wired():
    assert AFG31000SequenceElement.choices.jump_slope.positive == "POSitive"
    # jump_* and wait_* share the same underlying enums.
    assert AFG31000SequenceElement.choices.wait_slope is AFG31000SequenceElement.choices.jump_slope
    assert AFG31000SequenceElement.choices.wait_event is AFG31000SequenceElement.choices.jump_event


# --- Property round-trip tests via expected_protocol ---

def test_voltage_unit_set():
    with _afg(
        [("source1:voltage:unit VPP", None)],
    ) as inst:
        inst.ch1.voltage_unit = "VPP"


def test_voltage_unit_get():
    with _afg(
        [("source1:voltage:unit?", "VRMS")],
    ) as inst:
        assert inst.ch1.voltage_unit == "VRMS"


def test_voltage_unit_rejects_invalid():
    with _afg([]) as inst:
        with pytest.raises(ValueError):
            inst.ch1.voltage_unit = "INVALID"


def test_burst_mode_set():
    with _afg(
        [("source1:burst:mode TRIGgered", None)],
    ) as inst:
        inst.ch1.burst_mode = "TRIGgered"


def test_sweep_type_set():
    with _afg(
        [("source1:sweep:spacing LINear", None)],
    ) as inst:
        inst.ch1.sweep_spacing = "LINear"


def test_output_polarity_set():
    with _afg(
        [("output1:polarity NORMal", None)],
    ) as inst:
        inst.ch1.output_polarity = "NORMal"


def test_trigger_source_set():
    with _afg(
        [("trigger:source INTernal", None)],
    ) as inst:
        inst.trigger_source = "INTernal"


def test_trigger_source_rejects_invalid():
    with _afg([]) as inst:
        with pytest.raises(ValueError):
            inst.trigger_source = "INVALID"


# --- Sequence sub-instrument and element-channel tests ---

def test_sequence_types():
    assert issubclass(AFG31000Sequence, SubInstrument)
    assert issubclass(AFG31000SequenceElement, Channel)


def test_sequence_element_dict_is_one_based():
    with _afg([]) as inst:
        elements = inst.sequence.element
        assert isinstance(elements, dict)
        assert len(elements) == AFG31000Sequence.NUM_ELEMENTS
        assert min(elements) == 1
        assert max(elements) == AFG31000Sequence.NUM_ELEMENTS
        assert isinstance(elements[1], AFG31000SequenceElement)
        assert elements[1].id == 1


def test_sequence_length_round_trip():
    with _afg(
        [("sequence:length 2", None), ("sequence:length?", "2")],
    ) as inst:
        inst.sequence.length = 2
        assert inst.sequence.length == 2


def test_sequence_length_rejects_out_of_range():
    with _afg([]) as inst:
        with pytest.raises(ValueError):
            inst.sequence.length = 257


def test_sequence_new():
    with _afg([("sequence:new", None)]) as inst:
        inst.sequence.new()


def test_sequence_run_control():
    with _afg(
        [
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
    with _afg(
        [
            ("seqcontrol:source1:scale 50", None),
            ("seqcontrol:source2:offset?", "0.1"),
        ],
    ) as inst:
        inst.sequence.set_source_scale(50, channel=1)
        assert inst.sequence.source_offset(channel=2) == 0.1


def test_sequence_element_properties():
    with _afg(
        [
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
    with _afg([]) as inst:
        with pytest.raises(ValueError):
            inst.sequence.element[1].goto_index = 0
        with pytest.raises(ValueError):
            inst.sequence.element[1].loop_count = 2_000_000


# --- Memory sub-instrument tests ---

def test_memory_types():
    assert issubclass(AFG31000Memory, SubInstrument)


def test_memory_is_wired():
    with _afg([]) as inst:
        assert isinstance(inst.memory, AFG31000Memory)


def test_memory_usb_delete_matches_manual_example():
    # MMEMORY:DELETE "U:/TEK001.TFWX"  <->  instrument.memory.usb_delete = 'TEK001.TFWX'
    with _afg(
        [('mmemory:delete "U:/TEK001.TFWX"', None)],
    ) as inst:
        inst.memory.usb_delete = "TEK001.TFWX"


def test_memory_internal_delete_keeps_relative_subpath():
    with _afg(
        [('mmemory:delete "M:/sub/TEK001.TFWX"', None)],
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
    with _afg(
        [
            ('mmemory:open:sequence "U:/AFGseq.seq"', None),
            ('mmemory:open:sequence "M:/AFGseq.seq"', None),
            ('mmemory:open:sequence "P:/AFGseq.seq"', None),
        ],
    ) as inst:
        inst.memory.usb_open_sequence = "AFGseq.seq"
        inst.memory.memory_open_sequence = "AFGseq.seq"
        inst.memory.read_only_memory_open_sequence = "AFGseq.seq"


def test_memory_make_directory():
    with _afg(
        [('mmemory:mdirectory "M:/sample"', None)],
    ) as inst:
        inst.memory.memory_make_directory = "sample"


def test_memory_current_directory_query_strips_quotes():
    with _afg(
        [("mmemory:cdirectory?", '"U:/AFG/WORK0"')],
    ) as inst:
        assert inst.memory.current_directory == "U:/AFG/WORK0"


def test_memory_change_directory():
    with _afg(
        [('mmemory:cdirectory "U:/AFG/WORK0"', None)],
    ) as inst:
        inst.memory.usb_change_directory = "AFG/WORK0"


def test_memory_load_trace_from_predefined_drive():
    with _afg(
        [('mmemory:load:trace ememory2,"P:/Sine.tfwx"', None)],
    ) as inst:
        inst.memory.read_only_memory_load_trace("Sine.tfwx", edit_memory=2)


def test_memory_store_state_is_usb_and_internal_only():
    assert hasattr(AFG31000Memory, "usb_store_state")
    assert hasattr(AFG31000Memory, "memory_store_state")
    assert not hasattr(AFG31000Memory, "read_only_memory_store_state")
    with _afg(
        [('mmemory:store:state 1,"M:/test1.tfs"', None)],
    ) as inst:
        inst.memory.memory_store_state(1, "test1.tfs")


def test_memory_lock_round_trip():
    with _afg(
        [
            ('mmemory:lock:state "M:/setup1.tfs",1', None),
            ('mmemory:lock:state? "M:/setup1.tfs"', "1"),
        ],
    ) as inst:
        inst.memory.memory_set_lock("setup1.tfs", True)
        assert inst.memory.memory_lock_state("setup1.tfs") is True


def test_setup_memory_save_and_recall():
    with _afg(
        [("*SAV 2", None), ("*RCL 2", None)],
    ) as inst:
        inst.memory.save(2)
        inst.memory.recall(2)


def test_setup_memory_valid_query():
    with _afg(
        [("memory:state:valid? 0", "1")],
    ) as inst:
        assert inst.memory.setup_valid(0) is True


def test_setup_memory_save_rejects_out_of_range():
    with _afg([]) as inst:
        with pytest.raises(ValueError):
            inst.memory.save(5)


def test_setup_recall_last_auto_round_trip():
    with _afg(
        [
            ("memory:state:recall:auto 1", None),
            ("memory:state:recall:auto?", "1"),
        ],
    ) as inst:
        inst.memory.recall_last_auto = True
        assert inst.memory.recall_last_auto is True


# --- Per-model spec resolution ---

def test_model_table_has_all_ten_entries():
    assert len(AFG31000_MODELS) == 10
    assert set(AFG31000_MODELS) == {
        "AFG31021", "AFG31022", "AFG31051", "AFG31052", "AFG31101",
        "AFG31102", "AFG31151", "AFG31152", "AFG31251", "AFG31252",
    }
    assert all(isinstance(spec, AFG31000Specs) for spec in AFG31000_MODELS.values())


def test_50mhz_models_seq_rate_below_arb_rate():
    # The 500 MS/s sequence ceiling is the bug-relevant trap: it is not equal to
    # the 1 GS/s arbitrary sample rate on the 50 MHz models.
    for model in ("AFG31051", "AFG31052"):
        spec = AFG31000_MODELS[model]
        assert spec.seq_sample_rate == 500e6
        assert spec.arb_sample_rate == 1e9


def test_two_channel_model_via_idn_query():
    # model=None triggers the *IDN? query, which must be the first exchange.
    with expected_protocol(
        AFG31000,
        [("*IDN?", "TEKTRONIX,AFG31052,C013513,SCPI:99.0 FV:1.6.1")],
        model=None,
    ) as inst:
        assert hasattr(inst, "ch1")
        assert hasattr(inst, "ch2")
        assert inst.num_channels == 2
        assert inst.specs.seq_sample_rate == 500e6
        assert inst.scpi_id.model_num == "AFG31052"


def test_single_channel_model_via_idn_query():
    with expected_protocol(
        AFG31000,
        [("*IDN?", "TEKTRONIX,AFG31101,C010001,SCPI:99.0 FV:1.6.1")],
        model=None,
    ) as inst:
        assert hasattr(inst, "ch1")
        assert not hasattr(inst, "ch2")
        assert inst.num_channels == 1
        assert inst.specs.seq_sample_rate == 1e9


def test_model_kwarg_skips_idn_query():
    # Supplying model= must not emit *IDN? (empty comm_pairs proves it).
    with expected_protocol(AFG31000, [], model="AFG31052") as inst:
        assert inst.scpi_id is None
        assert inst.num_channels == 2
        assert inst.specs.model_num == "AFG31052"


def test_unknown_model_is_non_fatal():
    # An unrecognised model must not crash construction: specs is None and the
    # instrument falls back to the class-default channel count, still usable.
    with expected_protocol(
        AFG31000,
        [("*IDN?", "TEKTRONIX,AFG39999,X,Y")],
        model=None,
    ) as inst:
        assert inst.specs is None
        assert inst.num_channels == AFG31000.NUM_CHANNELS
        assert hasattr(inst, "ch1")


def test_unknown_model_logs_warning(caplog):
    import logging
    with caplog.at_level(logging.WARNING):
        with expected_protocol(
            AFG31000,
            [("*IDN?", "TEKTRONIX,AFG39999,X,Y")],
            model=None,
        ):
            pass
    assert any("Unknown AFG31000 model" in record.message for record in caplog.records)


# --- Sequence sample-rate validation (B4) ---

def test_set_sample_rate_in_range_writes():
    with expected_protocol(
        AFG31000,
        [("seqcontrol:srate 5.000000e+08", None)],
        model="AFG31052",
    ) as inst:
        inst.sequence.set_sample_rate(500e6)


def test_set_sample_rate_overrange_raises():
    with expected_protocol(AFG31000, [], model="AFG31052") as inst:
        with pytest.raises(ValueError):
            inst.sequence.set_sample_rate(600e6)
