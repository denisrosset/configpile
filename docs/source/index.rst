Configpile: get clean configuration out of a pile of arguments
==============================================================

Configpile is a replacement for the :mod:`argparse` module of the Python
standard library.

It is written in clean, modern Python with extensive support of
`PEP 484 <https://peps.python.org/pep-0484/>`_ type hints and :mod:`dataclasses`.

It processes configuration settings coming from a variety of sources:

* Environment variables

* Command-line parameters

* Configuration files (INI)

Its best selling points are:

* **Code compactness**; from the same dataclass declaration, we derive a
  configuration parser, a command-line usage description and a Sphinx
  documentation block.

* Compatibility with **IDEs** (due to typed dataclasses as configuration results)

* **Error reporting**: Instead of crashing at the first parse error, configpile
  collects all the errors encountered and reports all of them.


How to use
----------

``configpile`` is easily installed through ``pip``::

  pip install configpile

It supports Python >= 3.8, depends only on
`class-doc <https://github.com/danields761/class-doc>`_ and ``typing_extensions``.

Optionally, it supports `parsy <https://github.com/python-parsy/parsy>`_ (to define more
complicated parsers) and `rich <https://github.com/Textualize/rich>`_ (for pretty-printing
error information).

You can do::

  pip install configpile[parsy,rich]

Code example
------------

(taken from :ref:`tutorial_step2`)

.. literalinclude:: ../../examples/calculator2.py

Execution result
----------------

.. command-output:: python ../../examples/calculator2.py --help

.. command-output:: python ../../examples/calculator2.py -x 1 -y 2


.. toctree::
    :hidden:
    :maxdepth: 3
    :caption: General information

    Home page <self>
    tutorial/index
    concepts/index


.. toctree::
    :hidden:
    :maxdepth: 3
    :caption: API

    api
