Step 1: Simple calculator
=========================

We build a script that takes two floating-point values as an argument, adds them and displays
them.

In the code below, we write our own :class:`~configpile.parsers.Parser` subclass to parse
floating-point numbers.

Let's observe a few things.

On the code general structure:

- The most used ``configpile`` identifiers are imported when writing
  ``from configpile import *``; they are aliases of identifiers in subpackages
  (for example ``configpile.Config`` is an alias of :class:`configpile.config.Config`).

- The "configuration" is a dataclass using :func:`~dataclasses.dataclass`. It should be frozen
  because there is no reason not to.

- The "configuration" is also a subclass of :class:`configpile.config.Config`.

- The script help is given in the class docstring; argument descriptions are written using 
  `sphinx autodoc <https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html>`_ style
  comments (they start with ``#:``).


On the parser declaration:

- A parser is a subclass of :class:`configpile.parsers.Parser`, which is generic: when
  declaring the inheritance relation, we specify *what* this parser returns: a ``float``.

  To subclass a parser, one only needs to implement the :meth:`~configpile.parsers.Parser.parse`
  method.


On the parameter declarations:

- The parameters are dataclass fields. They are automatically filled by ``configpile`` when
  calling :meth:`configpile.config.Config.from_command_line_` using the information given
  in the `annotated <https://docs.python.org/3/library/typing.html#typing.Annotated>`_ 
  type annotation.

- The extra information provided in the :data:`typing.Annotated` wrapper is removed when
  type checking, and is used only by ``configpile`` when it performs its introspection.
  For `mypy <https://mypy.readthedocs.io/en/stable/>`_, the fields ``x`` and ``y`` have type
  ``float``.

- The extra information is of type :class:`~configpile.arg.Param`, and the concept is detailed in
  :ref:`concepts:params`.

- Here, we instantiate a :class:`~configpile.arg.Param` through the
  :meth:`configpile.arg.Param.store` static method. This a kind of parameter that takes
  the last value provided. Note that we did not define a default value for the parameters, thus
  both of them will be required.
 
- The command-line flags ``--x`` and ``--y`` are automatically deduced from the Python identifiers.

On the sample script executions:

- Note that when the script is called with a ``--help`` argument, or when the configuration
  cannot be parsed, the script execution is aborted. When ``configpile`` deals with a
  ``--help`` argument, the script execution has an exit value of ``0``, but when there is
  an error, the exit value will be positive to signal this fact.

- When several errors occur, ``configpile`` does not stop at the first error encountered
  but accumulates them.

Code
----

.. literalinclude:: ../../../examples/calculator1.py

Executions
----------

Note that on the examples below, the path to the Python script is relative to the ``docs/source``
folder.

.. command-output:: python ../../examples/calculator1.py --help

.. command-output:: python ../../examples/calculator1.py --x 1 --y 2

.. command-output:: python ../../examples/calculator1.py --x asd --y zxc
   :returncode: 1
