# help

Runtime help for pymeasure instruments, channels and subsystems.

## Overview

`HelpMixin` gives a driver a `.help()` that documents its **pymeasure
properties** — the ones built by `CommonBase.control`, `CommonBase.measurement`
and `CommonBase.setting` — not just its methods. Per property it surfaces the
docstring, the access mode, and the SCPI commands, and on request the validator,
value limits, mapping, processing hooks, cast and dynamic overrides.

`.help_search()` covers the whole channel and subsystem tree and matches command
templates as well as text, so `scope.help_search("HORizontal:SCAle")` finds the
property that sends it.

Help is built into dataclasses rather than printed strings, so one description
feeds the Jupyter renderer, the terminal renderer, tree aggregation and search.

**Key components**

- `HelpMixin` (`mixin.py`) — inherit from it to gain `.help()` / `.help_search()`.
- `describe`, `describe_tree`, `search` — the same capability as free functions,
  working on *any* class built with the property creators, mixed in or not.
- `PropertyInfo`, `HelpDocument`, `HelpSection`, `HelpEntry`, `ChildGroup`,
  `SearchHit` (`model.py`) — the structured model.
- `extract.py` — recovery of property metadata; the only module that knows how
  `control` is built.
- `document.py` — curation, section assembly and the per-class cache.
- `tree.py` — child discovery, deduplication and aggregation.
- `render.py` — Markdown and plain text, with IPython detection and an
  encoding-safe terminal fallback.

## Quick start

```python
from pymeasure.instruments import Channel, HelpMixin, Instrument
from pymeasure.instruments.validators import strict_discrete_set

class MyChannel(HelpMixin, Channel):
    """One input channel."""

    coupling = Channel.control(
        "CH{ch}:COUP?", "CH{ch}:COUP %s",
        """Control the input coupling.""",
        validator=strict_discrete_set, values=["AC", "DC", "GND"],
    )

class MyScope(HelpMixin, Instrument):
    """A four-channel scope."""

    _help_root = "scope"
    _help_important = ("autoset",)

scope = MyScope(adapter)
scope.help()                        # overview: key items, properties, child index
scope.help(verbose=True)            # every command, limit, validator and hook
scope.help("coupling")              # one property in full
scope.help("ch_1")                  # everything that channel class offers
scope.help(hidden=True)             # include members curated as advanced
scope.help_search("COUP")           # search names, docstrings and commands
document = scope.help_document()    # the same thing as data
```

Without the mixin the engine still works:

```python
from pymeasure.instruments.help import describe_tree, search
describe_tree(some_third_party_instrument)
```

## Where the metadata comes from

`control` builds `fget` and `fset` closures and returns a `property`; nothing is
stored as an attribute. It is recoverable anyway, because the interesting
arguments become **default arguments** of those functions:

| argument | recovered from |
|---|---|
| `get_command`, `values`, `map_values`, `get_process`, `command_process`, `check_get_errors` | `fget` default arguments |
| `set_command`, `validator`, `values`, `map_values`, `preprocess_input`, `set_process`, `command_process`, `check_set_errors` | `fset` default arguments |
| `cast`, `maxsplit`, `preprocess_reply`, `separator`, `values_kwargs` | `fget` closure cells |
| `dynamic` | `isinstance(prop, DynamicProperty)` |
| `docs` | `fget.__doc__`, less the appended `(dynamic)` |

Those default-argument names are not incidental: they are exactly
`CommonBase._fget_params_list` and `_fset_params_list`, because
`DynamicProperty.__get__` binds per-instance overrides to them by keyword. That
is why nothing in `control` had to change to make this work, and why properties
built against an unpatched pymeasure describe just as well.
`test_control_signature_contract` guards the assumption.

Two traps worth knowing:

- **`control` always returns `property(fget, fset)`.** A measurement has a live
  `fset` whose `set_command` is `None` and which raises `LookupError` when
  called. Access mode therefore comes from the commands, never from a missing
  accessor.
- **`measurement` leaves `map_values` at `None`**, not `False`.

### Dynamic properties

A `dynamic=True` property accepts per-instance overrides written as
`instance.<name>_<param>`, stored under a reserved prefix. Reading the
un-prefixed name raises by design, so the effective value is read through the
descriptor's own `prefix` and `name`. Describing a class shows the defaults;
describing an instance additionally reports each parameter whose effective value
differs, under `PropertyInfo.overrides`.

### Command templates

`get_command` and `set_command` are always reported verbatim. When help is
called on a bound channel, the resolved form is added by calling that object's
own `insert_id` — never by substituting placeholders directly, since drivers
override `insert_id` (the Tektronix MSO channels substitute two placeholders)
and subsystem classes may not define it at all. `insert_id` uses
`str.format_map` and raises on an unknown brace, so the call is guarded and the
template stands alone when it fails.

## `HelpMixin`

**Curation attributes** (all optional; they select and order, never describe):

- `_help_title` — display title; defaults to the class name.
- `_help_root` — label the access paths hang off; defaults to the lowercased
  class name (`scope.ch_1.coupling`).
- `_help_important` — names featured first, under "Key properties" / "Key
  methods". Also re-includes a member the plumbing filter would otherwise drop.
- `_help_hidden` — names shown only with `help(hidden=True)`.
- `_help_exclude` — names omitted entirely.
- `_help_children` — explicit ordered child attribute names; `None`
  auto-discovers.
- `_help_child_exclude` — child attribute names to skip while auto-discovering.
- `_help_groups` — `((heading, (name, ...)), ...)`, splitting a long property
  list into subsections. Anything unlisted falls into "Other properties", so a
  new property is never silently invisible.
- `_help_use_md` — read narrative sections from a co-located `<dirname>.md`.

Lookup is plain attribute lookup: a subclass **replaces** its base's list. To
extend one, write `_help_important = Base._help_important + ("autoset",)`.

**Visibility precedence:** excluded, then hidden, then important, then normal.
Any remaining underscore-prefixed member is internal and never shown.

**Plumbing filter.** `document.PLUMBING_MEMBERS` lists the framework members
every driver inherits — `control`, `write`, `ask`, `values`, `add_child`,
`insert_id`, the help methods themselves — and they are excluded by default so a
driver's own API is what appears. It is a curated list rather than everything in
`vars(CommonBase)`, which would also swallow `reset`, `clear`, `shutdown` and
`check_errors`.

## Aggregation

`scope.help()` describes the instrument and every child class beneath it.

- Children are found by reading `vars(instance)` only. `getattr` on the class
  would fire property getters and talk to the instrument. Both routes are
  covered: attributes bound by `add_child` or by hand, and dict/list/tuple
  collections of children.
- **Identity dedupe first.** `scope.ch_1` and `scope.channels[0]` are one
  object; the better-ranked path wins (attribute over dict key over sequence
  index) and the other is recorded as an alias.
- **Class dedupe second.** Eight channels of one class collapse into one
  `ChildGroup`, labelled with the instances it covers:
  `Channels — ScopeChannel (ch_1, ch_2, ch_3, ... +5)`. Two children of
  different classes give two groups.
- Recursion is depth-first, cycle-guarded by object id, with `parent` skipped by
  name as well, and bounded by `max_depth` (which logs rather than truncating
  silently).
- Every aggregated entry carries its dotted path, built from the group's first
  representative — which also supplies the resolved commands.
- The overview shows a compact index per group; `verbose=True`,
  `help("ch_1")` or `help("ScopeChannel")` expand one.

## Rendering

`to_markdown` in a Jupyter kernel, `to_text` at a terminal; IPython is imported
lazily so it is never a dependency, and terminal output degrades rather than
raising when the console encoding cannot represent a docstring's Unicode.

Compact output is a table of name, access and the docstring's first line, plus
one index line per child class. `verbose=True` adds, per property, its command
templates and resolved forms, limits and validator, mapping, cast, separator,
processing hooks, error checks and dynamic overrides — omitting every row that
is at its default, so an ordinary property shows two lines rather than a dozen.

## Workflows and Use Cases

**Add help to a driver.** Inherit `HelpMixin` alongside the existing base, and
add `_help_important` naming the handful of properties a user reaches for first.
Everything else is discovered. For a subsystem with more than about twenty
properties, add `_help_groups`.

**Find the property behind a SCPI command.** `scope.help_search("HORizontal")`
matches command templates as well as names and docstrings, and reports the
dotted path to each match.

**Inspect an instrument you did not write.** `describe_tree(instrument)` works on
any pymeasure driver, including ones from an unmodified install that never heard
of this package.

**Check a channel's real limits.** `scope.ch_1.help(verbose=True)` shows the
validator, the rendered limits and — for dynamic properties — the effective
per-instance override next to the class default.

## Best Practices

- Keep descriptions in the property's `docs` argument and in docstrings. Never
  restate them in `_help_*`: curation selects and orders, docstrings describe.
- Write a real docstring, not an f-string. `f"""..."""` in the class-docstring
  position is an expression, not a docstring, and leaves `__doc__` as `None`;
  the class then describes itself with an empty summary. An f-string passed as
  the `docs` *argument* to `control` is fine.
- Feature four to eight names in `_help_important`; the full list is always in
  the property sections.
- `help()` must never raise. Every source parses permissively and degrades to
  less information rather than erroring, including on third-party classes built
  against an unpatched pymeasure. Keep any extension to that contract.
- Help never calls a property. If a change here would make it read from the
  instrument, it is the wrong change — `test_help_performs_no_io` enforces this.
