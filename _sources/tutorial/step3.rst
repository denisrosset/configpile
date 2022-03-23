Step 3: Two positional arguments
================================

For the parameters that are *not* optional, it makes sense to parse them in a positional manner,
i.e. take them from the command line arguments without them being preceded by a flag.

Now, for both ``x`` and ``y``, we set their :attr:`~configpile.arg.Param.long_flag_name` and
:attr:`~configpile.arg.Param.short_flag_name` fields to `None`, and set their 
:attr:`~configpile.arg.Param.positional` field to :attr:`~configpile.arg.Positional.ONCE`,
which means that a single value is expected for both.

Note how the usage description changed in the execution sample.

Code
----

.. literalinclude:: ../../../examples/calculator3.py

Executions
----------

.. command-output:: python ../../examples/calculator3.py --help

.. command-output:: python ../../examples/calculator3.py 1 3
