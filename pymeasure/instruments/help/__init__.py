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

"""Runtime help for pymeasure instruments.

:class:`HelpMixin` gives an instrument or channel a ``.help()`` that documents
its pymeasure properties — their access mode, SCPI commands, validators and
value limits — alongside its methods, and a ``.help_search()`` that covers the
whole channel and subsystem tree.

The same information is available without the mixin through :func:`describe`,
:func:`describe_tree` and :func:`search`, which introspect any class built with
:meth:`CommonBase.control` and its derivatives.

See help.md for detailed documentation.
"""

from .document import clear_cache, describe
from .extract import is_pymeasure_property, property_info, render_limits, validator_name
from .mixin import HelpMixin
from .model import (
    ChildGroup,
    HelpDocument,
    HelpEntry,
    HelpSection,
    PropertyInfo,
    SearchHit,
)
from .tree import ChildRef, describe_tree, search, walk

__all__ = [
    "ChildGroup",
    "ChildRef",
    "HelpDocument",
    "HelpEntry",
    "HelpMixin",
    "HelpSection",
    "PropertyInfo",
    "SearchHit",
    "clear_cache",
    "describe",
    "describe_tree",
    "is_pymeasure_property",
    "property_info",
    "render_limits",
    "search",
    "validator_name",
    "walk",
]
