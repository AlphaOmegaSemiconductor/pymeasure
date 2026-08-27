.. module:: pymeasure.instruments.help

####################
Runtime help
####################

:class:`~pymeasure.instruments.help.HelpMixin` gives an instrument or channel a
``.help()`` that documents its pymeasure properties — their access mode, SCPI
commands, validators and value limits — alongside its methods, and a
``.help_search()`` that covers the whole channel and subsystem tree.

Add it as an extra parent class::

    from pymeasure.instruments import Channel, HelpMixin, Instrument

    class MyScope(HelpMixin, Instrument):
        """A four-channel scope."""

        _help_root = "scope"
        _help_important = ("autoset",)

    scope.help()                      # overview and child index
    scope.help(verbose=True)          # commands, limits, validators, hooks
    scope.help("coupling")            # one property in full
    scope.help_search("HORizontal")   # search names, docstrings and commands

The mixin is only a convenience shell. The same information is available for any
driver, whether or not it opted in, through :func:`describe`,
:func:`describe_tree` and :func:`search`, which introspect properties built with
:meth:`~pymeasure.instruments.common_base.CommonBase.control` and its
derivatives. Help never reads from the instrument.

The module's own ``help.md`` covers the curation attributes, how property
metadata is recovered, and the aggregation rules in detail.

The mixin
=========

.. autoclass:: pymeasure.instruments.help.HelpMixin
    :members:

Describing an instrument
========================

.. autofunction:: pymeasure.instruments.help.describe

.. autofunction:: pymeasure.instruments.help.describe_tree

.. autofunction:: pymeasure.instruments.help.search

.. autofunction:: pymeasure.instruments.help.clear_cache

Introspection
=============

.. autofunction:: pymeasure.instruments.help.is_pymeasure_property

.. autofunction:: pymeasure.instruments.help.property_info

.. autofunction:: pymeasure.instruments.help.render_limits

.. autofunction:: pymeasure.instruments.help.validator_name

The data model
==============

.. autoclass:: pymeasure.instruments.help.PropertyInfo
    :members:

.. autoclass:: pymeasure.instruments.help.HelpEntry
    :members:

.. autoclass:: pymeasure.instruments.help.HelpSection
    :members:

.. autoclass:: pymeasure.instruments.help.HelpDocument
    :members:

.. autoclass:: pymeasure.instruments.help.ChildGroup
    :members:

.. autoclass:: pymeasure.instruments.help.SearchHit
    :members:
