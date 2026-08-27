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

"""Discovery and aggregation of an instrument's child objects.

An oscilloscope reaches a few hundred properties through its channels and
subsystems, but only a few dozen *distinct* ones: eight channels are eight
instances of one class. Aggregation therefore deduplicates twice — first by
object identity, because ``scope.ch_1`` and ``scope.channels[0]`` are the same
object, then by class for display, so one channel class is documented once and
labelled with the instances it covers.

Discovery reads ``vars(instance)`` and never calls ``getattr`` on the class,
because that would fire property getters and talk to the instrument.

See help.md for detailed documentation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Iterator

from ..channel import Channel
from ..common_base import CommonBase
from .document import curation, describe, searchable_text
from .model import (
    GROUP_CHANNELS,
    GROUP_SUBSYSTEMS,
    VISIBILITY_INTERNAL,
    ChildGroup,
    HelpDocument,
    SearchHit,
)

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

#: Attribute names never followed. ``parent`` is the back-reference every
#: channel holds; the identity guard would catch it, but not following it at all
#: keeps the traversal honest for a child built with a foreign parent.
SKIP_NAMES = frozenset({"parent"})

#: Default recursion limit. Real instrument trees are two levels deep; this is
#: insurance against a pathological driver, and it logs when it bites.
MAX_DEPTH = 4

# Preference when one object is reachable by several paths: a plain attribute
# beats a dictionary key, which beats a sequence index.
_RANK_ATTRIBUTE = 0
_RANK_MAPPING = 1
_RANK_SEQUENCE = 2


@dataclass
class ChildRef:
    """One child object, at its canonical access path.

    Attributes:
        path: The preferred access path, e.g. ``"mso58.ch_1"``.
        obj: The child itself.
        aliases: Other paths that reach the same object.
        depth: Distance from the root, counting from one.
    """

    path: str
    obj: Any
    aliases: tuple[str, ...] = ()
    depth: int = 1


def default_root(obj: Any) -> str:
    """Return the label a described object's paths hang off.

    The class name lowercased, not :attr:`Instrument.name`, which is prose
    ("Tektronix MSO58 Oscilloscope") rather than something a user can type.
    """
    return str(curation(type(obj), "_help_root", type(obj).__name__.lower()))


def _names(value: Any) -> tuple[str, ...]:
    """Normalise a curation attribute into a tuple of names."""
    if isinstance(value, str):
        return (value,)
    try:
        return tuple(str(item) for item in value)
    except TypeError:
        return ()


def _all_children(value: Any) -> bool:
    """Return whether every member of a collection is a describable child."""
    return bool(value) and all(isinstance(item, CommonBase) for item in value)


def iter_candidates(obj: Any, root: str) -> Iterator[tuple[int, str, Any]]:
    """Yield ``(rank, path, child)`` for every child reachable one level down.

    Reads only ``vars(obj)``, so no property getter runs. Both routes pymeasure
    drivers use are covered: children bound directly as attributes (whether by
    :meth:`CommonBase.add_child` or by hand in ``__init__``), and collections of
    them held in a dict, list or tuple.

    Args:
        obj: The parent instrument, channel or subsystem.
        root: Access path of ``obj``, used to build child paths.

    Yields:
        A rank used to pick the canonical path, the path, and the child.
    """
    cls = type(obj)
    prefix = (root + ".") if root else ""
    contents = vars(obj)

    explicit = curation(cls, "_help_children", None)
    if explicit is not None:
        for name in _names(explicit):
            child = contents.get(name)
            if isinstance(child, CommonBase):
                yield _RANK_ATTRIBUTE, prefix + name, child
        return

    exclude = set(_names(curation(cls, "_help_child_exclude", ())))
    for name, value in contents.items():
        if name.startswith("_") or name in SKIP_NAMES or name in exclude:
            continue
        if isinstance(value, CommonBase):
            yield _RANK_ATTRIBUTE, prefix + name, value
        elif isinstance(value, dict) and _all_children(value.values()):
            for key, child in value.items():
                yield _RANK_MAPPING, "{}{}[{!r}]".format(prefix, name, key), child
        elif isinstance(value, (list, tuple)) and _all_children(value):
            for index, child in enumerate(value):
                yield _RANK_SEQUENCE, "{}{}[{}]".format(prefix, name, index), child


def _canonical(candidates: list[tuple[int, str, Any]],
               seen: set[int]) -> list[ChildRef]:
    """Reduce one level's candidates to one reference per distinct object.

    An object reachable twice (``scope.ch_1`` and ``scope.channels[0]``) keeps
    the better-ranked path and records the other as an alias.
    """
    best: dict[int, tuple[tuple, str, Any]] = {}
    order: list[int] = []
    for rank, path, child in candidates:
        key = id(child)
        if key in seen:
            continue
        ranked = (rank, len(path), path)
        current = best.get(key)
        if current is None:
            best[key] = (ranked, path, child)
            order.append(key)
        elif ranked < current[0]:
            best[key] = (ranked, path, child)

    references = []
    for key in order:
        _ranked, path, child = best[key]
        aliases = sorted(
            other for _r, other, candidate in candidates
            if id(candidate) == key and other != path
        )
        references.append(ChildRef(path=path, obj=child, aliases=tuple(aliases)))
    return references


def walk(obj: Any, root: str = "", max_depth: int = MAX_DEPTH) -> list[ChildRef]:
    """Return every describable child under ``obj``, depth first.

    Args:
        obj: The root instrument.
        root: Access path of ``obj``.
        max_depth: Maximum recursion depth, counting the first level as one.

    Returns:
        One :class:`ChildRef` per distinct child object, in discovery order.
    """
    refs: list[ChildRef] = []
    _walk(obj, root, 1, max_depth, {id(obj)}, refs)
    return refs


def _walk(obj: Any, root: str, depth: int, max_depth: int,
          seen: set[int], refs: list[ChildRef]) -> None:
    """Recursive worker for :func:`walk`, guarding cycles via ``seen``."""
    if depth > max_depth:
        log.debug("help: stopped at depth %d below %r", max_depth, root)
        return
    try:
        candidates = list(iter_candidates(obj, root))
    except Exception:  # pragma: no cover - defensive
        log.debug("help: child discovery failed for %r", root, exc_info=True)
        return

    level = _canonical(candidates, seen)
    # Claim the whole level before recursing, so a grandchild cannot steal the
    # canonical path of a sibling that has not been visited yet.
    for ref in level:
        seen.add(id(ref.obj))
        ref.depth = depth
        refs.append(ref)
    for ref in level:
        _walk(ref.obj, ref.path, depth + 1, max_depth, seen, refs)


def group_by_class(refs: list[ChildRef]) -> list[ChildGroup]:
    """Collapse child references into one group per distinct class.

    Args:
        refs: Child references, in discovery order.

    Returns:
        One :class:`ChildGroup` per class, ordered by first discovery. Each
        group's document is built from the first instance, so its resolved
        commands are real ones.
    """
    buckets: dict[type, list[ChildRef]] = {}
    order: list[type] = []
    for ref in refs:
        cls = type(ref.obj)
        if cls not in buckets:
            buckets[cls] = []
            order.append(cls)
        buckets[cls].append(ref)

    groups = []
    for cls in order:
        members = buckets[cls]
        representative = members[0].obj
        groups.append(ChildGroup(
            child_class=cls,
            kind=GROUP_CHANNELS if isinstance(representative, Channel) else GROUP_SUBSYSTEMS,
            paths=tuple(ref.path for ref in members),
            representative=representative,
            document=describe(representative, members[0].path),
        ))
    return groups


def describe_tree(obj: Any, root: str | None = None,
                  max_depth: int = MAX_DEPTH) -> HelpDocument:
    """Describe ``obj`` together with every child class beneath it.

    Args:
        obj: The root instrument.
        root: Access path label; defaults to the lowercased class name.
        max_depth: Maximum recursion depth.

    Returns:
        The root's own :class:`HelpDocument` with its ``groups`` populated.
    """
    label = default_root(obj) if root is None else root
    document = describe(obj, label)
    try:
        document.groups = group_by_class(walk(obj, label, max_depth))
    except Exception:  # pragma: no cover - defensive
        log.debug("help: aggregation failed for %r", label, exc_info=True)
    return document


def search(obj: Any, query: str, root: str | None = None,
           max_depth: int = MAX_DEPTH) -> list[SearchHit]:
    """Search an instrument and its children for ``query``.

    Matching is case-insensitive across names, docstrings and both command
    templates. Results are reported once per class, at the representative
    instance's path, with the number of instances that share it.

    Args:
        obj: The root instrument.
        query: Substring to look for.
        root: Access path label; defaults to the lowercased class name.
        max_depth: Maximum recursion depth.

    Returns:
        Matching hits, root entries first, then one block per child class.
    """
    label = default_root(obj) if root is None else root
    needle = query.strip().lower()
    hits: list[SearchHit] = []
    if not needle:
        return hits

    _collect(describe(obj, label), needle, 1, hits)
    try:
        groups = group_by_class(walk(obj, label, max_depth))
    except Exception:  # pragma: no cover - defensive
        log.debug("help: search aggregation failed for %r", label, exc_info=True)
        return hits
    for group in groups:
        _collect(group.document, needle, len(group.paths), hits)
    return hits


def _collect(document: HelpDocument, needle: str, multiplicity: int,
             hits: list[SearchHit]) -> None:
    """Append every entry of ``document`` whose searchable text matches."""
    for entry in document.iter_entries():
        if entry.visibility == VISIBILITY_INTERNAL:
            continue
        if needle in searchable_text(entry):
            hits.append(SearchHit(
                path=entry.path or entry.name,
                entry=entry,
                source_title=document.title,
                multiplicity=multiplicity,
            ))
