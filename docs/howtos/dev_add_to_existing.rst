Integrating django-eztaskmanager into an existing project
---------------------------------------------------------

This guide is designed for **developers** who wish to incorporate `django-eztaskmanager`
into their existing Django project.

0.  Install the application using `pip`:

    Via **PyPI**:

    .. code-block::

        pip install django-eztaskmanager

    Or directly from **GitHub**:

    .. code-block::

        pip install git+https://github.com/openpolis/django-eztaskmanager.git

1.  Include "eztaskmanager" in your `INSTALLED_APPS` setting as follows:

    .. code-block:: python

        INSTALLED_APPS = [
            "django.contrib.admin",
            # ...,
            "eztaskmanager",
        ]

2. Install and configure 'django-rq' and 'django-scheduler' or 'celery' and 'celery-beats' if they are not already included in your project.

3. Run ``python manage.py migrate`` to generate the eztaskmanager tables.

4. Execute the ``collectcommands`` management task to create taskmanager commands [#excludecore]_:

    .. code-block:: bash

        python manage.py collectcommands --excludecore

5. Include the `eztaskmanager` URL configuration in your project's `urls.py` file:

    .. code-block:: python

        from django.contrib import admin
        from django.urls import path, include

        urlpatterns = [
            path('admin/', admin.site.urls),
            path('django-rq/', include('django_rq.urls')),
            path('eztaskmanager/', include('eztaskmanager.urls'))
        ]

6. Configure parameters in your settings file as delineated below *(optional)*. Uncommented settings represent default values:

    .. code-block:: python

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
        # EZTASKMANAGER_SHOW_LOGVIEWER_LINK = False

7. Follow the :ref:`howto-notifications` guide to set up notifications *(optional)*.


.. rubric:: Footnotes
.. [#excludecore] Using `excludecore` prevents fetching of core Django tasks.
