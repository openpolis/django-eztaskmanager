import logging

from django.core.management.base import BaseCommand

from eztaskmanager.models import Log


def verbosity2loglevel(verbosity):
    """Map verbosity level to logging level."""
    level_map = {
        0: logging.ERROR,
        1: logging.WARNING,
        2: logging.INFO,
        3: logging.DEBUG
    }
    # Get the corresponding logging level or default to WARNING
    logging_level = level_map.get(verbosity, logging.WARNING)
    return logging_level


class LoggerEnabledCommand(BaseCommand):
    """This class is a subclass of BaseCommand that adds logging functionality to the execute method."""

    logger = None

    def execute(self, *args, **kwargs):
        """Override the BaseCommand method, adding stream and Database handlers, if not existing."""
        verbosity = kwargs.get('verbosity', 1)

        # Get the logger
        logger = logging.getLogger(__name__)
        logger.setLevel(verbosity2loglevel(verbosity))

        # Remove launch_report_id from options
        launch_report_id = kwargs.pop('launch_report_id', None)

        if launch_report_id:
            # If launch_report_id is provided, use DatabaseLogHandler, avoid duplicates for embedded commands
            if not any(isinstance(handler, DatabaseLogHandler) for handler in logger.handlers):
                logger.addHandler(DatabaseLogHandler(launch_report_id))

        # Always use the default handler, avoid duplicates for embedded commands
        if not any(isinstance(handler, logging.StreamHandler) for handler in logger.handlers):
            logger.addHandler(logging.StreamHandler())

        # Set the logger as an instance variable
        self.logger = logger

        super().execute(*args, **kwargs)

    def create_parser(self, prog_name, subcommand, **kwargs):
        """Create a parser."""
        parser = super().create_parser(prog_name, subcommand, **kwargs)
        parser.add_argument('--launch_report_id', type=int, nargs='?',
                            help='Launch report ID for task logging')
        return parser


class DatabaseLogHandler(logging.Handler):
    """
    A handler class that logs messages to a database.

    This class extends the logging.Handler class and provides functionality to log messages to a database.
    Each log message is saved as a Log object in the database with the launch report level, and message attributes.

    Usage:
        log_handler = DatabaseLogHandler("launch_report_1")
        logger.addHandler(log_handler)
        logger.error("An error occurred")
    """

    def __init__(self, launch_report_id):
        logging.Handler.__init__(self)
        self.launch_report_id = launch_report_id

    def emit(self, record):
        """Implement the method to send the log message to the DB."""
        log_entry = Log(
            launch_report_id=self.launch_report_id,
            level=record.levelname,
            message=self.format(record),
        )
        log_entry.save()
