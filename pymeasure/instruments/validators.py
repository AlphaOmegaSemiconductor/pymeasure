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

from decimal import Decimal
from typing import Any, Iterable, Sequence, Union


def strict_range(value, values):
    """ Provides a validator function that returns the value
    if its value is less than or equal to the maximum and
    greater than or equal to the minimum of ``values``.
    Otherwise it raises a ValueError.

    :param value: A value to test
    :param values: A range of values (range, list, etc.)
    :raises: ValueError if the value is out of the range
    """
    if min(values) <= value <= max(values):
        return value
    else:
        raise ValueError('Value of {:g} is not in range [{:g},{:g}]'.format(
            value, min(values), max(values)
        ))


def strict_discrete_range(value, values, step):
    """ Provides a validator function that returns the value
    if its value is less than the maximum and greater than the
    minimum of the range and is a multiple of step.
    Otherwise it raises a ValueError.

    :param value: A value to test
    :param values: A range of values (range, list, etc.)
    :param step: Minimum stepsize (resolution limit)
    :raises: ValueError if the value is out of the range
    """
    # use Decimal type to provide correct decimal compatible floating
    # point arithmetic compared to binary floating point arithmetic
    if (strict_range(value, values) == value and
            Decimal(str(value)) % Decimal(str(step)) == 0):
        return value
    else:
        raise ValueError('Value of {:g} is not a multiple of {:g}'.format(
            value, step
        ))


def strict_discrete_set(value, values):
    """ Provides a validator function that returns the value
    if it is in the discrete set. Otherwise it raises a ValueError.

    :param value: A value to test
    :param values: A set of values that are valid
    :raises: ValueError if the value is not in the set
    """
    if value in values:
        return value
    else:
        raise ValueError('Value of {} is not in the discrete set {}'.format(
            value, values
        ))


def SCPI_discrete_set(value: str, values: Iterable[str]) -> str:
    """Validates ``value`` against SCPI-style abbreviated option strings.

    In SCPI convention the leading uppercase characters form the mandatory
    abbreviation (e.g. ``"CURRent"`` → ``"CURR"``, ``"INFinity"`` → ``"INF"``).
    ``value`` is accepted when it begins with the mandatory prefix of any
    option, compared case-insensitively.

    :param value: The string to validate.
    :param values: Candidate option strings using the SCPI capitalization
        convention (e.g. ``["CURRent", "VOLTage"]``).
    :returns: ``value`` unchanged if it matches any option.
    :raises ValueError: If ``value`` does not fuzzy-match any option.

    Example::

        >>> fuzzy_discrete_set("curr", ["CURRent", "VOLTage"])
        'curr'
        >>> fuzzy_discrete_set("CURRENT", ["CURRent", "VOLTage"])
        'CURRENT'
        >>> fuzzy_discrete_set("inf", ["INFinity", "MAXimum"])
        'inf'
        >>> fuzzy_discrete_set("freq", ["CURRent", "VOLTage"])
        Traceback (most recent call last):
        ...
        ValueError: Value of freq is not in the fuzzy discrete set ['CURRent', 'VOLTage']
    """
    values_list = list(values)
    value_upper = value.upper()
    for option in values_list:
        i = 0
        while i < len(option) and option[i].isupper():
            i += 1
        mandatory = option[:i]
        if mandatory and value_upper.startswith(mandatory):
            return value
    raise ValueError(
        'Value of {} is not in the fuzzy discrete set {}'.format(value, values_list)
    )


def truncated_range(value, values):
    """ Provides a validator function that returns the value
    if it is in the range. Otherwise it returns the closest
    range bound.

    :param value: A value to test
    :param values: A set of values that are valid
    """
    if min(values) <= value <= max(values):
        return value
    elif value > max(values):
        return max(values)
    else:
        return min(values)


def modular_range(value, values):
    """ Provides a validator function that returns the value
    if it is in the range. Otherwise it returns the value,
    modulo the max of the range.

    :param value: a value to test
    :param values: A set of values that are valid
    """
    return value % max(values)


def modular_range_bidirectional(value, values):
    """ Provides a validator function that returns the value
    if it is in the range. Otherwise it returns the value,
    modulo the max of the range. Allows negative values.

    :param value: a value to test
    :param values: A set of values that are valid
    """
    if value > 0:
        return value % max(values)
    else:
        return -1 * (abs(value) % max(values))


def truncated_discrete_set(value, values):
    """ Provides a validator function that returns the value
    if it is in the discrete set. Otherwise, it returns the smallest
    value that is larger than the value.

    :param value: A value to test
    :param values: A set of values that are valid
    """
    # Force the values to be sorted
    values = list(values)
    values.sort()
    for v in values:
        if value <= v:
            return v

    return values[-1]


def discreteTruncate(number, discreteSet):
    """ Truncates the number to the closest element in the positive discrete set.
    Returns False if the number is larger than the maximum value or negative.
    """
    if number < 0:
        return False
    discreteSet.sort()
    for item in discreteSet:
        if number <= item:
            return item
    return False

def cast_to_types(value: Any, casts: Sequence[type]) -> Any:
    """Attempts to cast ``value`` using each callable in ``casts``, returning on first success.

    Tries each callable in ``casts`` in order and returns the result of the
    first one that succeeds without raising ``ValueError`` or ``TypeError``.
    Useful for converting raw instrument response strings to the most
    appropriate Python type.

    :param value: The value to cast.
    :param casts: A non-empty sequence of callables (typically types) to try in
        order. Each is called as ``cast(value)``.
    :returns: ``value`` cast by the first callable in ``casts`` that succeeds.
    :raises ValueError: If ``casts`` is empty, or if every callable raises
        ``ValueError`` or ``TypeError`` when called with ``value``.

    Example::

        >>> cast_to_types('3', (int, float, str))
        3
        >>> cast_to_types('1.5', (int, float, str))
        1.5
        >>> cast_to_types('ON', (int, float, str))
        'ON'
    """
    if not casts:
        raise ValueError("casts must be a non-empty sequence")

    for cast in casts:
        try:
            return cast(value)
        except (ValueError, TypeError):
            pass

    raise ValueError(
        "Could not cast {!r} using any of: {}".format(
            value, [t.__name__ for t in casts]
        )
    )


def cast_to_alphanumeric(value: Any) -> Union[int, float, str]:
    """Casts ``value`` to ``int``, ``float``, or ``str``, whichever succeeds first.

    A convenience wrapper around :func:`cast_to_types` for the common case of
    converting raw instrument response strings to the most specific numeric
    type possible before falling back to a plain string.

    :param value: The value to cast.
    :returns: ``value`` as an ``int`` if possible, then ``float``, then ``str``.

    Example::

        >>> cast_to_alphanumeric('42')
        42
        >>> cast_to_alphanumeric('3.14')
        3.14
        >>> cast_to_alphanumeric('ON')
        'ON'
    """
    print("Value: ", value)
    return cast_to_types(value, (int, float, str))


# Keep "meta" validators at the end. these are composites of other validators
def joined_validators(*validators):
    """Returns a validator function that represents a list of validators joined together.

    A value passed to the validator is returned if it passes any validator (not all of them).
    Otherwise it raises a ValueError.

    Note: the joined validator expects ``values`` to be a sequence of ``values``
    appropriate for the respective validators (often sequences themselves).

    :Example:

    >>> from pymeasure.instruments.validators import strict_discrete_set, strict_range
    >>> from pymeasure.instruments.validators import joined_validators
    >>> joined_v = joined_validators(strict_discrete_set, strict_range)
    >>> values = [['MAX','MIN'], range(10)]
    >>> joined_v(5, values)
    5
    >>> joined_v('MAX', values)
    'MAX'
    >>> joined_v('NONSENSE', values)
    Traceback (most recent call last):
    ...
    ValueError: Value of NONSENSE does not match any of the joined validators

    :param validators: an iterable of other validators
    """

    def validate(value, values):
        for validator, vals in zip(validators, values):
            try:
                return validator(value, vals)
            except (ValueError, TypeError):
                pass
        raise ValueError(f"Value of {value} does not match any of the joined validators")

    return validate