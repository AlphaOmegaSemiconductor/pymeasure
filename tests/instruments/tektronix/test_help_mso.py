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

"""Help tests for the Tektronix MSO drivers.

These cover the shapes the MSO tree uses that stock pymeasure drivers do not:
children built by hand into tuples, a two-placeholder ``insert_id`` override,
and subsystem classes that are neither :class:`Channel` nor define ``insert_id``
at all.
"""

import pytest

from pymeasure.adapters import ProtocolAdapter
from pymeasure.instruments.help import HelpMixin, clear_cache, describe, describe_tree
from pymeasure.instruments.help import search, walk
from pymeasure.instruments.help.extract import iter_properties
from pymeasure.instruments.tektronix.mso.tektronix_common_base_channel import ScopeChannel
from pymeasure.instruments.tektronix.mso.tektronix_common_base_trigger import Trigger
from pymeasure.instruments.tektronix.mso58 import MSO58

#: Every child class the MSO58 tree exposes, from the Phase 0 census.
EXPECTED_GROUPS = {
    "ScopeChannel", "MathChannel", "MemoryChannel",
    "Acquisition", "Cursor", "Display", "FileSystem", "Horizontal", "Math",
    "Measurement", "Save", "Trigger", "WaveformTransfer",
}


@pytest.fixture
def scope():
    """An MSO58 on a protocol adapter, with the help cache cleared."""
    clear_cache()
    return MSO58(ProtocolAdapter())


def _forbid_io(monkeypatch, instrument):
    def boom(*args, **kwargs):
        raise AssertionError("help performed instrument I/O")

    for name in ("_write", "_read", "_write_bytes", "_read_bytes"):
        monkeypatch.setattr(instrument.adapter, name, boom)


# ------------------------------------------------------------------ opting in

def test_every_mso_class_opted_in(scope):
    assert isinstance(scope, HelpMixin)
    for group in describe_tree(scope).groups:
        assert issubclass(group.child_class, HelpMixin), group.label


def test_model_class_has_its_own_description(scope):
    """Regression: an f-string is not a docstring, so ``__doc__`` used to be None."""
    assert MSO58.__doc__ is not None
    assert describe(scope).description == "Represents the Tektronix MSO58 Oscilloscope."


def test_help_root_is_scope(scope):
    assert describe_tree(scope).path == "scope"


# --------------------------------------------------------------- tree discovery

def test_all_child_classes_are_grouped(scope):
    labels = {group.label for group in describe_tree(scope).groups}
    assert labels == EXPECTED_GROUPS


def test_channels_built_into_a_tuple_are_discovered(scope):
    """The MSO builds ``self.channels`` as a tuple, not the usual dict."""
    assert isinstance(scope.channels, tuple)
    group = next(g for g in describe_tree(scope).groups if g.label == "ScopeChannel")
    assert len(group.paths) == scope.analog_channels_count
    assert group.paths[0] == "scope.ch_1"


def test_attribute_alias_beats_the_tuple_index(scope):
    assert scope.ch_1 is scope.channels[0]
    ref = next(r for r in walk(scope, "scope") if r.obj is scope.ch_1)
    assert ref.path == "scope.ch_1"
    assert "scope.channels[0]" in ref.aliases


def test_subsystems_are_not_channels(scope):
    groups = {group.label: group for group in describe_tree(scope).groups}
    assert groups["ScopeChannel"].kind == "Channels"
    assert groups["Trigger"].kind == "Subsystems"
    assert groups["Horizontal"].kind == "Subsystems"


def test_the_census_is_stable(scope):
    """A regression check on how much of the instrument help actually covers."""
    groups = describe_tree(scope).groups
    distinct = sum(len(list(iter_properties(group.child_class))) for group in groups)
    distinct += len(list(iter_properties(MSO58)))
    assert distinct >= 250


# -------------------------------------------------------------------- commands

def test_two_placeholder_insert_id_resolves(scope):
    """``BaseScopeChannel`` substitutes both ``{ch}`` and ``{ch_type}``."""
    group = next(g for g in describe_tree(scope).groups if g.label == "ScopeChannel")
    info = group.document.find("coupling").info
    assert info.get_command == "{ch_type}{ch}:COUPling?"
    assert info.resolved_get_command == "CH1:COUPling?"


def test_subsystem_without_insert_id_leaves_commands_raw(scope):
    """``CommandGroupSubSystem`` has no ``insert_id``; help must not invent one."""
    assert not hasattr(Trigger, "insert_id")
    info = describe(scope.trigger, "scope.trigger").find("a_mode").info
    assert info.get_command.startswith("TRIGger:A:MODe")
    assert info.resolved_get_command is None


def test_channel_ids_differ_between_instances(scope):
    first = describe(scope.ch_1, "scope.ch_1").find("coupling").info
    eighth = describe(scope.ch_8, "scope.ch_8").find("coupling").info
    assert first.resolved_get_command == "CH1:COUPling?"
    assert eighth.resolved_get_command == "CH8:COUPling?"


# -------------------------------------------------------------------- curation

def test_scope_channel_groups_are_applied(scope):
    headings = [section.heading for section in describe(scope.ch_1).sections]
    assert "Vertical" in headings
    assert "Input" in headings
    assert "Label" in headings


def test_trigger_groups_split_a_long_property_list(scope):
    headings = [section.heading for section in describe(scope.trigger).sections]
    assert "A edge" in headings
    assert "B trigger" in headings


def test_no_property_is_dropped_by_grouping(scope):
    for cls in (ScopeChannel, Trigger):
        described = {entry.name for entry in describe(cls).iter_entries()}
        assert {name for name, _ in iter_properties(cls)} <= described


# ---------------------------------------------------------------------- search

def test_search_finds_a_scpi_fragment(scope):
    hits = search(scope, "HORizontal:SCAle")
    assert [hit.path for hit in hits] == ["scope.horizontal.scale"]


def test_search_collapses_the_eight_channels(scope):
    hit = next(hit for hit in search(scope, "COUPling") if "ch_1" in hit.path)
    assert hit.multiplicity == scope.analog_channels_count


# ------------------------------------------------------------------ no hardware

def test_help_performs_no_io(monkeypatch, scope, capsys):
    _forbid_io(monkeypatch, scope)
    scope.help()
    scope.help(verbose=True, hidden=True)
    scope.help("ch_1")
    scope.help("Trigger")
    scope.help("coupling")
    scope.help_search("bandwidth")
    scope.trigger.help(verbose=True)
    assert capsys.readouterr().out
