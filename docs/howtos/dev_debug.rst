Debugging Tasks
---------------

Debugging can be complex with multiple running components.

Prior to running the development components, a Docker stack must be executed because it's necessary
for Redis to be operational (and Mailhog helpfully tests email notifications).

Two components can be debugged during development:

- The ``runserver``, used for testing the admin application and the livelogviewer view.
- The ``rqworker``, used for testing the wrapper that initiates the tasks.

In the PyCharm IDE, you need to establish three run/debug configurations:

- The Django server configuration, which controls the ``runserver``. A *Before launch* task
is added to this that runs the Docker stack before the `runserver`. This ensures Redis and Mailhog are operational.

    .. image:: /_static/images/runserver_configuration.png
      :width: 800
      :alt: Runserver configuration

- The `rqworker` configuration.

    .. image:: /_static/images/rqworker_configuration.png
      :width: 800
      :alt: RQ Worker configuration

.. note::

    To make a configuration for local Docker compose execution, simply open the file in
PyCharm and click on the double green arrows. This actions `docker compose up` and
creates a temporary run/debug configuration. Save this configuration to reuse it later.

    .. image:: /_static/images/docker_compose.png
      :width: 600
      :alt: Executing docker compose up