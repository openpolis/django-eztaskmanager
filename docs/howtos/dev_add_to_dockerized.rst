Integrating Django-eztaskmanager into a Dockerized Stack
---------------------------------------------------------

This guide is intended for **developers** aiming to integrate **eztaskmanager** into their Django application
within a *dockerized* setup. This specific case applies to an **rq** queue manager.

The illustrated ``docker-compose.yml`` depicts portions of a stack that operates an app via the **web** service.

The integration requires two more services: **rqworker** and **rqscheduler**

These three —together: the web, rqworker, and rqscheduler-, need to spring from the same Django app image while holding
different start-up commands. Consequently, a consolidated shared environment gets defined, reused in the
``docker_compose.yml`` stack blueprint:


.. code-block:: yaml

    version: "3.7"

    # Define anchor for reusable parts
    x-shared-environment: &shared-environment
      environment:
        - POSTGRES_HOST
        - POSTGRES_PORT
        - POSTGRES_DB
        - POSTGRES_USER
        - POSTGRES_PASSWORD
        - DATABASE_URL=postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}
        - DJANGO_DEBUG
        - REDIS_URL
        - CI_COMMIT_SHA
        - ...

    services:
      web:
        <<: *shared-environment
        container_name: ${COMPOSE_PROJECT_NAME}_web
        restart: always
        build:
          context: .
          dockerfile: ./compose/production/django/Dockerfile
        image: acme/${COMPOSE_PROJECT_NAME}_production_django
        deploy:
          replicas: 4
        expose:
          - "5000"
        depends_on:
          - postgres
          - redis
        command: /start
        networks:
          - default
          - gw

      rqworker:
        <<: *shared-environment
        restart: unless-stopped
        build:
          context: .
          dockerfile: ./compose/production/django/Dockerfile
        image: acme/${COMPOSE_PROJECT_NAME}_production_django
        deploy:
          replicas: 2
        depends_on:
          - postgres
          - redis
        command: /start-rqworker
        networks:
          - default
          - gw

      rqscheduler:
        <<: *shared-environment
        restart: unless-stopped
        build:
          context: .
          dockerfile: ./compose/production/django/Dockerfile
        image: acme/${COMPOSE_PROJECT_NAME}_production_django
        deploy:
          replicas: 2
        depends_on:
          - postgres
          - redis
        command: /start-rqscheduler
        networks:
          - default
          - gw

      postgres:
        container_name: ${COMPOSE_PROJECT_NAME}_postgres
        restart: unless-stopped
        build:
          context: .
          dockerfile: ./compose/production/postgres/Dockerfile
        image: acme/${COMPOSE_PROJECT_NAME}_production_postgres
        volumes:
          - postgres_data:/var/lib/postgresql/data
          - postgres_data_backups:/backups
        environment:
          - POSTGRES_HOST=${POSTGRES_HOST}
          - POSTGRES_PORT=${POSTGRES_PORT}
          - POSTGRES_DB=${POSTGRES_DB}
          - POSTGRES_USER=${POSTGRES_USER}
          - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}

      redis:
        container_name: ${COMPOSE_PROJECT_NAME}_redis
        volumes:
          - redis_data:/data
        restart: always
        image: redis:latest

.. note::

    The YAML file is only partially shown here for explanatory purposes.
    Adjustments might be needed based on your specific application.

.. note::

    In the ``docker_compose.yml`` example, a reference to ``./compose/production/django`` indicates the
    residence of the django image's ``Dockerfile``, paired with the bash scripts launching the server,
    the worker, and the scheduler operations.

    The ``start`` command would resemble:

    .. code-block:: bash

        #!/bin/bash
        exec /usr/local/bin/gunicorn config.wsgi --bind 0.0.0.0:5000 --chdir=/app

    The ``start-rqworker`` command would be:

    .. code-block:: bash

        #!/bin/bash
        python manage.py rqworker default --with-scheduler

    And, for ``start-rqscheduler``:

    .. code-block:: bash

        #!/bin/bash
        python manage.py rqscheduler --verbosity=2


As for **Celery**, the same logic would apply,
only the starting commands would change, using something similar to:

.. code-block:: bash

    #!/bin/sh

    celery -A proj worker -l info --concurrency 2
    celery -A proj beat -l info ..concurrency 2
