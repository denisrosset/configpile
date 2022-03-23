Step 5: Additional features
===========================

Finally, we include two additional parameters in our calculator.

- The user can choose between addition and multiplication. The default operation is addition (``"+"``).

- The user can select the number of displayed digits, the default value is ``3``.

Note the following new features.

- **Parameter from a list of choices**

  One can construct a parser of strings using the :meth:`~configpile.parsers.Parser.from_choices`
  static method of :class:`~configpile.arg.Param`. The possible choices are displayed in the
  usage description when invoking the script help.

- **Default values**

  Default values are given as strings, and they are parsed by ``configpile`` using the same parser
  used for other strings. Though if there is a problem, we do not report an error but rather throw
  an exception.

- **Environment variables**

  Parameters can be set from environment variables, though this is disabled by default.

  Set the :attr:`configpile.arg.Param.env_var_name` field to enable this feature, and
  see how to use it in the sample executions below. Note that one can ``export DIGITS=10`` in
  Bash scripts as well.

- **Validation**

  By applying the :meth:`~configpile.parsers.Parser.validated` method on a parser, one 
  can ensure that the final value in the configuration obeys constraints.

Code
----

.. literalinclude:: ../../../examples/calculator5.py

Executions
----------

.. command-output:: python ../../examples/calculator5.py --help

.. command-output:: python ../../examples/calculator5.py 1 2 3 4 --operation "*"

.. command-output:: bash -c "DIGITS=10 python ../../examples/calculator5.py 1 2 3 4"
