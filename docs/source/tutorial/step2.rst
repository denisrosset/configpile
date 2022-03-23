Step 2: Reuse defaults, short flags
===================================

In this step:

- We reused the :data:`~configpile.parsers.float_parser` float parser instead of defining 
  our own.

- We added short versions of the command-line flags, ``-x`` and ``-y``. Each parameter
  can correspond to a short flag (should be composed of an hyphen following by a single
  letter or digit) and/or a long flag (should start with two hyphens, following by a
  lower-case name in `kebab case <https://en.wikipedia.org/wiki/Letter_case#Kebab_case>`_.
  By default, :attr:`~configpile.arg.Param.short_flag_name` is not set (i.e. is `None`),
  and :attr:`~configpile.arg.Param.long_flag_name` is set to 
  :attr:`configpile.arg.Derived.KEBAB_CASE`, which means it is derived from the field name.

Code
----

.. literalinclude:: ../../../examples/calculator2.py

Executions
----------

.. command-output:: python ../../examples/calculator2.py --help

.. command-output:: python ../../examples/calculator2.py -x 1 -y 2
