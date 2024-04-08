.. _howto-notifications:

How to enable notifications
---------------------------

The ``notifications system`` enables ``django-eztaskmanager`` to send custom notifications
at the end of tasks execution.
Tasks may be sent according to the specified ``level`` parameter in the handler:

 - ``failed``: whenever failures are trapped during the execution,
 - ``errors`` or ``warnings``: when the execution terminates correctly, but errors or warnings are detected,
 - ``ok``: when everything runs smoothly, just to know.

Thanks to the work of `Gabriele Lucci`_ in django_uwsgi_taskmanager,
the notifications system is *pluggable*. It comes with **email** and **slack**.
Development of a custom subsystem is possible, and a small developer guide is present
in the last paragraph of this section.

.. _Gabriele Lucci: https://github.com/gabrielelucci

To enable the Slack notifications subsystem, you have to first install the
required packages, which are not included by default. To do that, just:

.. code-block:: bash

    pip install django-eztaskmanager[slack]

This will install the ``django-eztaskmanager`` package from PyPI, including the optional slack_sdk_ dependency
required to make Slack notifications work.

Email notifications are instead handled using Django `django.core.mail`_
module, so no further dependencies are needed and they should work out of the box, given you have at
least one `email backend`_ properly
configured.

Then, you have to configure the ``EZTASKMANAGER_NOTIFICATION_HANDLERS`` setting variable
as a dictionary with the chosen handlers.

For example, to set up the slack notification handler:

.. code-block:: python

    EZTASKMANAGER_NOTIFICATION_HANDLERS = {
        "slack": {
            "class": "taskmanager.notifications.SlackNotificationHandler",
            "level": "errors",
            "token": env("EZTASKMANAGER_NOTIFICATIONS_SLACK_TOKEN", default=""),
            "channel": env("EZTASKMANAGER_NOTIFICATIONS_SLACK_CHANNELS", default=""),
        },
    }

with the following env variables set:

- ``EZTASKMANAGER_NOTIFICATIONS_SLACK_TOKEN``, the Slack token as string.
- ``EZTASKMANAGER_NOTIFICATIONS_SLACK_CHANNELS``, a list of strings representing the names or ids of the channels which will receive the notifications.

For the email notification handler:

.. code-block:: python

    EZTASKMANAGER_NOTIFICATION_HANDLERS = {
        "mail": {
            "class": "taskmanager.notifications.MailNotificationHandler",
            "level": "errors",
            "from_email": env("EZTASKMANAGER_NOTIFICATIONS_EMAIL_FROM", default=""),
            "recipients": env("EZTASKMANAGER_NOTIFICATIONS_EMAIL_RECIPIENTS", default=""),
        },
    }

with the following env variables:

- ``EZTASKMANAGER_NOTIFICATIONS_EMAIL_FROM``, the "from address" you want your outgoing notification emails to use.
- ``EZTASKMANAGER_NOTIFICATIONS_EMAIL_RECIPIENTS``, a list of strings representing the recipients of the notifications.

More than one handler can be added. Notifications will be sent to all parties defined.


Developing a custom handler
===========================

The basic notification handler is defined in ``eztaskmanager.notifications.NotificationHandler``,
as an abstract class. All handlers subclass this one.

Handlers class can be created anywhere in the python import path. If found, they will be imported
by the taskmanager application, during the app startup, and registered as active handler.

In order to setup the handler in the settings, a custom dictionary must be created,
just like the two examples above. The dictionary needs to be created, with the
``class`` and ``level`` keys, at least.

The ``class`` key will be popped out of the dictionary and used to instantiate the handler,
with the others keys passed as arguments.

The ``emit_notifications`` method of the ``LaunchReport`` class will call all registered handlers and
emit the notifications.
It is called at the end of ``eztaskmanager.tasks.exec_command_task``.

Dependencies, should they be needed, must be installed separately.

Feel free to create a pull request if you want to add a notification handler directly in the package.

.. _django.core.mail: https://docs.djangoproject.com/en/5.0/topics/email/
.. _email backend: https://docs.djangoproject.com/en/5.0/topics/email/#email-backends
.. _slack_sdk: https://slack.dev/python-slack-sdk/

