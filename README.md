
Django application to manage common django management tasks
*asynchronously*, via the Django admin interface, using either [`RQ`](https://github.com/rq/rq) or 
[`Celery`](https://docs.celeryq.dev/en/stable/index.html).

**eztaskmanager** is a port and an evolution of our previous 
[django-uwsgi-taskmanager](https://github.com/openpolis/django-uwsgi-taskmanager).

Main **features**:

- use standard django management commands as tasks 'templates',
- import available management commands through a meta-management command, as possible templates for tasks,
- start and stop tasks manually via admin,
- schedule point and periodic tasks via django admin,
- use RQ (rq + rq-scheduler) or Celery (celery + celery-beat) for queue management,
- check or download the generated reports/logs,
- live logs streaming view, with filters on errors and warnings for tasks debugging,
- get notifications via Slack or email when a task succeeds or fails.

See full documentation at http://django-eztaskmanager.rtfd.io/

## Installation

1. Install the app with `pip`:

    -  via PyPI:

       `pip install django-eztaskmanager`

    -  or via GitHub:

       `pip install git+https://github.com/openpolis/django-eztaskmanager.git`

2. Add "eztaskmanager" to your `INSTALLED_APPS` setting like this:

    ```python
   
    INSTALLED_APPS = [
        "django.contrib.admin",
        # ...
        "eztaskmanager",
    ]
    ```

3. Run `python manage.py migrate` to create the taskmanager tables.

4. Run `python manage.py collectcommands --excludecore` to import taskmanager commands.

5. Include the taskmanager URLConf (for the log viewers) in your project `urls.py` like this _(optional)_:

    ```python

    from django.contrib import admin
    from django.urls import include, path
    
    urlpatterns = [
        path("admin/", admin.site.urls),
        path('eztaskmanager/', include('eztaskmanager.urls'))
    ]
    ```

6. Set parameters in your settings file as below _(optional)_:

    ```python

    # eztaskmanager
    # EZTASKMANAGER_QUEUE_SERVICE_TYPE = 'RQ'
    # EZTASKMANAGER_N_LINES_IN_REPORT_LOG = 10
    # EZTASKMANAGER_N_REPORTS_INLINE = 10
    # EZTASKMANAGER_SHOW_LOGVIEWER_LINK = True
    # EZTASKMANAGER_USE_FILTER_COLLAPSE = True
    # EZTASKMANAGER_NOTIFICATION_HANDLERS = {}
    # EZTASKMANAGER_BASE_URL = None
    EZTASKMANAGER_NOTIFICATION_HANDLERS = {
        "email-errors": {
            "class": "eztaskmanager.services.notifications.EmailNotificationHandler",
            "level": "failure",
            "from_email": "admin@example.com",
            "recipients": ["admin@example.com", ],
        },
    }
    EZTASKMANAGER_N_LINES_IN_REPORT_LOG = 5
    ```

## Usage

You just need to install `django-eztaskmanager` in your Django Project and run `collectcommands` as described.
Django ezaskmanager will collect all the commands and make them available for asynchronous scheduling in the admin.

If you need a new asynchronous task, just write a standard custom Django command 
using `eztaskmanager.services.logger.LogEnabledCommand` in places of `django.core.management.base.BaseCommand`, 
and synchronize the app. Then go to the admin page and schedule it.

You can disable commands from the admin, and let users (with limited permissions) schedule only the available ones.

> **NOTE**: RQ or Celery workers and schedulers (rq-scheduler or celery-beat) need to be up and running

## Enabling notifications

To enable Slack notifications support for failing tasks, you have to first install the
required packages, which are not included by default. To do that, just:

    pip install django-eztaskmanager[notifications]
    
This will install the `django-eztaskmanager` package from PyPI, including the optional dependencies
required to make Slack notifications work. 

Email notifications are instead handled using Django [`django.core.mail`](https://docs.djangoproject.com/en/5.0/topics/email/) 
module, so no further dependencies are needed and they should work out of the box, given you have at
least one [email backend](https://docs.djangoproject.com/en/5.0/topics/email/#email-backends) properly
configured.

Then, you have to configure the following settings:

- `EZTASKMANAGER_NOTIFICATIONS_SLACK_TOKEN`, which must be set with you own Slack token as string.
- `EZTASKMANAGER_NOTIFICATIONS_SLACK_CHANNELS`, a list of strings representing the names or ids of the channels which will receive the notifications.
- `EZTASKMANAGER_NOTIFICATIONS_EMAIL_FROM`, the "from address" you want your outgoing notification emails to use.
- `EZTASKMANAGER_NOTIFICATIONS_EMAIL_RECIPIENTS`, a list of strings representing the recipients of the notifications.

### The demo tutorial (RQ)
Following this tutorial, it will be possible to install, configure and use **eztaskmanager** for a
simple demo django project running in developer mode, with the RQ engine.

Clone the project from github onto your hard disk:

```bash
    git clone https://github.com/openpolis/django-eztaskmanager
    cd django-eztaskmanager
```

There is a basic Django project under the ``demoproject`` directory, set to use ``eztaskmanager``.

```
    demoproject/
    ├── demoproject/
    │   ├── __init__.py
    │   └── asgi.py
    │   ├── settings.py
    │   ├── test_settings.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── manage.py
    ├── static/
    └── docker-compose-local.yml
```

#### Try the demo project

As a **pre-requisite**, a Redis server should be up and running on the default port 6379.
Follow the instructions_, or if you use docker_, just run ``docker compose -f docker-compose-local.yml``.

Enter the ``demoproject`` directory, then create and activate the virtual environments:

```bash
    $ cd demoproject
    $ mkdir -p venv
    $ python3 -m venv venv
    $ source venv/bin/activate
```

Install **eztaskmanager**, this will install all needed dependencies (django, redis, django-rq, rq-scheduler,...):

```bash
    (venv) $ pip install django-eztaskmanager
```

Then execute this commands to setup the server in development mode, the rq worker and the scheduler:

```bash
    (venv) $ python manage.py migrate  # create tables in the DB (default sqlite will do)
    (venv) $ python manage.py createsuperuser # take note of username and password for login
    (venv) $ python manage.py collectcommands --excludecore  # collect basic commands from the eztaskmanager package
    (venv) $ python manage.py runserver  # django app server on port 8000
    (venv) $ python manage.py rqworker  # rq worker to execute enqueued tasks
    (venv) $ python manage.py rqscheduler --verbosity=3  # rq scheduler to enqueue periodic tasks
```

Visit http://127.0.0.1:8000/admin/


## Copyright

**Django uWSGI taskmanager** is an application to manage async tasks via admin interface, using uWSGI spooler.

Copyright (c) 2024 Guglielmo Celata, Fondazione Openpolis

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
