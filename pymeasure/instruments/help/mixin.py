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

"""``HelpMixin`` — runtime help for instruments and channels.

Add :class:`HelpMixin` to an :class:`~pymeasure.instruments.Instrument` or
:class:`~pymeasure.instruments.Channel` subclass and it gains ``.help()`` and
``.help_search()``. With no configuration the output is built entirely from
introspection; the optional ``_help_*`` attributes select and order what is
featured, and never restate what a docstring already says.

The mixin is a convenience shell. Everything it does is available as
:func:`~pymeasure.instruments.help.describe_tree` and
:func:`~pymeasure.instruments.help.search`, which work on any class whether or
not it inherits from here.

See help.md for detailed documentation.
"""

from __future__ import annotations

import logging
from typing import Any

from . import render
from .document import describe
from .model import HelpDocument
from .tree import default_root, describe_tree, search

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class HelpMixin:
    """Mixin giving an instrument or channel structured, searchable runtime help.

    All curation attributes are optional and select or order only; descriptive
    text always comes from docstrings.

    Attributes:
        _help_title: Display title; defaults to the class name.
        _help_root: Label the access paths hang off; defaults to the lowercased
            class name.
        _help_important: Names featured first, under "Key properties".
        _help_hidden: Names shown only when ``help(hidden=True)`` is used.
        _help_exclude: Names omitted entirely.
        _help_children: Explicit ordered child attribute names; ``None``
            auto-discovers children on the instance.
        _help_child_exclude: Child attribute names to skip while auto-discovering.
        _help_groups: ``((heading, (name, ...)), ...)`` splitting a long property
            list into subsections. Unlisted names fall into "Other properties".
        _help_use_md: Whether to read narrative sections from a co-located
            ``<dirname>.md`` documentation file, when one exists.
    """

    _help_title: str | None = None
    _help_root: str | None = None
    _help_important: tuple[str, ...] = ()
    _help_hidden: tuple[str, ...] = ()
    _help_exclude: tuple[str, ...] = ()
    _help_children: tuple[str, ...] | None = None
    _help_child_exclude: tuple[str, ...] = ()
    _help_groups: tuple[tuple[str, tuple[str, ...]], ...] = ()
    _help_use_md: bool = True

    # ------------------------------------------------------------------ public

    def help(self, topic: str | None = None, *, verbose: bool = False,
             hidden: bool = False, root: str | None = None) -> None:
        """Display help for this instrument, its channels and its subsystems.

        Args:
            topic: When ``None``, show the overview. Otherwise the name of a
                property, method, child attribute (``"ch_1"``) or child class
                (``"ScopeChannel"``) to show in full.
            verbose: Show every property's commands, limits and hooks rather
                than the compact index.
            hidden: Include members curated as advanced.
            root: Override the label access paths hang off.

        Returns:
            ``None``; the help is printed, or rendered as Markdown in Jupyter.
        """
        try:
            render.display(self._help_render(topic, verbose, hidden, root))
        except Exception:
            log.debug("help: rendering failed for %r", type(self), exc_info=True)
            render.safe_print(
                "Help is unavailable for {}: introspection failed.".format(
                    type(self).__name__)
            )

    def help_search(self, query: str, *, root: str | None = None) -> None:
        """Search this instrument and its children for ``query``.

        Matching covers names, docstrings and both SCPI command templates, so a
        command fragment finds the property that sends it.

        Args:
            query: Case-insensitive substring to look for.
            root: Override the label access paths hang off.

        Returns:
            ``None``; the results are printed, or shown as a table in Jupyter.
        """
        try:
            hits = search(self, query, root)
            render.display(render.search_results(hits, query, render.in_ipython()))
        except Exception:
            log.debug("help: search failed for %r", type(self), exc_info=True)
            render.safe_print("Help search is unavailable for {}.".format(
                type(self).__name__))

    def help_document(self, *, root: str | None = None,
                      aggregate: bool = True) -> HelpDocument:
        """Return this object's help as data, for tooling rather than display.

        Args:
            root: Override the label access paths hang off.
            aggregate: Include child classes as populated ``groups``.

        Returns:
            The :class:`HelpDocument` describing this object.
        """
        if aggregate:
            return describe_tree(self, root)
        return describe(self, default_root(self) if root is None else root)

    # ----------------------------------------------------------------- private

    def _help_render(self, topic: str | None, verbose: bool, hidden: bool,
                     root: str | None) -> str:
        """Build the string ``help`` displays."""
        markdown = render.in_ipython()
        document = describe_tree(self, root)
        if topic is None:
            if markdown:
                return render.to_markdown(document, verbose, hidden)
            return render.to_text(document, verbose, hidden)
        return _resolve_topic(document, topic, hidden, markdown)


def _resolve_topic(document: HelpDocument, topic: str, hidden: bool,
                   markdown: bool) -> str:
    """Render whichever entity ``topic`` names.

    Resolution order is child instance path, child class name, member of the
    root, then member of any child class. An ambiguous member name lists the
    candidates rather than guessing one.
    """
    needle = topic.strip().lower()
    root = document.path

    for group in document.groups:
        labels = {path.lower() for path in group.paths}
        labels.update(render.relative_path(path, root).lower() for path in group.paths)
        if needle in labels or needle == group.label.lower():
            return render.group_detail(group, root, markdown, hidden)

    entry = document.find(topic)
    if entry is not None:
        return render.entry_detail(entry, markdown)

    matches = []
    for group in document.groups:
        found = group.document.find(topic)
        if found is not None:
            matches.append((group, found))
    if len(matches) == 1:
        return render.entry_detail(matches[0][1], markdown)
    if matches:
        return _ambiguous(topic, matches, root)

    return ("No help topic named {!r} on {}. "
            "Call .help() to list what is available.").format(topic, document.title)


def _ambiguous(topic: str, matches: list[tuple[Any, Any]], root: str) -> str:
    """Report a member name that several child classes share."""
    lines = ["{!r} exists on several children:".format(topic)]
    for group, _entry in matches:
        lines.append("  {}.{}  ({})".format(
            render.relative_path(group.paths[0], root), topic, group.label))
    lines.append("Ask for one of these paths, or for the class by name.")
    return "\n".join(lines) + "\n"
