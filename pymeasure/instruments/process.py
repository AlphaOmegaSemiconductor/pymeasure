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

# from decimal import Decimal
# from typing import Any, Sequence, Union


def normalize_str_to_upper(input_str):
    """Normalize a string to its uppercase form.

    Intended for use as a ``preprocess_input`` or ``set_process`` callable on
    ``control`` / ``setting`` properties whose accepted values are upper-case
    SCPI mnemonics. Forwarding mixed-case user input through this function
    ensures the value matches the canonical form expected by the instrument.

    :param input_str: The string to uppercase.
    :returns: ``input_str.upper()``.

    Example::

        >>> normalize_str_to_upper("edge")
        'EDGE'
    """
    return input_str.upper()


def get_processor_default(caster, validator, values, default):
    """Returns a get_process callable that casts and validates a value, falling back to a default.

    The returned function casts the raw instrument response with ``caster``, then
    validates the result via ``validator(casted_val, values)``. If both succeed the
    cast value is returned; if either raises an exception ``default`` is returned
    instead.

    :param caster: A callable that converts the raw instrument response (e.g. ``int``,
        ``float``, or a custom function).
    :param validator: A callable with signature ``(value, values)`` that returns the
        value when valid or raises an exception when not (e.g.
        :func:`strict_range`, :func:`strict_discrete_set`).
    :param values: The allowed-values argument forwarded to ``validator``.
    :param default: The fallback value returned when casting or validation fails.
    :returns: A callable ``get_process(val)`` that returns the cast-and-validated value
        or ``default`` on any failure.
    """
    def get_process(val):

        casted_val = caster(val)
        try:
            if validator(casted_val, values):
                return casted_val
        except:
            pass
        return default
    return get_process


def preprocess_input_enum(enum_type):
    """Returns a preprocess_input callable that resolves a string to its canonical enum value.

    The returned function compares ``val`` case-insensitively against each member's
    value string and returns the canonical value on a match, or ``val`` unchanged if
    no member matches. Useful as ``preprocess_input`` on a ``control`` or ``setting``
    property whose ``values`` is an :class:`InstrumentStrEnum` subclass.

    :param enum_type: An :class:`InstrumentStrEnum` subclass (or any ``StrEnum``) whose
        member values are the canonical strings to match against.
    :returns: A callable ``preprocess(val)`` that returns the matching member's value string,
        or ``val`` unchanged if no member matches.

    Example::

        >>> from pymeasure.instruments.values import str_enum_from_values
        >>> Waveform = str_enum_from_values("Waveform", ["SINusoid", "SQUare"])
        >>> proc = preprocess_input_enum(Waveform)
        >>> proc("sinusoid")
        'SINusoid'
        >>> proc("SQUARE")
        'SQUare'
        >>> proc("TRI")
        'TRI'
    """
    def preprocess(val):
        val_cf = str(val).casefold()
        for m in enum_type:
            if m.value.casefold() == val_cf:
                return m
        return val
    return preprocess


def set_processor_dict_map(map):
    """Returns a set_process callable that resolves an input value to its canonical map key.

    Selects between :func:`_set_processor_dict_str_map` (all-string map) and
    :func:`_set_processor_dict_mixed_map` (mixed ``str``/``int``/``float`` map) based on
    the types present in ``map``.  In both cases the returned function uses prefix-based,
    case-insensitive matching for string inputs; the mixed variant additionally supports
    exact numeric equality for ``int``/``float`` keys.

    :param map: A dict whose keys are canonical forms and whose values drive prefix
        matching.  For all-string maps the value is the abbreviation prefix
        (e.g. ``{"CURRent": "CURR", "VOLTage": "VOLT"}``).  For mixed maps numeric keys
        are matched by exact equality alongside string prefix matching
        (e.g. ``{"CURRent": "CURR", 1: "1", 2.5: "2.5"}``).
    :returns: A callable ``set_process(val)`` that returns the matching canonical key,
        or ``val`` unchanged if no entry matches.
    :raises TypeError: If ``map`` contains keys or values that are not all strings or not
        all ``str``/``int``/``float``.

    Example::

        >>> proc = set_processor_dict_map({"CURRent": "CURR", "VOLTage": "VOLT"})
        >>> proc("curr")
        'CURRent'
        >>> proc("VOLT")
        'VOLTage'
        >>> proc("POW")
        'POW'
    """
    if all(isinstance(k, str) and isinstance(v, str) for k, v in map.items()):
        return _set_processor_dict_str_map(map)
    elif all(isinstance(k, (str, int, float)) and isinstance(v, (str, int, float)) for k, v in map.items()):
        return _set_processor_dict_mixed_map(map)
    raise TypeError("All keys and values in map must be strings, or mixed str, int, floats")

def _set_processor_dict_str_map(map):
    """Returns a set_process callable that resolves an input value to its canonical map key.

    The returned function iterates over ``map`` and returns the key ``k`` whose
    lowercase form contains the first ``len(v)`` characters of ``val``
    (case-insensitively), where ``v`` is the corresponding map value. If no entry
    matches, ``val`` is returned unchanged. Useful for normalizing abbreviated or
    mixed-case SCPI strings to their canonical representation.

    :param map: A dict whose keys are canonical string forms and whose values are
        the abbreviation strings that determine the prefix length used for
        matching (e.g. ``{"CURRent": "CURR", "VOLTage": "VOLT"}``).
    :returns: A callable ``set_process(val)`` that returns the matching canonical key,
        or ``val`` unchanged if no entry matches.

    Example::

        >>> proc = set_processor_dict_map({"CURRent": "CURR", "VOLTage": "VOLT"})
        >>> proc("CURR")
        'CURRent'
        >>> proc("volt")
        'VOLTage'
        >>> proc("POW")
        'POW'
    """
    def set_process(val):
        for k, v in map.items():
            if val[:len(v)].casefold() in k.casefold():
                return  k
        return val
    return set_process

def _set_processor_dict_mixed_map(map):
    """Returns a set_process callable that resolves an input to its canonical map key.

    The returned function dispatches on the type of ``val``: if ``val`` is a string it
    performs the same prefix-based case-insensitive lookup as
    :func:`_set_processor_dict_str_map` — returning the key ``k`` whose lowercase form
    contains the first ``len(v)`` characters of ``val``; if ``val`` is an ``int`` or
    ``float`` it performs an exact equality check against the keys.  If no entry
    matches in either branch, ``val`` is returned unchanged.

    :param map: A dict whose keys are the canonical forms (``str``, ``int``, or
        ``float``) and whose values are the corresponding abbreviation strings used for
        prefix matching when the key is a string
        (e.g. ``{"CURRent": "CURR", 1: "1", 2.5: "2.5"}``).
    :returns: A callable ``set_process(val)`` that returns the matching canonical key,
        or ``val`` unchanged if no entry matches.

    Example::

        >>> proc = _set_processor_dict_mixed_map({"CURRent": "CURR", 1: "1", 2.5: "2.5"})
        >>> proc("CURR")
        'CURRent'
        >>> proc(1)
        1
        >>> proc(2.5)
        2.5
        >>> proc("POW")
        'POW'
    """
    # Is there a better way to filter this? I vaguely recall a builtin filter method/class?
    map_str_only = {k:v for k,v in map.items() if isinstance(k, str)}
    def set_process(val):
        if isinstance(val, str):
            for k in map_str_only.keys():
                # only consider the key for this method, this is not scpi cmd focused
                if val[:len(k)].casefold() in k.casefold(): 
                    return  k
        elif isinstance(val, (float, int)):
            for k in map.values():
                if val == k: # hopefully resolves minor type differences like 1 and 1.0
                    return  k
        return val
    return set_process

# TODO might want a nearest neighbor or something, 
# like resolve to the nearest numerical value if available? 