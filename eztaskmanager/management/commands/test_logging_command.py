"""Test logging command."""

from django.core import management

from eztaskmanager.services.logger import LoggerEnabledCommand


class Command(LoggerEnabledCommand):
    """Command for testing logger."""

    help = "Command for testing logger"
    verbosity = None
    logger = None

    def add_arguments(self, parser):
        """Add arguments method."""
        parser.add_argument(
            "--debug", default="ND", dest="debug", help="Test debug output"
        )
        parser.add_argument(
            "--info", default="ND", dest="info", help="Test info output"
        )
        parser.add_argument(
            "--warning", default="ND", dest="warning", help="Test warning output"
        )
        parser.add_argument(
            "--error", default="ND", dest="error", help="Test error output"
        )
        parser.add_argument(
            "--test-embedded",
            action="store_true",
            dest="test_embedded",
            help="Test embedded tasks launches",
        )

    def handle(self, *args, **options):
        """Handle method."""
        if options["debug"] != "ND":
            self.logger.debug(str(options["debug"]))
        if options["info"] != "ND":
            self.logger.info(str(options["info"]))
        if options["warning"] != "ND":
            self.logger.warning(str(options["warning"]))
        if options["error"] != "ND":
            self.logger.error(str(options["error"]))
        if options["test_embedded"]:
            management.call_command(
                "test_logging_command",
                verbosity=options.get('verbosity', 1),
                info="Embedded info message",
                warning="Embedded warning message",
            )
