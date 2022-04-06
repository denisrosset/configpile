API
===

The package ``configpile`` reexports a few symbols for ease of use, and they are imported in
the current scope by ``from configpile import *``.

Those identifiers are:

- :class:`~configpile.config.Config`
- :class:`~configpile.enums.Derived`
- :class:`~configpile.userr.Err`
- :class:`~configpile.arg.Expander`
- :class:`~configpile.enums.ForceCase`
- :class:`~configpile.arg.Param`
- :mod:`~configpile.parsers`
- :class:`~configpile.parsers.Parser`
- :class:`~configpile.enums.Positional`
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
   configpile.enums
   configpile.handlers
   configpile.parsers
   configpile.processor
   configpile.userr
   configpile.util
