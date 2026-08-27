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

"""Rendering of help documents to Markdown or plain text.

One document renders two ways: as Markdown for a Jupyter kernel, and as plain
text at a terminal. The per-property detail block is shared between them as an
indented, aligned key/value listing, which is valid Markdown and already
readable as text.

IPython is imported lazily inside :func:`in_ipython`, so the help system has no
dependency on it, and terminal output degrades rather than raising when the
console encoding cannot represent a docstring's Unicode.

See help.md for detailed documentation.
"""

from __future__ import annotations

import textwrap
from typing import Any

from .model import (
    ACCESS_SHORT,
    KIND_NARRATIVE,
    KIND_PROPERTY,
    VISIBILITY_HIDDEN,
    VISIBILITY_INTERNAL,
    ChildGroup,
    HelpDocument,
    HelpEntry,
    HelpSection,
    PropertyInfo,
    SearchHit,
)

#: Paths listed in full in a child group heading before eliding.
_MAX_GROUP_PATHS = 5
_MAX_TEXT_WIDTH = 100


def in_ipython() -> bool:
    """Return whether an IPython or Jupyter kernel is running."""
    try:
        from IPython import get_ipython
    except ImportError:
        return False
    return get_ipython() is not None


def safe_print(text: Any) -> None:
    """Print ``text``, replacing characters the console encoding cannot encode.

    Instrument docstrings carry ohm, micro and plus-minus signs that a cp1252
    Windows console cannot always represent; help must degrade, not raise.
    """
    import sys

    try:
        print(text)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        print(str(text).encode(encoding, errors="replace").decode(encoding))


def display(text: str) -> None:
    """Show rendered help, richly in a notebook and as plain text elsewhere."""
    if in_ipython():
        from IPython.display import Markdown, display as ipython_display

        ipython_display(Markdown(text))
    else:
        safe_print(text)


# ------------------------------------------------------------------ shared parts

def visible(section: HelpSection, hidden: bool) -> list[HelpEntry]:
    """Return the entries of ``section`` that should be shown."""
    return [
        entry for entry in section.entries
        if entry.visibility != VISIBILITY_INTERNAL
        and (hidden or entry.visibility != VISIBILITY_HIDDEN)
    ]


def has_hidden(document: HelpDocument) -> bool:
    """Return whether any entry is suppressed by default."""
    return any(
        entry.visibility in (VISIBILITY_HIDDEN, VISIBILITY_INTERNAL)
        for entry in document.iter_entries()
    )


def _command_value(template: str, resolved: str | None) -> str:
    """Render a command template, showing its resolved form when it differs."""
    return template if resolved is None else "{}  ->  {}".format(template, resolved)


def _hooks(info: PropertyInfo) -> str:
    """Join the non-default processing hooks into one row value."""
    pairs = (
        ("get_process", info.get_process),
        ("set_process", info.set_process),
        ("preprocess_input", info.preprocess_input),
        ("preprocess_reply", info.preprocess_reply),
        ("command_process", info.command_process),
    )
    return ", ".join("{}={}".format(name, value) for name, value in pairs if value)


def detail_rows(info: PropertyInfo) -> list[tuple[str, str]]:
    """Build the label/value rows shown for one property in verbose output.

    Rows at their default are omitted, so an ordinary property shows two lines
    rather than a dozen.
    """
    rows: list[tuple[str, str]] = []
    if info.get_command:
        rows.append(("get", _command_value(info.get_command, info.resolved_get_command)))
    if info.set_command:
        rows.append(("set", _command_value(info.set_command, info.resolved_set_command)))
    if info.limits:
        limits = info.limits
        if info.validator:
            limits += "  ({})".format(info.validator)
        rows.append(("limits", limits))
    elif info.validator:
        rows.append(("validator", info.validator))
    if info.map_values:
        rows.append(("mapped", "values are translated on the way in and out"))
    if info.cast != "float":
        rows.append(("cast", info.cast))
    if info.separator != ",":
        rows.append(("separator", repr(info.separator)))
    if info.maxsplit != -1:
        rows.append(("maxsplit", str(info.maxsplit)))
    hooks = _hooks(info)
    if hooks:
        rows.append(("processing", hooks))
    checks = [name for name, flag in (("after get", info.check_get_errors),
                                      ("after set", info.check_set_errors)) if flag]
    if checks:
        rows.append(("error check", ", ".join(checks)))
    if info.values_kwargs:
        rows.append(("values kwargs", repr(info.values_kwargs)))
    if info.dynamic:
        rows.append(("dynamic", "parameters may be overridden per instance"))
    for name, value in info.overrides.items():
        rows.append(("override", "{} = {!r}".format(name, value)))
    if not info.complete:
        rows.append(("note", "metadata could not be fully recovered"))
    return rows


def _rows_block(rows: list[tuple[str, str]], indent: str = "    ") -> list[str]:
    """Render label/value rows as an aligned, indented block."""
    if not rows:
        return []
    width = max(len(label) for label, _ in rows)
    return [indent + label.ljust(width) + "  " + value for label, value in rows]


def _entry_headline(entry: HelpEntry, quote: str) -> str:
    """Render an entry's name, signature and access mode as one line."""
    name = "{}{}{}".format(quote, entry.name + entry.signature, quote)
    if entry.kind != KIND_PROPERTY or entry.info is None:
        return name
    suffix = entry.info.access
    if entry.info.dynamic:
        suffix += ", dynamic"
    return "{} - {}".format(name, suffix)


def group_heading(group: ChildGroup, root: str, dash: str) -> str:
    """Render a child group's heading, eliding a long instance list."""
    labels = [relative_path(path, root) for path in group.paths]
    if len(labels) > _MAX_GROUP_PATHS:
        shown = ", ".join(labels[:3]) + ", ... +{}".format(len(labels) - 3)
    else:
        shown = ", ".join(labels)
    return "{} {} {} ({})".format(group.kind, dash, group.label, shown)


def relative_path(path: str, root: str) -> str:
    """Strip the root prefix from an access path for display."""
    prefix = root + "."
    return path[len(prefix):] if root and path.startswith(prefix) else path


def _short_signature(entry: HelpEntry) -> str:
    """Abbreviate a method signature for the compact overview table.

    A full signature is useful in the detail view and ruinous in a table: the
    property creators' own signatures run to several hundred characters.
    """
    if entry.kind != KIND_PROPERTY and entry.signature:
        return "()" if entry.signature in ("()", "(self)") else "(...)"
    return ""


def _entry_names(document: HelpDocument, hidden: bool) -> list[str]:
    """Return the visible property names, for a compact child index line."""
    names = []
    for section in document.sections:
        for entry in visible(section, hidden):
            if entry.kind == KIND_PROPERTY:
                names.append(entry.name)
    return names


# --------------------------------------------------------------------- markdown

def _escape(text: str) -> str:
    """Escape the one character that breaks a Markdown table cell."""
    return text.replace("|", "\\|")


def _table_md(entries: list[HelpEntry]) -> list[str]:
    """Render entries as a compact Markdown table."""
    lines = ["| Name | Access | Description |", "| --- | :---: | --- |"]
    for entry in entries:
        access = ACCESS_SHORT.get(entry.info.access, "-") if entry.info else ""
        name = entry.name + _short_signature(entry)
        lines.append("| `{}` | {} | {} |".format(_escape(name), access, _escape(entry.summary)))
    lines.append("")
    return lines


def _verbose_md(entries: list[HelpEntry], level: int) -> list[str]:
    """Render entries as full Markdown detail blocks."""
    lines: list[str] = []
    for entry in entries:
        lines.append("{} {}".format("#" * level, _entry_headline(entry, "`")))
        lines.append("")
        for text in (entry.summary, entry.details):
            if text:
                lines.extend([text, ""])
        if entry.info is not None:
            block = _rows_block(detail_rows(entry.info))
            if block:
                lines.extend(block)
                lines.append("")
    return lines


def _section_md(section: HelpSection, hidden: bool, verbose: bool, level: int) -> list[str]:
    """Render one section to Markdown lines."""
    entries = visible(section, hidden)
    if not entries:
        return []
    lines = ["{} {}".format("#" * level, section.heading), ""]
    if entries[0].kind == KIND_NARRATIVE:
        lines.extend([entries[0].details, ""])
        return lines
    if verbose:
        lines.extend(_verbose_md(entries, level + 1))
    else:
        lines.extend(_table_md(entries))
    return lines


def to_markdown(document: HelpDocument, verbose: bool = False, hidden: bool = False) -> str:
    """Render a help document as Markdown.

    Args:
        document: The document to render.
        verbose: Show every property's commands, limits and hooks.
        hidden: Include entries curated as advanced.

    Returns:
        A Markdown string, ending in a newline.
    """
    lines = ["# {}".format(document.title), ""]
    if document.description:
        lines.extend([document.description, ""])
    for section in document.sections:
        lines.extend(_section_md(section, hidden, verbose, level=2))
    for group in document.groups:
        lines.append("## {}".format(group_heading(group, document.path, "—")))
        lines.append("")
        if verbose:
            for section in group.document.sections:
                lines.extend(_section_md(section, hidden, True, level=3))
        else:
            names = _entry_names(group.document, hidden)
            lines.extend([", ".join("`{}`".format(name) for name in names), ""])
    lines.extend(_footer(document, verbose, hidden))
    return "\n".join(lines).rstrip() + "\n"


# ------------------------------------------------------------------- plain text

def _table_text(entries: list[HelpEntry]) -> list[str]:
    """Render entries as an aligned plain-text table."""
    rows = [
        (entry.name + _short_signature(entry),
         ACCESS_SHORT.get(entry.info.access, "-") if entry.info else "",
         entry.summary)
        for entry in entries
    ]
    name_width = max(len(row[0]) for row in rows)
    access_width = max(2, max(len(row[1]) for row in rows))
    budget = _MAX_TEXT_WIDTH - name_width - access_width - 6
    lines = []
    for name, access, summary in rows:
        if budget > 3 and len(summary) > budget:
            summary = summary[: budget - 3] + "..."
        lines.append("  {}  {}  {}".format(
            name.ljust(name_width), access.ljust(access_width), summary).rstrip())
    lines.append("")
    return lines


def _verbose_text(entries: list[HelpEntry]) -> list[str]:
    """Render entries as full plain-text detail blocks."""
    lines: list[str] = []
    for entry in entries:
        lines.extend(["  " + _entry_headline(entry, ""), ""])
        for text in (entry.summary, entry.details):
            if text:
                lines.extend(textwrap.indent(text, "    ").splitlines())
                lines.append("")
        if entry.info is not None:
            block = _rows_block(detail_rows(entry.info), indent="      ")
            if block:
                lines.extend(block)
                lines.append("")
    return lines


def _section_text(section: HelpSection, hidden: bool, verbose: bool) -> list[str]:
    """Render one section to plain-text lines."""
    entries = visible(section, hidden)
    if not entries:
        return []
    lines = ["", section.heading, "-" * len(section.heading)]
    if entries[0].kind == KIND_NARRATIVE:
        lines.extend(["", entries[0].details, ""])
        return lines
    lines.extend(_verbose_text(entries) if verbose else _table_text(entries))
    return lines


def to_text(document: HelpDocument, verbose: bool = False, hidden: bool = False) -> str:
    """Render a help document as plain text.

    Args:
        document: The document to render.
        verbose: Show every property's commands, limits and hooks.
        hidden: Include entries curated as advanced.

    Returns:
        A plain-text string with no Markdown markup.
    """
    lines = [document.title, "=" * len(document.title)]
    if document.description:
        lines.extend(["", document.description])
    for section in document.sections:
        lines.extend(_section_text(section, hidden, verbose))
    for group in document.groups:
        heading = group_heading(group, document.path, "-")
        lines.extend(["", heading, "=" * len(heading)])
        if verbose:
            for section in group.document.sections:
                lines.extend(_section_text(section, hidden, True))
        else:
            lines.extend(["  " + ", ".join(_entry_names(group.document, hidden)), ""])
    lines.extend(_footer(document, verbose, hidden))
    return "\n".join(lines).rstrip() + "\n"


# ----------------------------------------------------------------------- pieces

def _footer(document: HelpDocument, verbose: bool, hidden: bool) -> list[str]:
    """Build the trailing hints about what the current view is not showing."""
    hints = []
    if not verbose:
        hints.append('call .help(verbose=True) for commands and limits, '
                     'or .help("<name>") for one item')
    if not hidden and has_hidden(document):
        hints.append("call .help(hidden=True) to show advanced members")
    return ["", "({})".format("; ".join(hints))] if hints else []


def entry_detail(entry: HelpEntry, markdown: bool = True) -> str:
    """Render one entry's full detail.

    Args:
        entry: The entry to render.
        markdown: Render as Markdown rather than plain text.

    Returns:
        The rendered detail block.
    """
    if markdown:
        return "\n".join(_verbose_md([entry], level=3)).rstrip() + "\n"
    return "\n".join(_verbose_text([entry])).rstrip() + "\n"


def group_detail(group: ChildGroup, root: str, markdown: bool = True,
                 hidden: bool = False) -> str:
    """Render one child group in full, as if it were its own document."""
    document = HelpDocument(
        title=group_heading(group, root, "—" if markdown else "-"),
        description=group.document.description,
        sections=group.document.sections,
        path=group.document.path,
    )
    if markdown:
        return to_markdown(document, verbose=True, hidden=hidden)
    return to_text(document, verbose=True, hidden=hidden)


def search_results(hits: list[SearchHit], query: str, markdown: bool = True) -> str:
    """Render search hits.

    Args:
        hits: The matches to show.
        query: The query, echoed back in the heading.
        markdown: Render as a Markdown table rather than aligned text.

    Returns:
        The rendered result listing.
    """
    if not hits:
        return "No help matches for {!r}.".format(query)
    rows = [
        ("{}{}".format(hit.path, " (x{})".format(hit.multiplicity)
                       if hit.multiplicity > 1 else ""),
         hit.entry.kind,
         hit.entry.summary)
        for hit in hits
    ]
    heading = "{} match(es) for {!r}".format(len(hits), query)
    if markdown:
        lines = ["### {}".format(heading), "", "| Path | Kind | Description |",
                 "| --- | --- | --- |"]
        lines.extend("| `{}` | {} | {} |".format(_escape(path), kind, _escape(summary))
                     for path, kind, summary in rows)
        return "\n".join(lines) + "\n"
    width = max(len(row[0]) for row in rows)
    lines = [heading + ":"]
    lines.extend("  {}  {}".format(path.ljust(width), summary).rstrip()
                 for path, _kind, summary in rows)
    return "\n".join(lines) + "\n"
