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

"""Introspection of pymeasure properties into structured help.

:meth:`CommonBase.control` closes its ``get_command``, ``values``, ``validator``
and friends over the ``fget``/``fset`` it builds. Almost all of them land as
*default arguments* of those functions, because :class:`DynamicProperty` binds
per-instance overrides to them by keyword; the remainder (``cast``, ``maxsplit``,
``preprocess_reply``, ``separator``, ``values_kwargs``) land in ``fget``'s
closure. Both are read back here, so nothing in the property creators needs to
change and properties built against an unpatched pymeasure describe just as well.

Every function in this module is defensive: a driver written against a future
pymeasure, or a hand-written ``@property``, degrades to less information rather
than raising.

See help.md for detailed documentation.
"""

from __future__ import annotations

import inspect
import logging
import pathlib
from enum import Enum
from typing import Any, Callable, Iterator

from ..common_base import CommonBase, DynamicProperty
from .model import (
    ACCESS_NONE,
    ACCESS_READ,
    ACCESS_READ_WRITE,
    ACCESS_WRITE,
    KIND_METHOD,
    KIND_NARRATIVE,
    KIND_PROPERTY,
    HelpEntry,
    PropertyInfo,
)

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

#: Appended to the docstring of every dynamic property by ``control``.
_DYNAMIC_SUFFIX = "(dynamic)"

_FGET_QUALNAME = "CommonBase.control.<locals>.fget"
_JOINED_QUALNAME = "joined_validators.<locals>.validate"
#: ``control`` builds this lambda when ``command_process`` is not supplied.
_COMMAND_PROCESS_NOOP_QUALNAME = "CommonBase.control.<locals>.<lambda>"

#: Narrative headings lifted from a sibling ``<dirname>.md``, when one exists.
MARKDOWN_NARRATIVE_HEADINGS = ("Workflows and Use Cases", "Best Practices")

_MAX_SET_ITEMS = 12
_MAX_MAP_PAIRS = 8


class _Missing:
    """Sentinel for an absent value, distinct from ``None``."""


_MISSING = _Missing()


def _identity_defaults() -> tuple[Callable, ...]:
    """Collect the pass-through lambdas that the property creators default to.

    ``control``, ``measurement`` and ``setting`` each declare their own
    ``lambda v: v`` defaults, so a hook is only worth reporting when it is none
    of them. Identity comparison is used rather than name matching, which would
    also swallow a driver's own lambda.

    Returns:
        The default callables of all three property creators.
    """
    found = []
    for creator in (CommonBase.control, CommonBase.measurement, CommonBase.setting):
        try:
            parameters = inspect.signature(creator).parameters.values()
        except (ValueError, TypeError):  # pragma: no cover - defensive
            continue
        for parameter in parameters:
            default = parameter.default
            if callable(default) and getattr(default, "__name__", "") == "<lambda>":
                found.append(default)
    return tuple(found)


_IDENTITY_DEFAULTS = _identity_defaults()

#: Every parameter a dynamic property may have overridden on an instance.
_DYNAMIC_PARAMS = tuple(
    dict.fromkeys(CommonBase._fget_params_list + CommonBase._fset_params_list)
)


# --------------------------------------------------------------------- docstrings

def summarize_docstring(doc: str | None) -> tuple[str, str]:
    """Split a docstring into a one-line summary and the remaining body.

    Args:
        doc: A raw docstring, or ``None``.

    Returns:
        A ``(summary, body)`` tuple. ``summary`` is the first non-empty line and
        ``body`` everything after it, both stripped. Both are empty when ``doc``
        is falsy.
    """
    if not doc:
        return "", ""
    lines = inspect.cleandoc(doc).strip().splitlines()
    if not lines:
        return "", ""
    return lines[0].strip(), "\n".join(lines[1:]).strip()


def _property_docstring(fget: Callable | None) -> str:
    """Return a property's ``docs`` text with the dynamic marker removed."""
    doc = getattr(fget, "__doc__", None) or ""
    if doc.endswith(_DYNAMIC_SUFFIX):
        doc = doc[: -len(_DYNAMIC_SUFFIX)]
    return inspect.cleandoc(doc).strip()


# ------------------------------------------------------------------ introspection

def _signature_defaults(func: Callable | None) -> dict[str, Any]:
    """Return the default value of every keyword parameter of ``func``."""
    if func is None:
        return {}
    try:
        parameters = inspect.signature(func).parameters
    except (ValueError, TypeError):
        return {}
    return {
        name: parameter.default
        for name, parameter in parameters.items()
        if parameter.default is not inspect.Parameter.empty
    }


def _closure_values(func: Callable | None) -> dict[str, Any]:
    """Return the name-to-value mapping of ``func``'s closure cells."""
    if func is None:
        return {}
    code = getattr(func, "__code__", None)
    closure = getattr(func, "__closure__", None)
    if code is None or not closure:
        return {}
    values = {}
    for name, cell in zip(code.co_freevars, closure):
        try:
            values[name] = cell.cell_contents
        except ValueError:  # pragma: no cover - empty cell
            continue
    return values


def is_pymeasure_property(member: Any) -> bool:
    """Return whether ``member`` was built by :meth:`CommonBase.control`.

    Identification is by the qualified name of the generated getter, with a
    fallback on its parameter names so a vendored or renamed ``CommonBase``
    is still recognised.

    Args:
        member: Any class attribute.

    Returns:
        ``True`` for a property created by ``control``, ``measurement`` or
        ``setting``; ``False`` for a hand-written property or anything else.
    """
    if not isinstance(member, property) or member.fget is None:
        return False
    if getattr(member.fget, "__qualname__", "") == _FGET_QUALNAME:
        return True
    try:
        names = set(inspect.signature(member.fget).parameters)
    except (ValueError, TypeError):
        return False
    return names.issuperset(CommonBase._fget_params_list)


def iter_properties(cls: type) -> Iterator[tuple[str, property]]:
    """Yield ``(name, property)`` for every pymeasure property on ``cls``.

    Walks ``vars()`` of each class in the MRO rather than using ``getattr``, so
    no getter is ever invoked and no instrument is contacted. The most-derived
    definition of a name wins.

    Args:
        cls: The class to introspect.

    Yields:
        Name and descriptor pairs, in MRO order.
    """
    seen = set()
    for klass in cls.__mro__:
        if klass is object:
            continue
        for name, member in vars(klass).items():
            if name in seen or (name.startswith("__") and name.endswith("__")):
                continue
            if is_pymeasure_property(member):
                seen.add(name)
                yield name, member


# ---------------------------------------------------------------------- rendering

def _hook_name(func: Any) -> str:
    """Return a display name for a processing hook, or empty if it is a default."""
    if func is None:
        return ""
    if any(func is default for default in _IDENTITY_DEFAULTS):
        return ""
    if getattr(func, "__qualname__", "") == _COMMAND_PROCESS_NOOP_QUALNAME:
        return ""
    return getattr(func, "__name__", "") or repr(func)


def validator_name(func: Any) -> str:
    """Return a display name for a validator.

    Args:
        func: The ``validator`` callable captured by the property.

    Returns:
        The validator's name, ``"joined(a, b)"`` for a
        :func:`~pymeasure.instruments.validators.joined_validators` composite,
        or an empty string for the permissive default.
    """
    name = _hook_name(func)
    if not name:
        return ""
    if getattr(func, "__qualname__", "") == _JOINED_QUALNAME:
        parts = _closure_values(func).get("validators", ())
        names = [getattr(part, "__name__", "?") for part in parts]
        return "joined({})".format(", ".join(names))
    return name


def _number(value: Any) -> str:
    """Format a bound of a numeric range compactly."""
    if isinstance(value, bool) or not isinstance(value, float):
        return str(value)
    return "{:g}".format(value)


def _elide(items: list[str], limit: int) -> str:
    """Join ``items`` with commas, replacing the tail past ``limit`` with a count."""
    if len(items) <= limit:
        return ", ".join(items)
    return "{}, ... +{} more".format(", ".join(items[:limit]), len(items) - limit)


def _render_enum(values: type) -> str:
    """Render an :class:`enum.Enum` subclass used as ``values``."""
    items = []
    for member in values:
        if str(member.name) == str(member.value):
            items.append(str(member.name))
        else:
            items.append("{}={}".format(member.name, member.value))
    return "{" + _elide(items, _MAX_SET_ITEMS) + "}"


def _render_mapping(values: dict) -> str:
    """Render a ``map_values`` dictionary as user value to instrument value."""
    items = ["{}->{}".format(key, value) for key, value in values.items()]
    return "{" + _elide(items, _MAX_MAP_PAIRS) + "}"


def _render_sequence(values: Any) -> str:
    """Render a discrete set of allowed values."""
    items = [str(value) for value in values]
    return "{" + _elide(items, _MAX_SET_ITEMS) + "}"


def _render_interval(name: str, values: Any) -> str:
    """Render a two-element ``values`` used with a range validator."""
    low, high = min(values), max(values)
    text = "[{}, {}]".format(_number(low), _number(high))
    if name.startswith("modular"):
        text += " wraps"
    return text


def render_limits(validator: Any, values: Any, map_values: bool | None = False) -> str:
    """Render ``values`` into a human-readable limit string for its validator.

    The same ``values`` means different things to different validators: ``[0, 10]``
    is an interval for :func:`strict_range` and a two-element choice for
    :func:`strict_discrete_set`. Rendering therefore dispatches on the pair.

    Args:
        validator: The validator callable captured by the property.
        values: The ``values`` argument exactly as passed.
        map_values: Whether ``values`` is a mapping rather than a set of choices.

    Returns:
        A limit string such as ``"[0, 1720]"``, ``"{AC, DC, DCR}"`` or
        ``"{True->1, False->0}"``. Empty when there is no constraint to show.
    """
    try:
        return _render_limits(validator, values, map_values)
    except Exception:
        log.debug("help: could not render limits for %r", values, exc_info=True)
        return ""


def _render_limits(validator: Any, values: Any, map_values: bool | None) -> str:
    """Body of :func:`render_limits`; see there for the contract."""
    # An Enum subclass is iterable, so it must be recognised before sequences.
    if isinstance(values, type) and issubclass(values, Enum):
        return _render_enum(values)

    name = validator_name(validator)
    if name.startswith("joined("):
        parts = _closure_values(validator).get("validators", ())
        if isinstance(values, (list, tuple)) and len(values) == len(parts):
            rendered = [_render_limits(part, group, map_values)
                        for part, group in zip(parts, values)]
            return " or ".join(text for text in rendered if text)

    if isinstance(values, range):
        return "[{}, {}] step {}".format(values.start, values.stop - values.step, values.step)
    if not values:
        return ""
    if isinstance(values, dict):
        return _render_mapping(values) if map_values else _render_sequence(list(values))
    if "range" in name and isinstance(values, (list, tuple)) and len(values) == 2:
        return _render_interval(name, values)
    if isinstance(values, (list, tuple, set, frozenset)):
        return _render_sequence(values)
    return str(values)


# ----------------------------------------------------------------- property_info

def _access_mode(get_command: Any, set_command: Any) -> str:
    """Return the access mode implied by the presence of each command.

    ``control`` always builds both ``fget`` and ``fset``, so a missing accessor
    is never the signal; a ``None`` command is.
    """
    if get_command is not None and set_command is not None:
        return ACCESS_READ_WRITE
    if get_command is not None:
        return ACCESS_READ
    if set_command is not None:
        return ACCESS_WRITE
    return ACCESS_NONE


def _resolve_command(instance: Any, command: Any) -> str | None:
    """Substitute the channel id into ``command``, or return ``None``.

    ``Channel.insert_id`` uses :meth:`str.format_map` and raises on a brace that
    is not a known placeholder, and subsystem classes may not define it at all.
    Both degrade to an unresolved command rather than an error.
    """
    if not isinstance(command, str) or "{" not in command:
        return None
    insert_id = getattr(instance, "insert_id", None)
    if not callable(insert_id):
        return None
    try:
        resolved = insert_id(command)
    except Exception:
        log.debug("help: insert_id failed for %r", command, exc_info=True)
        return None
    return resolved if resolved != command else None


def _differs(value: Any, default: Any) -> bool:
    """Return whether ``value`` differs from ``default``, tolerating odd types."""
    if value is default:
        return False
    try:
        return bool(value != default)
    except Exception:  # pragma: no cover - exotic __ne__
        return True


def _dynamic_overrides(prop: property, instance: Any, defaults: dict[str, Any]) -> dict[str, Any]:
    """Collect the dynamic parameters ``instance`` has overridden.

    Overrides live under a reserved name of the form
    ``<prefix><property>_<param>``; the un-prefixed name is deliberately
    unreadable, so the prefix carried on the descriptor must be used.

    Args:
        prop: The :class:`DynamicProperty` descriptor.
        instance: The bound instrument or channel.
        defaults: Class-level values, to report only genuine differences.

    Returns:
        Mapping of parameter name to its effective value on ``instance``.
    """
    prefix = getattr(prop, "prefix", "")
    name = getattr(prop, "name", "")
    if not name:
        return {}
    overrides = {}
    for param in _DYNAMIC_PARAMS:
        try:
            value = getattr(instance, prefix + name + "_" + param, _MISSING)
        except Exception:  # pragma: no cover - defensive
            continue
        if value is _MISSING:
            continue
        if _differs(value, defaults.get(param, _MISSING)):
            overrides[param] = value
    return overrides


def property_info(name: str, prop: property, instance: Any = None) -> PropertyInfo:
    """Extract the full description of one pymeasure property.

    Args:
        name: The attribute name the property is bound to.
        prop: The property descriptor, as found in the class ``__dict__``.
        instance: When given, commands are resolved through ``insert_id`` and
            dynamic overrides are read from it.

    Returns:
        A :class:`PropertyInfo`. On any introspection failure the result carries
        whatever was recovered with ``complete`` set to ``False``; this function
        does not raise.
    """
    try:
        return _property_info(name, prop, instance)
    except Exception:
        log.debug("help: introspection failed for property %r", name, exc_info=True)
        return PropertyInfo(
            name=name,
            doc=_property_docstring(getattr(prop, "fget", None)),
            complete=False,
        )


def _property_info(name: str, prop: property, instance: Any) -> PropertyInfo:
    """Body of :func:`property_info`; see there for the contract."""
    fget, fset = prop.fget, prop.fset
    getter = _signature_defaults(fget)
    setter = _signature_defaults(fset)
    closure = _closure_values(fget)
    merged = dict(setter)
    merged.update(getter)

    get_command = getter.get("get_command")
    set_command = setter.get("set_command")
    values = getter.get("values", setter.get("values", ()))
    map_values = getter.get("map_values", setter.get("map_values", False))
    validator = setter.get("validator")
    cast = closure.get("cast", float)

    dynamic = isinstance(prop, DynamicProperty)
    overrides = {}
    if dynamic and instance is not None:
        overrides = _dynamic_overrides(prop, instance, merged)

    return PropertyInfo(
        name=name,
        access=_access_mode(get_command, set_command),
        doc=_property_docstring(fget),
        get_command=get_command,
        set_command=set_command,
        resolved_get_command=(
            _resolve_command(instance, get_command) if instance is not None else None
        ),
        resolved_set_command=(
            _resolve_command(instance, set_command) if instance is not None else None
        ),
        validator=validator_name(validator),
        values=values,
        limits=render_limits(validator, values, map_values),
        map_values=map_values,
        cast=getattr(cast, "__name__", None) or str(cast),
        separator=closure.get("separator", ","),
        maxsplit=closure.get("maxsplit", -1),
        get_process=_hook_name(getter.get("get_process")),
        set_process=_hook_name(setter.get("set_process")),
        preprocess_input=_hook_name(setter.get("preprocess_input")),
        preprocess_reply=_hook_name(closure.get("preprocess_reply")),
        command_process=_hook_name(getter.get("command_process")),
        check_get_errors=bool(getter.get("check_get_errors", False)),
        check_set_errors=bool(setter.get("check_set_errors", False)),
        values_kwargs=dict(closure.get("values_kwargs") or {}),
        dynamic=dynamic,
        overrides=overrides,
    )


def needs_instance_pass(info: PropertyInfo) -> bool:
    """Return whether describing ``info`` from an instance can add anything.

    Only dynamic properties and templated commands vary per instance; the rest
    of a description is class-level and is reused from the cache.
    """
    if info.dynamic:
        return True
    for command in (info.get_command, info.set_command):
        if isinstance(command, str) and "{" in command:
            return True
    return False


# ------------------------------------------------------------------ class members

def _member_entry(name: str, member: Any) -> HelpEntry | None:
    """Build the entry for a non-pymeasure class member, or ``None`` to skip it."""
    if isinstance(member, property):
        summary, details = summarize_docstring(inspect.getdoc(member.fget))
        return HelpEntry(name=name, kind=KIND_PROPERTY, summary=summary, details=details)

    func = member.__func__ if isinstance(member, (staticmethod, classmethod)) else member
    if not callable(func) or isinstance(func, type):
        return None
    summary, details = summarize_docstring(inspect.getdoc(func))
    try:
        signature = str(inspect.signature(func))
    except (ValueError, TypeError):
        signature = ""
    return HelpEntry(
        name=name, kind=KIND_METHOD, summary=summary, details=details, signature=signature
    )


def introspect_members(cls: type, exclude: frozenset) -> tuple[list[HelpEntry], dict[str, Any]]:
    """Collect help entries for every member declared across ``cls``'s MRO.

    Args:
        cls: The class to introspect.
        exclude: Member names to omit entirely.

    Returns:
        A ``(entries, descriptors)`` tuple. ``entries`` holds one
        :class:`HelpEntry` per member with the most-derived definition winning;
        ``descriptors`` maps the name of each pymeasure property to its
        descriptor, so a bound description can re-read it.
    """
    entries: dict[str, HelpEntry] = {}
    descriptors: dict[str, Any] = {}
    for klass in cls.__mro__:
        if klass is object:
            continue
        for name, member in vars(klass).items():
            if name in entries or name in exclude:
                continue
            if name.startswith("__") and name.endswith("__"):
                continue
            try:
                if is_pymeasure_property(member):
                    info = property_info(name, member)
                    summary, details = summarize_docstring(info.doc)
                    entries[name] = HelpEntry(
                        name=name, kind=KIND_PROPERTY, summary=summary,
                        details=details, info=info,
                    )
                    descriptors[name] = member
                    continue
                entry = _member_entry(name, member)
                if entry is not None:
                    entries[name] = entry
            except Exception:  # pragma: no cover - defensive
                log.debug("help: skipping member %r of %r", name, cls, exc_info=True)
    return list(entries.values()), descriptors


# --------------------------------------------------------------------- narrative

def find_sibling_md(cls: type) -> pathlib.Path | None:
    """Locate a ``<dirname>.md`` documentation file beside a class's source.

    Walks the MRO, so a driver inherits its manufacturer package's narrative.
    pymeasure ships no such files, in which case this simply returns ``None``
    and the narrative source contributes nothing.

    Args:
        cls: The class whose source directory, and its bases', is inspected.

    Returns:
        The path to the nearest matching markdown file, or ``None``.
    """
    for klass in cls.__mro__:
        if klass is object:
            continue
        try:
            source = pathlib.Path(inspect.getfile(klass))
        except (TypeError, OSError):
            continue
        candidate = source.parent / (source.parent.name + ".md")
        if candidate.is_file():
            return candidate
    return None


def extract_markdown_sections(
    md_path: pathlib.Path,
    headings: tuple[str, ...] = MARKDOWN_NARRATIVE_HEADINGS,
) -> dict[str, str]:
    """Extract the body under each of the given ``##`` headings.

    Args:
        md_path: Path to a markdown file.
        headings: Heading titles to capture, matched case-insensitively.

    Returns:
        Mapping of heading title to body text. Empty on any read error.
    """
    try:
        text = md_path.read_text(encoding="utf-8")
    except OSError:
        return {}

    wanted = {heading.lower(): heading for heading in headings}
    result: dict[str, str] = {}
    current: str | None = None
    buffer: list[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current is not None:
                result[current] = "\n".join(buffer).strip()
            current = wanted.get(line[3:].strip().lower())
            buffer = []
            continue
        if current is not None:
            buffer.append(line)
    if current is not None:
        result[current] = "\n".join(buffer).strip()
    return result


def narrative_entries(cls: type) -> list[HelpEntry]:
    """Build narrative entries from a sibling markdown file, if there is one."""
    md_path = find_sibling_md(cls)
    if md_path is None:
        return []
    return [
        HelpEntry(name=heading, kind=KIND_NARRATIVE, details=body)
        for heading, body in extract_markdown_sections(md_path).items()
        if body
    ]
