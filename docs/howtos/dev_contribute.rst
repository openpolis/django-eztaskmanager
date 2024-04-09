Contribute to the Project
-------------------------

Documentation
^^^^^^^^^^^^^

The project documentation, present in the ``docs`` directory, is created using sphinx_.
We adhere to the `guidelines for creating technical documentation`_ proposed by Daniele Procida.

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

Our ``makefile`` has been customized from the original produced by the ``sphinx-quickstart`` script,
and includes a ``livehtml`` target. This facilitates the automatic rebuilding of HTML
output whenever changes to the rst source files are made.

.. code-block:: bash

    make livehtml

Development
^^^^^^^^^^^

The source code is hosted on https://github.com/openpolis/django-eztaskmanager.

There's a suite of unit tests. Run them with:

.. code-block:: bash

    python demoproject/manage.py test

Source code syntax and formatting are validated using flake8.


.. _sphinx: https://www.sphinx-doc.org/en/master/index.html
.. _guidelines for creating technical documentation: https://www.divio.com/blog/documentation/
.. _flake8: https://flake8.pycqa.org/en/latest/