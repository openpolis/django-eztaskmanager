Contribute to the Project
-------------------------

Documentation
^^^^^^^^^^^^^

The project documentation, present in the ``docs`` directory, is created using sphinx_. We adhere to the `guidelines for creating technical documentation`_ proposed by Daniele Procida.

To contribute to the documentation, ensure that your virtual environment has the following packages installed:

.. code-block::

    sphinx
    sphinx-django-command
    sphinx-rtd-theme
    sphinx-autobuild
    pyembed-rst

To build the documentation, navigate to the ``docs`` directory and run the following commands:

.. code-block:: bash

    make clean
    make html

Our ``makefile`` has been customized from the original produced by the ``sphinx-quickstart`` script, and includes a ``livehtml`` target. This facilitates the automatic rebuilding of HTML output whenever changes to the rst source files are made.

.. code-block:: bash

    make livehtml

Development
^^^^^^^^^^^

The source code is hosted on https://github.com/openpolis/django-eztaskmanager.

Run tests with:

.. code-block:: bash

    python demo/manage.py test

Source code syntax and formatting are validated using black_.


.. _sphinx: https://www.sphinx-doc.org/en/master/index.html
.. _guidelines for creating technical documentation: https://www.divio.com/blog/documentation/
.. _black: https://black.readthedocs.io/en/stable/