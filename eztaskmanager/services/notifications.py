import re
from typing import Union

from django.apps import apps
from django.core.mail import send_mail
from django.urls import reverse

try:
    import slack_sdk
    SLACK_SDK_AVAILABLE = True
except ImportError:
    SLACK_SDK_AVAILABLE = False

from abc import ABC, abstractmethod

from eztaskmanager.settings import EZTASKMANAGER_BASE_URL

LEVEL_MAPPING = {
    "ok": 0,
    "warnings": 10,
    "errors": 20,
    "failed": 30
}

MESSAGES = {
    0: 'Task *"{task_name}"* invoked at {invocation_time} ' "completed successfully. ",
    10: 'Task *"{task_name}"* invoked at {invocation_time} '
        "completed successfully with *{n_errors}* errors and *{n_warnings}* warnings.",
    20: 'Task *"{task_name}"* invoked at {invocation_time} '
        "completed successfully with *{n_errors}* errors and *{n_warnings}* warnings.",
    30: 'Task *"{task_name}"* invoked at {invocation_time} *failed*.'
}


def get_base_url():
    """
    Retrieve the base URL for the current site.

    Returns:
        str: The base URL for the current site.

    Raises:
        None.

    Examples:
        >>> get_base_url()
        'example.com'
    """
    base_url = re.sub(r"https?://", "", EZTASKMANAGER_BASE_URL)
    return apps.get_app_config("sites").get_current().domain or base_url


class NotificationHandler(ABC):
    """An abstract base class for handling notifications."""

    def __init__(self, level: Union[int, str] = 0):
        self.level = level if isinstance(level, int) else LEVEL_MAPPING.get(level, 0)

    def handle(self, report):
        """Check the result of the report against the established lo level before emitting notifications."""
        result = LEVEL_MAPPING.get(report.invocation_result)

        if result and result >= self.level:
            return self.emit(report)

    @abstractmethod
    def emit(self, report):  # pragma: no cover
        """Abstract method. To be implemented in concrete classes."""
        raise NotImplementedError


class SlackNotificationHandler(NotificationHandler):
    """
    This class is a notification handler that sends notifications to a specified Slack channel using the Slack API.

    Params:
        client (slack_sdk.WebClient): The Slack WebClient object used to interact with the Slack API.
        channel (str): The Slack channel to which the notifications will be sent.
        level (int): The log level at which notifications will be sent.

    Methods:
        emit(report): Sends an email notification based on the given report.
    """

    def __init__(self, token, channel, level):
        if not SLACK_SDK_AVAILABLE:
            raise ImportError('Cannot instantiate SlackNotificationHandler without slack_sdk')
        self.client = slack_sdk.WebClient(token=token)
        self.channel = channel
        super().__init__(level)

    def emit(self, report):
        """Send a Slack notification based on the given report's result."""
        result = LEVEL_MAPPING[report.invocation_result]
        formatted_message = MESSAGES[result].format(
            task_name=report.task.name,
            invocation_time=report.invocation_datetime.strftime("%x %X"),
            n_warnings=report.n_log_warnings,
            n_errors=report.n_log_errors,
        )

        blocks = [
            {"type": "context", "elements": [{"type": "mrkdwn", "text": "django-eztaskmanager", }]},
            {"type": "section", "text": {"type": "mrkdwn", "text": formatted_message, }},
            {"type": "context", "elements": [
                {"type": "mrkdwn",
                 "text": f"<http://{get_base_url()}"
                         f"{reverse('eztaskmanager:live_log_viewer', args=(report.id,))}|Full logs>"},
            ]},
            {"type": "section", "text": {"type": "mrkdwn", "text": "Logs tail:\n" f"```{report.log_tail()}```", }},
        ]

        self.client.chat_postMessage(channel=self.channel, blocks=blocks)


class EmailNotificationHandler(NotificationHandler):
    """
    A class for handling email notifications.

    Inherits from NotificationHandler.

    Attributes:
        from_email (str): The email address to use as the sender of the notification.
        recipients (list[str]): A list of email addresses to send the notification to.
        level (int): The level of the notification.

    Methods:
        emit(report): Sends an email notification based on the given report.

    """

    def __init__(self, from_email, recipients, level):
        self.from_email = from_email
        self.recipients = recipients
        super().__init__(level)

    def emit(self, report):
        """Send an email notification based on the given level."""
        result = LEVEL_MAPPING[report.invocation_result]

        send_mail(
            subject=MESSAGES[result],
            message=MESSAGES[result].format(
                task_name=report.task.name,
                invocation_time=report.invocation_datetime.strftime("%x %X"),
                n_warnings=report.n_log_warnings,
                n_errors=report.n_log_errors,
            ),
            from_email=self.from_email,
            recipient_list=self.recipients,
            fail_silently=True,
        )


def emit_notifications(report):
    """
    Emit notifications for the given report.

    Args:
        report: The report object containing the invocation result.

    Returns:
        None
    """
    if not report.invocation_result:
        return

    handlers = report.get_notification_handlers()
    for handler in handlers.values():
        handler.handle(report)
