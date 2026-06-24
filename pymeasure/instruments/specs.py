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

"""Generic instrument identification and capability-specification helpers.

This module is deliberately dependency-free (standard library only) so that it
can be imported anywhere — including by external projects — without pulling in
PyVISA, IPython or any project logging machinery.

It provides two building blocks:

* :class:`SCPI_ID` — a frozen dataclass wrapping the four fields of a SCPI
  ``*IDN?`` response, together with the :func:`scpi_id_parser` free function.
* :class:`InstrumentSpecs` — a generic, frozen base dataclass for per-model
  capability/limit tables. Instrument families subclass it with their own
  fields and build a ``{model_key: InstrumentSpecs}`` registry in their driver.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Optional, Type, TypeVar

_S = TypeVar("_S", bound="InstrumentSpecs")


def scpi_id_parser(id_string: str) -> Dict[str, Optional[str]]:
    """Parse a SCPI ``*IDN?`` response string into its four components.

    Args:
        id_string: Identification string returned by the ``*IDN?`` command,
            conventionally ``"<manufacturer>,<model>,<serial>,<revision>"``.

    Returns:
        Dictionary with keys ``'manufacturer'``, ``'model_num'``,
        ``'serial_num'`` and ``'software_rev'``. Any field that cannot be parsed
        from the string is ``None`` (e.g. an empty string, a non-string input,
        or fewer than four comma-separated parts yields all ``None``).
    """
    result: Dict[str, Optional[str]] = {
        "manufacturer": None,
        "model_num": None,
        "serial_num": None,
        "software_rev": None,
    }

    if id_string and isinstance(id_string, str):
        id_parts = id_string.split(",")
        if len(id_parts) >= 4:
            result["manufacturer"] = id_parts[0].strip()
            result["model_num"] = id_parts[1].strip()
            result["serial_num"] = id_parts[2].strip()
            result["software_rev"] = id_parts[3].strip()

    return result


@dataclass(frozen=True)
class SCPI_ID:
    """Parsed components of a SCPI ``*IDN?`` identification response.

    A ``*IDN?`` response conventionally contains four comma-separated fields:
    manufacturer, model number, serial number and software/firmware revision.

    Attributes:
        manufacturer: Instrument manufacturer name.
        model_num: Model number or identifier.
        serial_num: Serial number of the specific instrument.
        software_rev: Software or firmware revision/version.
    """

    manufacturer: Optional[str] = None
    model_num: Optional[str] = None
    serial_num: Optional[str] = None
    software_rev: Optional[str] = None

    @classmethod
    def from_id(cls, id: str) -> "SCPI_ID":
        """Create a :class:`SCPI_ID` from a raw ``*IDN?`` string.

        Args:
            id: SCPI ``*IDN?`` string to parse.

        Returns:
            A :class:`SCPI_ID` instance; unparseable fields are ``None``.
        """
        return cls.from_dict(scpi_id_parser(id))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SCPI_ID":
        """Create a :class:`SCPI_ID` from a dictionary of fields.

        Args:
            data: Mapping that may contain the keys ``'manufacturer'``,
                ``'model_num'``, ``'serial_num'`` and ``'software_rev'``.

        Returns:
            A :class:`SCPI_ID` instance; missing keys default to ``None``.
        """
        return cls(
            manufacturer=data.get("manufacturer"),
            model_num=data.get("model_num"),
            serial_num=data.get("serial_num"),
            software_rev=data.get("software_rev"),
        )

    def to_dict(self) -> Dict[str, Optional[str]]:
        """Convert this :class:`SCPI_ID` to a plain dictionary.

        Returns:
            Dictionary representation with the four identification fields.
        """
        return {
            "manufacturer": self.manufacturer,
            "model_num": self.model_num,
            "serial_num": self.serial_num,
            "software_rev": self.software_rev,
        }

    def validate(self) -> bool:
        """Check that every identification field is a non-empty string.

        Returns:
            ``True`` if all four fields are truthy (no ``None`` or ``''``),
            otherwise ``False``.
        """
        return all(
            (self.manufacturer, self.model_num, self.serial_num, self.software_rev)
        )


@dataclass(frozen=True)
class InstrumentSpecs:
    """Generic base for per-model instrument capability/limit specifications.

    This base carries no domain-specific fields; instrument families subclass it
    with their own (e.g. bandwidth, sample-rate ceilings, channel count) and
    build a registry mapping model keys to instances. It exists to hold limits
    that cannot be queried from the instrument over SCPI and therefore must live
    in code.
    """

    def to_dict(self) -> Dict[str, Any]:
        """Convert this specification to a plain dictionary.

        Returns:
            Dictionary of every dataclass field and its value.
        """
        return asdict(self)

    @staticmethod
    def normalize_model(model: str) -> str:
        """Normalize a model string for use as a registry key.

        Args:
            model: Raw model string (e.g. from a ``*IDN?`` response).

        Returns:
            The model string stripped of surrounding whitespace and uppercased.
        """
        return model.strip().upper()

    @classmethod
    def from_registry(
        cls: Type[_S], model: str, registry: Mapping[str, _S]
    ) -> _S:
        """Resolve a model string against a registry of specifications.

        Args:
            model: Model string to look up; matched case-insensitively via
                :meth:`normalize_model`.
            registry: Mapping of normalized model key to its specification.

        Returns:
            The matching specification from ``registry``.

        Raises:
            KeyError: If ``model`` is not present in ``registry``. The error
                message lists the supported model keys.
        """
        key = cls.normalize_model(model)
        if key not in registry:
            supported = ", ".join(sorted(registry)) or "(none)"
            raise KeyError(
                f"Unknown model {model!r}; supported models are: {supported}."
            )
        return registry[key]
