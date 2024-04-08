.. Django eztaskmanager documentation master file, created by
   sphinx-quickstart on Sun Dec 29 13:37:22 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

django-eztaskmanager documentation
==================================

**django-eztaskmanager** is a Django application designed to initiate standard Django management tasks *asynchronously*.
This is done through a conventional Django administrative interface, using either `RQ`_ or, in the near future,
`Celery`_.

Introducing django-eztaskmanager – a tool designed to put the control of managing and monitoring
asynchronous tasks into the hands of non-technical users. It's both an evolution and upgrade from
our previous django-uwsgi-taskmanager_.

The key change is that django-eztaskmanager operates independently from the application server,
like gunicorn or uvicorn. This means it doesn't get in the way of your application's processes.
Moreover, it's built to integrate seamlessly with Redis, a caching solution that's likely
part of your current tech stack, for a fit so comfortable you'll hardly notice it's there.

This tool provides a hands-off experience for developers and an empowering one for non-technical users,
bridging the gap between the two.

**django-eztaskmanager** comes loaded with key **features**:

- usage of standard Django management commands as task *templates*;
- capability to import existing management commands through a meta-management command;
- manual starting and stopping of tasks via an administrative interface;
- ability to schedule singular and periodic tasks using the Django admin system;
- compatibility with RQ (rq + rq-scheduler) or Celery (celery + celery-beat) for queue management;
- verification or download of generated reports/logs;
- live log streaming display, with error and warning filters for task debugging;
- notification capabilities via email or Slack on task completion or failure.

.. _RQ: https://github.com/rq/rq
.. _Celery: https://docs.celeryq.dev/en/stable/index.html
.. _django-uwsgi-taskmanager: https://github.com/openpolis/django-uwsgi-taskmanager

.. note::

   Right now, **django-eztaskmanager** is built to play nice with RQ (Redis Queue).
   It does the job, and does it well. But I know some of you out there swear by Celery, and I hear you.
   It's on my radar and I'm knee-deep in code working to get it integrated.

   So, keep an eye out for updates!

.. toctree::
   :maxdepth: 2
   :caption: Contents

   getstarted
   howtos/index
   reference/index
   discussions

