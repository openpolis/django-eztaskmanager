.. Django eztaskmanager documentation master file, created by
   sphinx-quickstart on Sun Dec 29 13:37:22 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Django eztaskmanager Documentation
====================================================

**eztaskmanager** is a Django application designed to initiate standard Django management tasks *asynchronously*. This is done through a conventional Django administrative interface, utilizing either `RQ`_ or `Celery`_.

Designed to empower *non-technical users* with the ability to manage and monitor asynchronous task scheduling without the need for developer assistance or team member intervention, **eztaskmanager** is both a port and evolution from our earlier django-uwsgi-taskmanager_. Optimized for cross-functional independence, it operates separately from the application server (like gunicorn, uvicorn, etc.) and leverages Redis, a common caching solution that is routinely part of the technical stack.

**eztaskmanager** comes loaded with key **features**:

- Usage of standard Django management commands as task 'templates'.
- Capability to import available management commands through a meta-management command, serving as potential templates for tasks.
- Manual initiation and stopping of tasks via an administrative interface.
- Ability to schedule singular and periodic tasks using the Django admin system.
- Compatibility with RQ (rq + rq-scheduler) or Celery (celery + celery-beat) for queue management.
- Functionality to verify or download generated reports/logs.
- Live log streaming display, with error and warning filters for task debugging.
- Notification capabilities via Slack or email on task completion or failure.

.. _RQ: https://github.com/rq/rq
.. _Celery: https://docs.celeryq.dev/en/stable/index.html
.. _django-uwsgi-taskmanager: https://github.com/openpolis/django-uwsgi-taskmanager


.. toctree::
   :maxdepth: 2
   :caption: Contents

   getstarted
   howtos/index
   reference/index
   discussions

