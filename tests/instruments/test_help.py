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

"""Tests for the instrument help system's introspection, curation and rendering."""

import importlib
import inspect
import pkgutil
from enum import Enum

import pytest

from pymeasure.adapters import ProtocolAdapter
from pymeasure.instruments import Channel, HelpMixin, Instrument
from pymeasure.instruments.common_base import CommonBase, DynamicProperty
from pymeasure.instruments.help import (
    clear_cache,
    describe,
    describe_tree,
    is_pymeasure_property,
    property_info,
    render_limits,
    search,
    validator_name,
    walk,
)
from pymeasure.instruments.help import render
from pymeasure.instruments.help.document import PLUMBING_MEMBERS
from pymeasure.instruments.validators import (
    joined_validators,
    strict_discrete_set,
    strict_range,
    truncated_range,
)


class Shape(Enum):
    """A values Enum, of the kind a driver may use instead of a dict."""

    SQUARE = "SQU"
    PULSE = "PULS"


class DemoChannel(HelpMixin, Channel):
    """A demo channel."""

    _help_groups = (("Vertical", ("scale", "offset")),)

    coupling = Channel.control(
        "CH{ch}:COUP?", "CH{ch}:COUP %s",
        """Control the input coupling.""",
        validator=strict_discrete_set, values=["AC", "DC", "GND"],
    )
    scale = Channel.control(
        "CH{ch}:SCA?", "CH{ch}:SCA %g",
        """Control the vertical scale in V/div.

        The second paragraph is the detail body.
        """,
        validator=strict_range, values=[1e-3, 10], check_set_errors=True,
    )
    offset = Channel.control(
        "CH{ch}:OFFS?", "CH{ch}:OFFS %g", """Control the vertical offset in volts.""",
        validator=truncated_range, values=[-5, 5],
    )
    state = Channel.control(
        "CH{ch}:STATE?", "CH{ch}:STATE %d",
        """Control whether the channel is displayed.""",
        validator=strict_discrete_set, values={True: 1, False: 0}, map_values=True,
    )
    clipping = Channel.measurement(
        "CH{ch}:CLIP?", """Get whether the input clips.""", cast=int,
    )


class DemoTrigger(HelpMixin, Channel):
    """The demo trigger subsystem."""

    _help_important = ("level",)
    _help_hidden = ("raw_word",)
    _help_exclude = ("legacy_knob",)

    level = Channel.control(
        "TRIG:LEV?", "TRIG:LEV %g", """Control the trigger level in volts.""",
        validator=joined_validators(strict_discrete_set, strict_range),
        values=[["MIN", "MAX"], [-5, 5]], dynamic=True,
    )
    shape = Channel.control(
        "TRIG:SHAP?", "TRIG:SHAP %s", """Control the trigger shape.""",
        validator=strict_discrete_set, values=Shape,
    )
    slots = Channel.control(
        "TRIG:SLOT?", "TRIG:SLOT %d", """Control the trigger slot.""",
        validator=strict_discrete_set, values=range(1, 9),
    )
    holdoff = Channel.setting("TRIG:HOLD %g", """Set the trigger holdoff in seconds.""")
    raw_word = Channel.measurement(
        "TRIG:RAW?", """Get the raw trigger word.""",
        separator=";", maxsplit=2, cast=str, check_get_errors=True,
    )
    legacy_knob = Channel.control("TRIG:OLD?", "TRIG:OLD %g", """Control a legacy knob.""")


class DemoScope(HelpMixin, Instrument):
    """A demo oscilloscope."""

    _help_root = "scope"
    _help_important = ("acquisition_state",)
    _help_hidden = ("debug_word",)
    _help_groups = (("Acquisition", ("acquisition_state", "record_length")),)

    acquisition_state = Instrument.control(
        "ACQ:STATE?", "ACQ:STATE %d", """Control the acquisition state.""",
        validator=strict_discrete_set, values={"run": 1, "stop": 0}, map_values=True,
    )
    record_length = Instrument.control(
        "HOR:RECO?", "HOR:RECO %d", """Control the record length in points.""",
        validator=strict_discrete_set, values=[1000, 10000, 100000], cast=int,
    )
    debug_word = Instrument.measurement("DEBUG:WORD?", """Get the debug word.""")

    @property
    def hand_written(self):
        """A plain Python property, not built by control."""
        return 42

    def autoset(self, timeout: float = 5.0) -> None:
        """Run autoset and wait for it to finish."""

    def __init__(self, adapter, name="Demo Scope", **kwargs):
        super().__init__(adapter, name, includeSCPI=False, **kwargs)
        self.channels = tuple(DemoChannel(self, index + 1) for index in range(4))
        for index, channel in enumerate(self.channels, start=1):
            setattr(self, "ch_{}".format(index), channel)
        self.trigger = DemoTrigger(self, 1)


class DynamicSubScope(DemoScope):
    """A subclass that narrows a dynamic property at class level."""

    level_values = [["MIN"], [-1, 1]]


@pytest.fixture
def scope():
    """A demo scope on a protocol adapter with no expected communication."""
    clear_cache()
    return DemoScope(ProtocolAdapter())


def _prop(cls, name):
    """Return the raw descriptor for ``name``, without invoking it."""
    for klass in cls.__mro__:
        if name in vars(klass):
            return vars(klass)[name]
    raise AssertionError("{} has no attribute {}".format(cls, name))


# ---------------------------------------------------------------- identification

def test_recognises_control_measurement_and_setting():
    assert is_pymeasure_property(_prop(DemoChannel, "coupling"))
    assert is_pymeasure_property(_prop(DemoChannel, "clipping"))
    assert is_pymeasure_property(_prop(DemoTrigger, "holdoff"))


def test_ignores_plain_properties_and_methods():
    assert not is_pymeasure_property(_prop(DemoScope, "hand_written"))
    assert not is_pymeasure_property(_prop(DemoScope, "autoset"))
    assert not is_pymeasure_property(None)


def test_control_signature_contract():
    """Guard the introspection contract against an upstream refactor of ``control``.

    Every field of a description is read out of these parameter names and closure
    variables. If a merge changes them, this fails loudly instead of the help
    system silently emptying out.
    """
    prop = CommonBase.control("A?", "A %s", "doc")
    assert prop.fget.__qualname__ == "CommonBase.control.<locals>.fget"
    assert set(inspect.signature(prop.fget).parameters) == (
        {"self"} | set(CommonBase._fget_params_list))
    assert set(inspect.signature(prop.fset).parameters) == (
        {"self", "value"} | set(CommonBase._fset_params_list))
    assert set(prop.fget.__code__.co_freevars) == {
        "cast", "maxsplit", "preprocess_reply", "separator", "values_kwargs"}


# ------------------------------------------------------------------ access mode

def test_measurement_has_a_setter_but_reads_only():
    """Access mode comes from the commands, never from a missing accessor."""
    prop = _prop(DemoChannel, "clipping")
    assert prop.fset is not None
    assert property_info("clipping", prop).access == "read"


def test_setting_writes_only():
    assert property_info("holdoff", _prop(DemoTrigger, "holdoff")).access == "write"


def test_control_reads_and_writes():
    assert property_info("coupling", _prop(DemoChannel, "coupling")).access == "read-write"


# --------------------------------------------------------------------- commands

def test_templates_are_reported_unresolved_without_an_instance():
    info = property_info("coupling", _prop(DemoChannel, "coupling"))
    assert info.get_command == "CH{ch}:COUP?"
    assert info.resolved_get_command is None


def test_templates_resolve_against_a_bound_channel(scope):
    info = property_info("coupling", _prop(DemoChannel, "coupling"), scope.ch_2)
    assert info.get_command == "CH{ch}:COUP?"
    assert info.resolved_get_command == "CH2:COUP?"
    assert info.resolved_set_command == "CH2:COUP %s"


def test_untemplated_commands_have_no_resolved_form(scope):
    info = property_info("level", _prop(DemoTrigger, "level"), scope.trigger)
    assert info.get_command == "TRIG:LEV?"
    assert info.resolved_get_command is None


def test_unresolvable_template_degrades(scope):
    """``insert_id`` raises on an unknown placeholder; help must not."""
    prop = Channel.control("X:{nope}?", "X %s", """Control a bad template.""")
    info = property_info("bad", prop, scope.ch_1)
    assert info.get_command == "X:{nope}?"
    assert info.resolved_get_command is None


# ----------------------------------------------------------------------- limits

@pytest.mark.parametrize("cls, name, expected", [
    (DemoChannel, "scale", "[0.001, 10]"),
    (DemoChannel, "offset", "[-5, 5]"),
    (DemoChannel, "coupling", "{AC, DC, GND}"),
    (DemoChannel, "state", "{True->1, False->0}"),
    (DemoTrigger, "shape", "{SQUARE=Shape.SQUARE}"),
    (DemoTrigger, "slots", "[1, 8] step 1"),
    (DemoTrigger, "level", "{MIN, MAX} or [-5, 5]"),
    (DemoTrigger, "holdoff", ""),
])
def test_limits_render_from_the_validator_and_values(cls, name, expected):
    info = property_info(name, _prop(cls, name))
    if name == "shape":
        # Enum members render as NAME=value; assert the shape rather than the repr.
        assert info.limits.startswith("{SQUARE=") and "PULSE=" in info.limits
    else:
        assert info.limits == expected


def test_same_values_render_differently_per_validator():
    """``[0, 10]`` is an interval for a range validator and a pair of choices otherwise."""
    assert render_limits(strict_range, [0, 10]) == "[0, 10]"
    assert render_limits(strict_discrete_set, [0, 10]) == "{0, 10}"


def test_validator_names():
    assert validator_name(strict_range) == "strict_range"
    assert validator_name(joined_validators(strict_discrete_set, strict_range)) == (
        "joined(strict_discrete_set, strict_range)")
    default = inspect.signature(CommonBase.control).parameters["validator"].default
    assert validator_name(default) == ""


def test_limits_never_raise_on_odd_values():
    class Awkward:
        def __bool__(self):
            raise RuntimeError("no truth value here")

    assert render_limits(strict_range, Awkward()) == ""


# --------------------------------------------------------------- other metadata

def test_cast_separator_maxsplit_and_error_checks():
    info = property_info("raw_word", _prop(DemoTrigger, "raw_word"))
    assert info.cast == "str"
    assert info.separator == ";"
    assert info.maxsplit == 2
    assert info.check_get_errors is True
    assert info.check_set_errors is False


def test_check_set_errors_is_reported():
    assert property_info("scale", _prop(DemoChannel, "scale")).check_set_errors is True


def test_map_values_is_three_state():
    """``measurement`` leaves ``map_values`` at ``None``, not ``False``."""
    assert property_info("clipping", _prop(DemoChannel, "clipping")).map_values is None
    assert property_info("state", _prop(DemoChannel, "state")).map_values is True
    assert property_info("coupling", _prop(DemoChannel, "coupling")).map_values is False


# ---------------------------------------------------------------------- dynamic

def test_dynamic_property_is_flagged_and_docstring_cleaned():
    info = property_info("level", _prop(DemoTrigger, "level"))
    assert isinstance(_prop(DemoTrigger, "level"), DynamicProperty)
    assert info.dynamic is True
    assert "(dynamic)" not in info.doc
    assert info.doc == "Control the trigger level in volts."


def test_dynamic_class_default_has_no_overrides(scope):
    info = property_info("level", _prop(DemoTrigger, "level"), scope.trigger)
    assert info.overrides == {}


def test_dynamic_instance_override_is_reported(scope):
    scope.trigger.level_values = [["MIN"], [-1, 1]]
    info = property_info("level", _prop(DemoTrigger, "level"), scope.trigger)
    assert info.overrides["values"] == [["MIN"], [-1, 1]]


def test_dynamic_subclass_override_is_reported():
    scope = DynamicSubScope(ProtocolAdapter())
    scope.trigger.level_values = [["MIN"], [-2, 2]]
    info = property_info("level", _prop(DemoTrigger, "level"), scope.trigger)
    assert info.overrides["values"] == [["MIN"], [-2, 2]]


# ------------------------------------------------------------------- degradation

def test_hand_written_property_carries_no_metadata(scope):
    entry = describe(scope).find("hand_written")
    assert entry is not None
    assert entry.info is None
    assert entry.summary == "A plain Python property, not built by control."


def test_broken_property_degrades_rather_than_raising():
    broken = property(lambda self: None)
    info = property_info("broken", broken)
    assert info.name == "broken"
    assert info.access == "none"


def test_describe_never_raises_on_a_hostile_class():
    class Hostile:
        """A class whose members explode when touched."""

        _help_important = object()          # not iterable as names
        _help_groups = 12                   # not a group definition

    document = describe(Hostile)
    assert document.title == "Hostile"


# ------------------------------------------------------------------- no hardware

def _forbid_io(monkeypatch, instrument):
    """Make any adapter traffic an immediate test failure."""
    def boom(*args, **kwargs):
        raise AssertionError("help performed instrument I/O")

    for name in ("_write", "_read", "_write_bytes", "_read_bytes"):
        monkeypatch.setattr(instrument.adapter, name, boom)


def test_help_performs_no_io(monkeypatch, scope, capsys):
    """Nothing in the help path may touch the instrument.

    The adapter is patched rather than relying on an empty comm-pair list,
    because a driver may swallow its own communication errors during ``__init__``
    and mask the assertion.
    """
    _forbid_io(monkeypatch, scope)
    scope.help()
    scope.help(verbose=True, hidden=True)
    scope.help("coupling")
    scope.help("ch_1")
    scope.help_search("COUP")
    scope.ch_1.help(verbose=True)
    assert capsys.readouterr().out


def test_help_survives_an_unrenderable_document(monkeypatch, scope, capsys):
    monkeypatch.setattr(render, "to_text", lambda *a, **k: 1 / 0)
    scope.help()
    assert "Help is unavailable" in capsys.readouterr().out


# --------------------------------------------------------------------- curation

def test_important_hidden_and_excluded(scope):
    document = describe(scope.trigger)
    headings = [section.heading for section in document.sections]
    assert "Key properties" in headings
    assert document.find("level").visibility == "important"
    assert document.find("raw_word").visibility == "hidden"
    assert document.find("legacy_knob") is None


def test_help_groups_split_the_property_list(scope):
    headings = [section.heading for section in describe(scope.ch_1).sections]
    assert "Vertical" in headings
    assert "Other properties" in headings


def test_ungrouped_properties_are_never_lost(scope):
    """A property missing from ``_help_groups`` lands in the catch-all section."""
    names = {entry.name for entry in describe(scope.ch_1).iter_entries()}
    assert {"scale", "offset", "coupling", "state", "clipping"} <= names


def test_plumbing_is_excluded_but_reset_survives(scope):
    names = {entry.name for entry in describe(scope).iter_entries()}
    assert not (names & PLUMBING_MEMBERS)
    assert "reset" in names and "shutdown" in names


def test_important_overrides_the_plumbing_filter():
    class Chatty(DemoScope):
        """A driver that documents its own write path."""

        _help_important = ("write",)

    assert describe(Chatty).find("write") is not None


def test_class_docstring_is_not_inherited():
    """A class with no docstring of its own must not borrow a base's."""
    class Undocumented(DemoScope):
        pass

    assert describe(Undocumented).description == ""


# ----------------------------------------------------------------------- tree

def test_children_are_discovered_without_touching_the_class(scope):
    refs = walk(scope, "scope")
    paths = {ref.path for ref in refs}
    assert "scope.ch_1" in paths
    assert "scope.trigger" in paths


def test_identity_dedupe_prefers_the_attribute_path(scope):
    assert scope.ch_1 is scope.channels[0]
    ref = next(r for r in walk(scope, "scope") if r.obj is scope.ch_1)
    assert ref.path == "scope.ch_1"
    assert "scope.channels[0]" in ref.aliases


def test_parent_back_reference_is_not_followed(scope):
    assert all(ref.obj is not scope for ref in walk(scope, "scope"))


def test_groups_collapse_instances_of_one_class(scope):
    groups = {group.label: group for group in describe_tree(scope).groups}
    assert set(groups) == {"DemoChannel", "DemoTrigger"}
    assert groups["DemoChannel"].paths == (
        "scope.ch_1", "scope.ch_2", "scope.ch_3", "scope.ch_4")
    assert groups["DemoChannel"].kind == "Channels"


def test_group_entries_carry_the_representative_path(scope):
    group = next(g for g in describe_tree(scope).groups if g.label == "DemoChannel")
    assert group.document.find("coupling").path == "scope.ch_1.coupling"


def test_max_depth_is_respected(scope):
    assert walk(scope, "scope", max_depth=0) == []


# ---------------------------------------------------------------------- search

def test_search_matches_a_command_template(scope):
    hits = search(scope, "CH{ch}:COUP")
    assert [hit.path for hit in hits] == ["scope.ch_1.coupling"]


def test_search_reports_one_hit_per_class_with_multiplicity(scope):
    hit = next(hit for hit in search(scope, "coupling"))
    assert hit.multiplicity == 4


def test_search_is_empty_for_an_empty_query(scope):
    assert search(scope, "   ") == []


# --------------------------------------------------------------------- render

def test_markdown_overview_has_a_table_and_group_headings(scope):
    text = render.to_markdown(describe_tree(scope))
    assert "| Name | Access | Description |" in text
    assert "| `acquisition_state` | RW |" in text
    assert "DemoChannel (ch_1, ch_2, ch_3, ch_4)" in text


def test_verbose_shows_commands_limits_and_resolution(scope):
    text = render.to_text(describe_tree(scope), verbose=True)
    assert "CH{ch}:COUP?  ->  CH1:COUP?" in text
    assert "{AC, DC, GND}  (strict_discrete_set)" in text


def test_compact_omits_what_verbose_adds(scope):
    text = render.to_text(describe_tree(scope))
    assert "CH{ch}:COUP?" not in text
    assert "verbose=True" in text


def test_hidden_entries_appear_only_on_request(scope):
    assert "debug_word" not in render.to_text(describe_tree(scope))
    assert "debug_word" in render.to_text(describe_tree(scope), hidden=True)


def test_long_signatures_are_abbreviated_in_the_overview(scope):
    text = render.to_text(describe_tree(scope))
    assert "autoset(...)" in text
    assert "timeout: float" not in text


def test_ambiguous_topic_lists_the_candidates(scope, capsys):
    scope.help("label_that_does_not_exist")
    assert "No help topic named" in capsys.readouterr().out


# ----------------------------------------------------------------------- cache

def test_cache_is_per_class_and_clearable(scope):
    first = describe(scope.ch_1)
    second = describe(scope.ch_1)
    assert first is not second
    assert first.find("scale") is not second.find("scale")
    clear_cache(DemoChannel)
    assert describe(scope.ch_1).find("scale") is not None


# ------------------------------------------------------------- the whole library

def _all_driver_classes():
    """Import every driver module and collect its instrument and channel classes."""
    from pymeasure import instruments as package

    found = set()
    # Some drivers need vendor libraries that are not installed everywhere; an
    # onerror handler makes walk_packages skip them instead of propagating.
    walker = pkgutil.walk_packages(
        package.__path__, package.__name__ + ".", onerror=lambda name: None)
    for info in walker:
        try:
            module = importlib.import_module(info.name)
        except Exception:
            continue  # optional vendor dependencies are not installed everywhere
        for obj in vars(module).values():
            if isinstance(obj, type) and issubclass(obj, (Instrument, Channel)):
                found.add(obj)
    return sorted(found, key=lambda cls: (cls.__module__, cls.__name__))


def test_describe_never_raises_for_any_driver_in_the_library():
    """Class-level description must succeed for every driver, mixed in or not."""
    failures = []
    for cls in _all_driver_classes():
        try:
            document = describe(cls)
        except Exception as error:  # pragma: no cover - the point of the test
            failures.append("{}.{}: {!r}".format(cls.__module__, cls.__name__, error))
        else:
            if not document.title:
                failures.append("{}.{}: empty title".format(cls.__module__, cls.__name__))
    assert not failures, "describe() failed for:\n" + "\n".join(failures)
