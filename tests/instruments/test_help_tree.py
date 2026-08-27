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

"""Aggregation tests against stock pymeasure drivers.

None of the drivers exercised here inherit :class:`HelpMixin`, which is the
point: the engine describes any class built with the property creators, so an
instrument from an unmodified pymeasure install is documented just as well as
one that opted in.
"""

import pytest

from pymeasure.adapters import ProtocolAdapter
from pymeasure.instruments.aimtti.aimttiPL import PL303QMDP
from pymeasure.instruments.help import clear_cache, describe, describe_tree, search, walk
from pymeasure.instruments.hp.hp11713a import HP11713A
from pymeasure.instruments.redpitaya.redpitaya_scpi import RedPitayaScpi


@pytest.fixture
def switch():
    """An HP11713A: children created by MultiChannelCreator into a dict."""
    clear_cache()
    return HP11713A(ProtocolAdapter())


@pytest.fixture
def redpitaya():
    """A RedPitayaScpi: six distinct child classes under one instrument."""
    clear_cache()
    return RedPitayaScpi(ProtocolAdapter())


def test_engine_works_without_the_mixin(switch):
    from pymeasure.instruments.help import HelpMixin

    assert not isinstance(switch, HelpMixin)
    assert describe(switch).title == "HP11713A"


def test_default_root_is_the_lowercased_class_name(switch):
    assert describe_tree(switch).path == "hp11713a"


def test_add_child_children_are_found(switch):
    paths = {ref.path for ref in walk(switch, "sw")}
    assert "sw.ch_0" in paths
    assert len(paths) == len(switch.channels)


def test_attribute_path_beats_the_collection_path(switch):
    """``sw.ch_0`` and ``sw.channels[0]`` are one object; the attribute wins."""
    assert switch.ch_0 is switch.channels[0]
    ref = next(r for r in walk(switch, "sw") if r.obj is switch.ch_0)
    assert ref.path == "sw.ch_0"
    assert "sw.channels[0]" in ref.aliases


def test_one_group_per_child_class(switch):
    groups = describe_tree(switch).groups
    assert len(groups) == 1
    assert groups[0].label == "SwitchDriverChannel"
    assert groups[0].kind == "Channels"
    assert len(groups[0].paths) == len(switch.channels)


def test_distinct_classes_stay_distinct(redpitaya):
    groups = describe_tree(redpitaya).groups
    labels = [group.label for group in groups]
    assert len(labels) == len(set(labels)) >= 4
    assert all(group.paths for group in groups)


def test_group_documents_are_bound_to_a_representative(redpitaya):
    for group in describe_tree(redpitaya).groups:
        assert isinstance(group.representative, group.child_class)
        assert group.representative is not None
        for entry in group.document.iter_entries():
            assert entry.path.startswith(group.paths[0] + ".")


def test_parent_back_reference_terminates_the_walk(switch):
    """Every channel holds ``parent``; the traversal must not loop through it."""
    refs = walk(switch, "sw")
    assert all(ref.obj is not switch for ref in refs)
    assert len(refs) == len({id(ref.obj) for ref in refs})


def test_search_reports_multiplicity(switch):
    hits = search(switch, "ch")
    assert hits
    assert all(hit.multiplicity in (1, len(switch.channels)) for hit in hits)


def test_search_finds_a_command_fragment(redpitaya):
    hits = search(redpitaya, "ANALOG:PIN")
    assert hits, "no property matched a command fragment"


def _forbid_io(monkeypatch, instrument):
    def boom(*args, **kwargs):
        raise AssertionError("help performed instrument I/O")

    for name in ("_write", "_read", "_write_bytes", "_read_bytes"):
        monkeypatch.setattr(instrument.adapter, name, boom)


@pytest.mark.parametrize("factory", [
    lambda: HP11713A(ProtocolAdapter()),
    lambda: RedPitayaScpi(ProtocolAdapter()),
    lambda: PL303QMDP(ProtocolAdapter()),
])
def test_aggregation_performs_no_io(monkeypatch, factory):
    instrument = factory()
    _forbid_io(monkeypatch, instrument)
    document = describe_tree(instrument)
    assert document.title
    assert search(instrument, "voltage") is not None
