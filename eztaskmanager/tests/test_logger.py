import logging

from django.test import TestCase
from unittest.mock import patch
from eztaskmanager.services.logger import verbosity2loglevel, LoggerEnabledCommand, DatabaseLogHandler


class TestModule(TestCase):
    def test_verbosity2loglevel(self):
        # Test that verbosity2loglevel correctly maps verbosity levels
        self.assertEqual(verbosity2loglevel(0), logging.ERROR)
        self.assertEqual(verbosity2loglevel(1), logging.WARNING)
        self.assertEqual(verbosity2loglevel(2), logging.INFO)
        self.assertEqual(verbosity2loglevel(3), logging.DEBUG)
        # Test that unspecified verbosity levels default to WARNING
        self.assertEqual(verbosity2loglevel(4), logging.WARNING)

    def test_logger_enabled_command(self):
        with patch('eztaskmanager.services.logger.logging') as mock_logging:
            cmd = LoggerEnabledCommand()
            cmd.execute(verbosity=2, force_color=False, no_color=False, skip_checks=False)
            # Test that logger's level is correctly set
            self.assertEqual(cmd.logger.level, logging.INFO)
            # Test that logger is correctly attached
            self.assertEqual(mock_logging.getLogger().__name__, cmd.logger.__name__)

    @patch('ezmanager.services.logger.logging.Handler')
    def test_database_log_handler(self, mock_handler):
        with patch('emanager.services.Log') as mock_log:
            handler = DatabaseLogHandler("launch_report_1")
            # Test that handler is correctly initialized
            self.assertEqual(handler.launch_report_id, "launch_report_1")
            # Test that emit correctly creates a log entry
            test_record = logging.LogRecord("test_name", logging.ERROR, None, None, "test_msg", None, None)
            handler.emit(test_record)
            mock_log.assert_called_once()
