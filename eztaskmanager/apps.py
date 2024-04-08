"""Configure taskmanager app."""
from pydoc import locate
from typing import Dict, Type

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

from eztaskmanager.settings import EZTASKMANAGER_NOTIFICATION_HANDLERS


class EZTaskmanagerConfig(AppConfig):
    """eztaskmanager app configuration."""

    name = "eztaskmanager"
    verbose_name = _("eztaskmanager")

    notification_handlers: Dict[str, "NotificationHandler"] = {}  # noqa: F821

    def _register_notification_handlers(self) -> None:
        """
        Register notification handlers for the eztaskmanager object.

        This method initializes and stores instances of the notification handlers
        based on the provided configuration in the EZTASKMANAGER_NOTIFICATION_HANDLERS
        dictionary.

        Args:
            self: The eztaskmanager object.

        Returns:
            None.
        """
        from eztaskmanager.services.notifications import NotificationHandler

        for name, handler in EZTASKMANAGER_NOTIFICATION_HANDLERS.items():
            handler_class: Type[NotificationHandler] = locate(handler.pop("class"))
            if handler_class:
                instance = handler_class(**handler)
                if instance:
                    self.notification_handlers[name] = instance

    def ready(self) -> None:
        """Run stuff when Django starts."""
        self._register_notification_handlers()
