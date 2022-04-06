Step 6: Final calculator script
===============================

In this step, we add a function that returns a legacy :class:`argparse.ArgumentParser`.

We put the script under a ``if __name__ == "__main__":`` guard.

We also had to move the 
`sphinx-autodoc <https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html>`_
style parameter documentation strings to the ``help`` keyword argument to avoid problems with the
Sphinx import style (which happens when using the ``:filename:`` directive). In standard projects,
where the scripts are part of a Python package imported with the ``:module:`` directive, this
problem should not happen.

We now demonstrate the `argparse <https://sphinx-argparse.readthedocs.io/en/stable/>`_
Sphinx extension.

The directive is instantiated like this::

  .. argparse::
    :module: configpile.calculator
    :func: argument_parser

and gives the result below.

Documentation in Sphinx
-----------------------
.. argparse::
  :module: configpile.calculator
  :func: argument_parser

Code
----

.. literalinclude:: ../../../examples/calculator6.py
