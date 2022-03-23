Step 4: Many positional arguments
=================================

Some scripts may get a variable number of values. Here we update our calculator so that
it takes an arbitrary number of positional values.

Note that the field type has changed: instead of ``float``, it is now a ``Sequence[float]``.

The parameter declaration changed as well: we now use the :meth:`~configpile.arg.Param.append1`
static method of :class:`~configpile.arg.Param`, which works by taking a parser of a given type,
here ``float``, to collect the values of a parameter of type ``Sequence[float]``.


Code
----

.. literalinclude:: ../../../examples/calculator4.py

Executions
----------

.. command-output:: python ../../examples/calculator4.py --help

.. command-output:: python ../../examples/calculator4.py 1 2 3 4
