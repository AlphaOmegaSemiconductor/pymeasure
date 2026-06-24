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

from dataclasses import dataclass, field
from enum import EnumMeta

try:
    from enum import StrEnum # only in python 3.10+?
except ImportError:
    from enum import Enum

    class StrEnum(str, Enum):
        """Compatibility shim: StrEnum was added in Python 3.11."""

        def __str__(self):
            return self.value


class _InstrumentEnumMeta(EnumMeta):
    def __contains__(cls, item):
        if isinstance(item, str):
            # Membership is by the member's original (canonical) value, matched
            # exactly. This lets ``"TRIGgered" in BURST_MODES`` succeed while a
            # wrong-case string such as ``"triggered"`` is reported as absent.
            return any(m.value == item for m in cls)
        return super().__contains__(item)

    def __getattr__(cls, name):
        # Members are accessible by their exact (upper-case) name as usual; if that
        # misses, fall back to a case-insensitive match so ``SHAPES.square`` resolves
        # to ``SHAPES.SQUARE``. This powers attribute access on the :class:`Choices`
        # container (e.g. ``channel.options.shape.square``).
        try:
            return super().__getattr__(name)  # type: ignore[misc]
        except AttributeError:
            name_cf = name.casefold()
            for member in cls.__members__.values():
                if member.name.casefold() == name_cf:
                    return member
            raise


class InstrumentStrEnum(StrEnum, metaclass=_InstrumentEnumMeta):
    """Base class for all instrument string enumerations."""


def str_enum_from_values(name: str, values) -> InstrumentStrEnum:
    """Create an :class:`InstrumentStrEnum` from a sequence of strings.

    Member names are the uppercase form of the values; member values preserve
    the original string (e.g. ``'TRIGgered'`` → member ``TRIGGERED``, value ``'TRIGgered'``).
    """
    if isinstance(values, dict):
        return InstrumentStrEnum(name, {k.upper(): v for k, v in values.items()})
    else:
        return InstrumentStrEnum(name, {v.upper(): v for v in values})


class RANGE_ENUM_LMH(StrEnum):
    '''
    Enum class for range settings with low, medium, high options
    '''
    LOW = 'LOW'
    MEDIUM = 'MED'
    HIGH = 'HIGH'


class RANGE_ENUM_LH(StrEnum):
    '''
    Enum class for range settings with low, medium, high options
    '''
    LOW = 'LOW'
    HIGH = 'HIGH'


class NORMAL_INVERTED_ENUM(StrEnum):
    '''
    Enum class for range settings with low, medium, high options
    '''
    NORMAL = 'NORMAL'
    INVERTED = 'INVERTED'


class RANGE:  # Deprecated?
    LOW = 'LOW'
    MEDIUM = 'MED'
    HIGH = 'HIGH'

# Predefined value groups for instruments to use. Each container is an immutable
# (frozen) singleton namespace, so callers import one group name per category and
# access members by attribute (e.g. ``DICTS.BOOLEAN_TO_INT``) instead of importing
# each constant individually.
# "A list, tuple, range, or dictionary of valid values, that can be used as to map
# values if map_values is True"


@dataclass(frozen=True)
class _Tuples:
    """Tuple value groups (e.g. for ``values=`` on a control/measurement)."""

    BINARY: tuple = (0, 1)
    BOOLEAN: tuple = (False, True)


@dataclass(frozen=True)
class _Dicts:
    """Mapping value groups, typically used with ``map_values=True``."""

    BOOLEAN_TO_INT: dict = field(default_factory=lambda: {True: 1, False: 0})
    BOOLEAN_TO_STR: dict = field(default_factory=lambda: {True: "True", False: "FALSE"})
    BOOLEAN_TO_ON_OFF: dict = field(default_factory=lambda: {True: "ON", False: "OFF"})


@dataclass(frozen=True)
class _Enums:
    """References to the shared instrument :class:`StrEnum` classes."""

    RANGE_ENUM_LMH: type = RANGE_ENUM_LMH
    RANGE_ENUM_LH: type = RANGE_ENUM_LH
    NORMAL_INVERTED_ENUM: type = NORMAL_INVERTED_ENUM


TUPLES = _Tuples()
DICTS = _Dicts()
ENUMS = _Enums()


class _ChoicesMeta(type):
    """Metaclass for :class:`Choices` containers.

    Makes the container class immutable (assigning or deleting a choice after the
    class is defined raises) and gives it a ``repr`` that lists each property and
    its member names for discovery. Operates on the class itself, since a
    :class:`Choices` subclass is used as a namespace rather than instantiated.
    """

    def __setattr__(cls, name, value):
        raise AttributeError(f"{cls.__name__} is immutable; cannot set {name!r}")

    def __delattr__(cls, name):
        raise AttributeError(f"{cls.__name__} is immutable; cannot delete {name!r}")

    def __repr__(cls):
        lines = [
            f"  {name}: {', '.join(member.name for member in enum)}"
            for name, enum in vars(cls).items()
            if not name.startswith("_")
            and isinstance(enum, type) and issubclass(enum, StrEnum)
        ]
        return f"{cls.__name__}(\n" + "\n".join(lines) + "\n)"


class Choices(metaclass=_ChoicesMeta):
    """Base class for an instrument's :class:`StrEnum` choice container.

    Subclass it and declare each accepted-value enum as a class attribute, keyed by
    the property name it backs. The subclass is the single source of truth for those
    enums: the driver references it directly in its property creators
    (``values=choices.shape``) and users discover the options the same way
    (``ch1.choices.shape.square``)::

        class AFG31000ChannelChoices(Choices):
            shape = str_enum_from_values("SHAPES", {"square": "SQU", "pulse": "PULS"})
            voltage_unit = str_enum_from_values("VOLTAGE_UNITS", ["VPP", "VRMS", "DBM"])

        class AFG31000Channel(Channel):
            choices = AFG31000ChannelChoices
            shape = Channel.control(..., values=choices.shape, ...)

    The container is used as a class (no instantiation needed) and is immutable, so an
    instrument's choices cannot be rebound by accident. Members resolve
    case-insensitively (``choices.shape.square`` is ``choices.shape.SQUARE``) because
    the enums are built on :class:`_InstrumentEnumMeta`, and ``repr`` lists every
    property and its members.

    When several properties share one enum, assign the alias directly
    (``fm_source = am_source``). Using the container is optional — a simple driver may
    keep its enums as plain attributes on the instrument class instead.
    """
