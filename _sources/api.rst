API
===

The package ``configpile`` reexports a few symbols for ease of use, and they are imported in the
current scope by ``from configpile import *``.

Those identifiers are:

- :class:`~configpile.config.Config`
- :class:`~configpile.arg.Derived`
- :class:`~configpile.userr.Err`
- :class:`~configpile.arg.Expander`
- :class:`~configpile.parsers.ForceCase`
- :class:`~configpile.arg.Param`
- :mod:`~configpile.parsers`
- :class:`~configpile.parsers.Parser`
- :class:`~configpile.arg.Positional`
- :class:`~configpile.userr.Res`

.. toctree::
    :hidden:
    :maxdepth: 1

.. autosummary::
   :toctree: _autosummary
   :recursive:

   configpile.arg
   configpile.collector
   configpile.config
   configpile.parsers
   configpile.processor
   configpile.userr
   configpile.util

