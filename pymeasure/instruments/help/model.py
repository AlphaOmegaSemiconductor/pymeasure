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

"""Data model for the instrument help system.

Help is built into these dataclasses rather than printed directly. Keeping the
structured form is what lets one description feed the Jupyter renderer, the
terminal renderer, tree aggregation and search without any of them re-parsing
strings.

See help.md for detailed documentation.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Iterator

# Access modes of a pymeasure property, derived from which commands it carries.
ACCESS_READ = "read"
ACCESS_WRITE = "write"
ACCESS_READ_WRITE = "read-write"
ACCESS_NONE = "none"

#: Compact single-column labels used by the overview table.
ACCESS_SHORT = {
    ACCESS_READ: "R",
    ACCESS_WRITE: "W",
    ACCESS_READ_WRITE: "RW",
    ACCESS_NONE: "-",
}

# Entry kinds.
KIND_PROPERTY = "property"
KIND_METHOD = "method"
KIND_NARRATIVE = "narrative"

# Visibility buckets, ordered from most to least prominent in the overview.
VISIBILITY_IMPORTANT = "important"
VISIBILITY_NORMAL = "normal"
VISIBILITY_HIDDEN = "hidden"
VISIBILITY_INTERNAL = "internal"

# Child group kinds, used as section headings in an aggregated document.
GROUP_CHANNELS = "Channels"
GROUP_SUBSYSTEMS = "Subsystems"


@dataclass(frozen=True)
class PropertyInfo:
    """Everything recoverable about one :meth:`CommonBase.control` property.

    Instances are immutable and cached per class, so a bound description copies
    with :func:`dataclasses.replace` rather than mutating.

    Note:
        ``values`` may be a list or dict, so instances must not be used as
        dictionary keys even though the dataclass is frozen.

    Attributes:
        name: The attribute name the property is bound to.
        access: One of the ``ACCESS_*`` constants.
        doc: The ``docs`` argument, with any ``"(dynamic)"`` suffix removed.
        get_command: The raw query command template, or ``None`` if write-only.
        set_command: The raw write command template, or ``None`` if read-only.
        resolved_get_command: ``get_command`` with the channel id substituted;
            ``None`` unless described from a bound instance whose substitution
            actually changed the template.
        resolved_set_command: As above, for ``set_command``.
        validator: Rendered validator name; empty for the permissive default.
        values: The ``values`` argument exactly as passed.
        limits: Human-readable rendering of ``values`` for this validator.
        map_values: The ``map_values`` argument (``None`` for measurements).
        cast: Name of the cast callable applied to each returned field.
        separator: Field separator used to split the instrument reply.
        maxsplit: Maximum number of splits, ``-1`` for no limit.
        get_process: Name of the get-side processing hook; empty if unset.
        set_process: Name of the set-side processing hook; empty if unset.
        preprocess_input: Name of the input preprocessing hook; empty if unset.
        preprocess_reply: Name of the reply preprocessing hook; empty if unset.
        command_process: Name of the command processing hook; empty if unset.
        check_get_errors: Whether errors are polled after a read.
        check_set_errors: Whether errors are polled after a write.
        values_kwargs: Further keyword arguments handed to ``values()``.
        dynamic: Whether the property is a :class:`DynamicProperty`.
        overrides: Effective dynamic parameter values that differ from the class
            default; empty unless described from a bound instance.
        complete: ``False`` when introspection degraded and fields may be missing.
    """

    name: str
    access: str = ACCESS_NONE
    doc: str = ""
    get_command: str | None = None
    set_command: str | None = None
    resolved_get_command: str | None = None
    resolved_set_command: str | None = None
    validator: str = ""
    values: Any = ()
    limits: str = ""
    map_values: bool | None = False
    cast: str = "float"
    separator: str = ","
    maxsplit: int = -1
    get_process: str = ""
    set_process: str = ""
    preprocess_input: str = ""
    preprocess_reply: str = ""
    command_process: str = ""
    check_get_errors: bool = False
    check_set_errors: bool = False
    values_kwargs: dict[str, Any] = field(default_factory=dict)
    dynamic: bool = False
    overrides: dict[str, Any] = field(default_factory=dict)
    complete: bool = True

    @property
    def readable(self) -> bool:
        """Whether the property can be read from the instrument."""
        return self.access in (ACCESS_READ, ACCESS_READ_WRITE)

    @property
    def writable(self) -> bool:
        """Whether the property can be written to the instrument."""
        return self.access in (ACCESS_WRITE, ACCESS_READ_WRITE)


@dataclass
class HelpEntry:
    """A single documented item: a property, a method, or a narrative block.

    Attributes:
        name: Identifier, or the heading of a narrative block.
        kind: One of the ``KIND_*`` constants.
        summary: First line of the docstring.
        details: Remainder of the docstring.
        signature: Call signature for methods; empty otherwise.
        visibility: One of the ``VISIBILITY_*`` constants.
        path: Dotted access path, e.g. ``"mso58.ch_1.coupling"``.
        info: Extracted metadata, present only for pymeasure properties.
    """

    name: str
    kind: str
    summary: str = ""
    details: str = ""
    signature: str = ""
    visibility: str = VISIBILITY_NORMAL
    path: str = ""
    info: PropertyInfo | None = None

    def copy(self) -> HelpEntry:
        """Return an independent copy, so cached entries are never mutated."""
        return replace(self)


@dataclass
class HelpSection:
    """A titled group of entries shown together in the overview.

    Attributes:
        heading: Section title, e.g. ``"Key properties"``.
        entries: The entries belonging to this section, in display order.
    """

    heading: str
    entries: list[HelpEntry] = field(default_factory=list)

    def __bool__(self) -> bool:
        """A section is falsy when empty, so empty sections can be skipped."""
        return bool(self.entries)


@dataclass
class HelpDocument:
    """The complete help description built for one class or instance.

    Attributes:
        title: Display title, from ``_help_title`` or the class name.
        description: First line of the class docstring.
        sections: Ordered content sections.
        groups: Aggregated child classes; populated only by ``describe_tree``.
        path: Dotted access path of the described object.
    """

    title: str
    description: str = ""
    sections: list[HelpSection] = field(default_factory=list)
    groups: list[ChildGroup] = field(default_factory=list)
    path: str = ""

    def iter_entries(self) -> Iterator[HelpEntry]:
        """Yield every entry across all sections, in display order."""
        for section in self.sections:
            for entry in section.entries:
                yield entry

    def find(self, name: str) -> HelpEntry | None:
        """Return the entry whose name matches ``name`` case-insensitively."""
        target = name.strip().lower()
        for entry in self.iter_entries():
            if entry.name.lower() == target:
                return entry
        return None


@dataclass
class ChildGroup:
    """One child *class*, together with every instance of it under the root.

    Eight channels of the same class collapse into a single group so the
    aggregate shows that class's properties once, labelled with the instances
    it covers.

    Attributes:
        child_class: The type all instances in this group share.
        kind: ``GROUP_CHANNELS`` or ``GROUP_SUBSYSTEMS``.
        paths: Canonical access path of each instance, in discovery order.
        representative: The first instance; supplies resolved commands.
        document: Help for ``child_class``, bound to ``representative``.
    """

    child_class: type
    kind: str
    paths: tuple[str, ...]
    representative: Any
    document: HelpDocument

    @property
    def label(self) -> str:
        """The child class name, used as the group's display label."""
        return self.child_class.__name__


@dataclass
class SearchHit:
    """One match produced by a help search.

    Attributes:
        path: Access path of the representative instance's matched entry.
        entry: The matched entry.
        source_title: Title of the document the entry came from.
        multiplicity: Number of instances sharing the matched class.
    """

    path: str
    entry: HelpEntry
    source_title: str
    multiplicity: int = 1
