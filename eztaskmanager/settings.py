"""Define settings for the taskmanager app."""

from typing import Any, Dict, Optional

from django.conf import settings as django_project_settings

EZTASKMANAGER_QUEUE_SERVICE_TYPE: str = getattr(
    django_project_settings, "EZTASKMANAGER_QUEUE_SERVICE_TYPE", 'RQ'
)

EZTASKMANAGER_BASE_URL: Optional[str] = getattr(
    django_project_settings, "EZTASKMANAGER_BASE_URL", None
)

EZTASKMANAGER_N_LINES_IN_REPORT_LOG: int = getattr(
    django_project_settings, "EZTASKMANAGER_N_LINES_IN_REPORT_LOG", 10
)

EZTASKMANAGER_N_REPORTS_INLINE: int = getattr(
    django_project_settings, "EZTASKMANAGER_N_REPORTS_INLINE", 5
)

EZTASKMANAGER_SHOW_LOGVIEWER_LINK: bool = getattr(
    django_project_settings, "EZTASKMANAGER_SHOW_LOGVIEWER_LINK", True
)

EZTASKMANAGER_USE_FILTER_COLLAPSE: bool = getattr(
    django_project_settings, "EZTASKMANAGER_USE_FILTER_COLLAPSE", True
)

EZTASKMANAGER_NOTIFICATION_HANDLERS: Dict[str, Dict[str, Any]] = getattr(
    django_project_settings, "EZTASKMANAGER_NOTIFICATION_HANDLERS", {}
)
"""
Configure notification handlers.

Example:

    EZTASKMANAGER_NOTIFICATION_HANDLERS = {
        "slack": {
            "class": "eztaskmanager.services.notifications.SlackNotificationHandler",
            "level": "warnings",
            "token": "<token>",
            "channel": "id-or-name-of-channel",
        },
        "slack-all": {
            "class": "eztaskmanager.services.notifications.SlackNotificationHandler",
            "level": "ok",
            "token": "<token>",
            "channel": "id-or-name-of-channel",
        },
        "slack-failures": {
            "class": "eztaskmanager.services.notifications.SlackNotificationHandler",
            "level": "failure",
            "token": "<token>",
            "channel": "id-or-name-of-channel",
        },
        "email-failures": {
            "class": "eztaskmanager.services.notifications.EmailNotificationHandler",
            "level": "failure",
            "from_email": "admin@example.com",
            "recipients": ["admin@example.com",],
        },
    }

NOTE: Email feature relies on Django built-in `send_mail()`.
Thus, an email backend (e.g. SMTP) should be configured by setting these options:
- EMAIL_HOST
- EMAIL_PORT
- EMAIL_HOST_USER
- EMAIL_HOST_PASSWORD

"""
