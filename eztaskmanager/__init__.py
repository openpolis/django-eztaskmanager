"""Django application to manage async tasks via admin interface."""

# PEP 440 - version number format
VERSION = (0, 4, 3)

# PEP 396 - module version variable
__version__ = ".".join(map(str, VERSION))

default_app_config = "eztaskmanager.apps.EZTaskmanagerConfig"
