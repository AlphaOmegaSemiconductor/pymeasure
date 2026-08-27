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

"""Assembly of a single class or instance into a :class:`HelpDocument`.

:mod:`extract` recovers raw metadata; this module applies the ``_help_*``
curation attributes on top of it, orders the result into sections, and caches
the class-level half. Curation only ever *selects and orders* — every piece of
descriptive text comes from a docstring.

The class-level description is cached because introspecting a 39-property
subsystem is not free and never changes. Anything that varies per instance —
resolved channel commands, dynamic overrides — is recomputed per call, and only
for the properties that can actually differ.

See help.md for detailed documentation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .extract import (
    introspect_members,
    narrative_entries,
    needs_instance_pass,
    property_info,
    summarize_docstring,
)
from .model import (
    KIND_METHOD,
    KIND_NARRATIVE,
    KIND_PROPERTY,
    VISIBILITY_HIDDEN,
    VISIBILITY_IMPORTANT,
    VISIBILITY_INTERNAL,
    VISIBILITY_NORMAL,
    HelpDocument,
    HelpEntry,
    HelpSection,
)

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

#: Members every driver inherits that describe the framework rather than the
#: instrument. Excluded by default so a driver's own API is what shows up; a
#: driver that genuinely wants one documented lists it in ``_help_important``.
#: Deliberately *not* computed from ``vars(CommonBase)`` and friends, which
#: would also swallow ``reset``, ``clear``, ``shutdown`` and ``check_errors``.
PLUMBING_MEMBERS = frozenset({
    # Property creators.
    "control", "measurement", "setting",
    # Communication plumbing.
    "ask", "read", "write", "read_bytes", "write_bytes", "values",
    "read_binary_values", "write_binary_values", "binary_values",
    "wait_for", "insert_id",
    # Channel management.
    "add_child", "remove_child", "get_channels", "get_channel_pairs",
    # Error hooks called by the property machinery itself.
    "check_get_errors", "check_set_errors",
    # The help system's own surface.
    "help", "help_search", "help_document",
})

SECTION_KEY_PROPERTIES = "Key properties"
SECTION_KEY_METHODS = "Key methods"
SECTION_PROPERTIES = "Properties"
SECTION_OTHER_PROPERTIES = "Other properties"
SECTION_METHODS = "Methods"
SECTION_ADVANCED = "Advanced"


@dataclass
class _ClassCache:
    """The instance-independent half of a class's description."""

    entries: list[HelpEntry] = field(default_factory=list)
    descriptors: dict[str, Any] = field(default_factory=dict)
    narrative: list[HelpEntry] = field(default_factory=list)


_CACHE: dict[type, _ClassCache] = {}


def clear_cache(cls: type | None = None) -> None:
    """Drop cached class descriptions.

    Args:
        cls: Clear only this class's entry; clear everything when ``None``.
    """
    if cls is None:
        _CACHE.clear()
    else:
        _CACHE.pop(cls, None)


def curation(cls: type, name: str, default: Any) -> Any:
    """Read a ``_help_*`` curation attribute off ``cls``.

    Reading through :func:`getattr` rather than requiring the mixin is what lets
    :func:`describe` work on any class, mixed in or not.

    Args:
        cls: The class to read from.
        name: The attribute name, e.g. ``"_help_important"``.
        default: Value to use when the attribute is absent or ``None``.

    Returns:
        The curated value, or ``default``.
    """
    value = getattr(cls, name, None)
    return default if value is None else value


def _names(value: Any) -> tuple[str, ...]:
    """Normalise a curation attribute into a tuple of names."""
    if isinstance(value, str):
        return (value,)
    try:
        return tuple(str(item) for item in value)
    except TypeError:
        return ()


def _class_cache(cls: type) -> _ClassCache:
    """Return the cached class-level entries for ``cls``, building them once."""
    cached = _CACHE.get(cls)
    if cached is not None:
        return cached

    important = set(_names(curation(cls, "_help_important", ())))
    exclude = frozenset(
        set(_names(curation(cls, "_help_exclude", ()))) | (PLUMBING_MEMBERS - important)
    )
    entries, descriptors = introspect_members(cls, exclude)
    narrative = narrative_entries(cls) if curation(cls, "_help_use_md", True) else []
    cached = _ClassCache(entries=entries, descriptors=descriptors, narrative=narrative)
    _CACHE[cls] = cached
    return cached


def _assign_visibility(entries: list[HelpEntry], cls: type) -> None:
    """Tag each entry with its visibility bucket.

    Precedence is exclude (already removed) over hidden over important over
    normal; any remaining underscore-prefixed member is internal.
    """
    important = set(_names(curation(cls, "_help_important", ())))
    hidden = set(_names(curation(cls, "_help_hidden", ())))
    for entry in entries:
        if entry.name in hidden:
            entry.visibility = VISIBILITY_HIDDEN
        elif entry.name in important:
            entry.visibility = VISIBILITY_IMPORTANT
        elif entry.name.startswith("_"):
            entry.visibility = VISIBILITY_INTERNAL
        else:
            entry.visibility = VISIBILITY_NORMAL


def _ordered(entries: list[HelpEntry], order: tuple[str, ...]) -> list[HelpEntry]:
    """Return ``entries`` sorted to follow the given name ``order``."""
    rank = {name: index for index, name in enumerate(order)}
    return sorted(entries, key=lambda entry: (rank.get(entry.name, len(rank)), entry.name))


def _grouped_property_sections(cls: type, normal: list[HelpEntry]) -> list[HelpSection]:
    """Split normal properties into the sections named by ``_help_groups``.

    ``_help_groups`` is ``((heading, (name, ...)), ...)``. Names it does not
    mention fall into a trailing catch-all, so adding a property to a driver
    never makes it silently disappear from help.
    """
    groups = curation(cls, "_help_groups", ())
    by_name = {entry.name: entry for entry in normal}
    if not groups:
        return [HelpSection(SECTION_PROPERTIES, sorted(normal, key=lambda e: e.name))]

    sections = []
    claimed = set()
    for heading, names in groups:
        chosen = [by_name[name] for name in _names(names) if name in by_name]
        claimed.update(entry.name for entry in chosen)
        if chosen:
            sections.append(HelpSection(str(heading), chosen))
    leftover = [entry for entry in normal if entry.name not in claimed]
    if leftover:
        sections.append(
            HelpSection(SECTION_OTHER_PROPERTIES, sorted(leftover, key=lambda e: e.name))
        )
    return sections


def _build_sections(cls: type, entries: list[HelpEntry],
                    narrative: list[HelpEntry]) -> list[HelpSection]:
    """Arrange tagged entries into ordered display sections."""
    important_order = _names(curation(cls, "_help_important", ()))
    hidden_order = _names(curation(cls, "_help_hidden", ()))

    def pick(visibility: str, kind: str | None = None) -> list[HelpEntry]:
        return [
            entry for entry in entries
            if entry.visibility == visibility and (kind is None or entry.kind == kind)
        ]

    sections = [
        HelpSection(SECTION_KEY_PROPERTIES,
                    _ordered(pick(VISIBILITY_IMPORTANT, KIND_PROPERTY), important_order)),
        HelpSection(SECTION_KEY_METHODS,
                    _ordered(pick(VISIBILITY_IMPORTANT, KIND_METHOD), important_order)),
    ]
    sections.extend(_grouped_property_sections(cls, pick(VISIBILITY_NORMAL, KIND_PROPERTY)))
    sections.append(
        HelpSection(SECTION_METHODS,
                    sorted(pick(VISIBILITY_NORMAL, KIND_METHOD), key=lambda e: e.name))
    )
    sections.append(HelpSection(SECTION_ADVANCED, _ordered(pick(VISIBILITY_HIDDEN), hidden_order)))
    for entry in narrative:
        sections.append(HelpSection(entry.name, [entry]))
    return [section for section in sections if section]


def _bind_entries(entries: list[HelpEntry], descriptors: dict[str, Any],
                  instance: Any) -> None:
    """Re-describe the properties whose metadata depends on the instance."""
    for entry in entries:
        if entry.kind != KIND_PROPERTY or entry.info is None:
            continue
        if not needs_instance_pass(entry.info):
            continue
        descriptor = descriptors.get(entry.name)
        if descriptor is None:
            continue
        entry.info = property_info(entry.name, descriptor, instance)


def describe(obj_or_cls: Any, root: str = "") -> HelpDocument:
    """Build the help document for one class or instance, without recursion.

    Args:
        obj_or_cls: An instrument or channel class, or an instance of one.
        root: Access path of the described object, used to build entry paths.

    Returns:
        A :class:`HelpDocument`. Never raises: on failure it returns a document
        with a title and no sections.
    """
    is_class = isinstance(obj_or_cls, type)
    cls = obj_or_cls if is_class else type(obj_or_cls)
    try:
        return _describe(cls, None if is_class else obj_or_cls, root)
    except Exception:
        log.debug("help: could not describe %r", cls, exc_info=True)
        return HelpDocument(title=getattr(cls, "__name__", "?"), path=root)


def _describe(cls: type, instance: Any, root: str) -> HelpDocument:
    """Body of :func:`describe`; see there for the contract."""
    cached = _class_cache(cls)
    entries = [entry.copy() for entry in cached.entries]
    narrative = [entry.copy() for entry in cached.narrative]

    if instance is not None:
        _bind_entries(entries, cached.descriptors, instance)
    _assign_visibility(entries, cls)

    prefix = (root + ".") if root else ""
    for entry in entries:
        entry.path = prefix + entry.name

    # A class docstring is read directly rather than through inspect.getdoc, which
    # would inherit a base class's text and describe the wrong instrument.
    summary, _ = summarize_docstring(cls.__doc__)
    return HelpDocument(
        title=str(curation(cls, "_help_title", cls.__name__)),
        description=summary,
        sections=_build_sections(cls, entries, narrative),
        path=root,
    )


def searchable_text(entry: HelpEntry) -> str:
    """Return the text a search query is matched against for one entry.

    Command templates are included: the question a driver user most often has is
    which property sends a particular SCPI string, and that is the one thing
    :func:`dir` cannot answer.
    """
    if entry.kind == KIND_NARRATIVE:
        return entry.name.lower()
    parts = [entry.name, entry.summary, entry.details, entry.signature]
    if entry.info is not None:
        parts.extend([entry.info.get_command or "", entry.info.set_command or ""])
    return "\n".join(parts).lower()
