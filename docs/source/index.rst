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

* Code compactness; from the same dataclass declaration, we derive a
  configuration parser, a command-line usage description and a Sphinx
  documentation block.

* Compatibility with IDEs

* Error reporting: Instead of crashing at the first parse error, configpile
  collects all the errors encountered and reports all of them.

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
