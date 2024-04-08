from unittest.mock import MagicMock

from django.test import TestCase
from django.utils import timezone

from eztaskmanager.models import AppCommand, Task, LaunchReport, Log, TaskCategory
from unittest import mock
from eztaskmanager.management.commands.test_command import Command


class AppCommandTestCase(TestCase):

    def setUp(self):
        # creating an instance of the model
        self.appCommand = AppCommand.objects.create(name="test_command", app_name="eztaskmanager")

    @mock.patch('eztaskmanager.models.load_command_class', return_value=Command())
    def test_get_command_class(self, mocked_load_command_class):
        response = self.appCommand.get_command_class()
        mocked_load_command_class.assert_called_once_with(
            app_name='eztaskmanager',
            name='test_command'
        )  # Assert if the function is called once

    @mock.patch('eztaskmanager.models.load_command_class', return_value=MagicMock())
    def test_help_text(self, mock_load_command_class):
        # The text you expect to be written to output
        expected_output = "sample text"

        # Create a mock parser that writes expected text to its 'file' argument when print_help is called
        mock_parser = MagicMock()
        def mock_print_help(file):
            file.write(expected_output)
        mock_parser.print_help = mock_print_help

        # Configure the mocked command class to return the mocked parser
        mock_command_class = mock_load_command_class.return_value
        mock_command_class.create_parser.return_value = mock_parser

        # Now when you call help_text, it should return the content written by the mocked parser
        response = self.appCommand.help_text
        self.assertEqual(response, expected_output)

        mock_load_command_class.assert_called_once()  # Check whether mock_load_command_class() is called

    def test_str(self):
        self.assertEqual(str(self.appCommand), f"{self.appCommand.app_name}: {self.appCommand.name}")


class LaunchReportTestCase(TestCase):
    def setUp(self):
        self.appCommand = AppCommand.objects.create(name="test_command", app_name="eztaskmanager")
        self.task = Task.objects.create(name='Test Task', command=self.appCommand)
        self.launch_report = LaunchReport.objects.create(
            task=self.task,
            invocation_result=LaunchReport.RESULT_OK
        )
        self.first_log = Log.objects.create(
            level="INFO", message="This is an info log",
            timestamp=timezone.now(),
            launch_report=self.launch_report
        )
        self.last_log = Log.objects.create(
            level="ERROR", message="This is a test log",
            timestamp=timezone.now(),
            launch_report=self.launch_report
        )

    def test_get_log_lines(self):
        log_lines = self.launch_report.get_log_lines()
        self.assertEqual(
            log_lines[0],
            f"{self.first_log.timestamp} - {self.first_log.level} - {self.first_log.message}"
        )

    def test_read_log_lines(self):
        log_lines, total_lines = self.launch_report.read_log_lines(1)
        self.assertEqual(
            log_lines[0], f"{self.last_log.timestamp} - {self.last_log.level} - {self.last_log.message}"
        )
        self.assertEqual(total_lines, 2)

    def test_log_tail(self):
        report = self.launch_report.log_tail(1)
        self.assertIn(f"{self.last_log.timestamp} - {self.last_log.level} - {self.last_log.message}", report)

    def test_n_log_lines(self):
        self.assertEqual(self.launch_report.n_log_lines, 2)

    def test_n_log_errors(self):
        self.assertEqual(self.launch_report.n_log_errors, 1)

    def test_n_log_warnings(self):
        self.assertEqual(self.launch_report.n_log_warnings, 0)

    def test_delete(self):
        self.launch_report.delete()
        self.assertEqual(Task.objects.count(), 1)
        self.assertEqual(Log.objects.count(), 0)

    def test_str(self):
        self.assertEqual(
            str(self.launch_report),
            f"LaunchReport {self.launch_report.task.name} {self.launch_report.invocation_result} "
            f"{self.launch_report.invocation_datetime}"
        )


class TaskTestCase(TestCase):
    def setUp(self):
        self.app_command = AppCommand.objects.create(name='Test Command', active=True)
        self.task = Task.objects.create(
            name='Test Task', command=self.app_command,
            repetition_period='day', repetition_rate=2,
            arguments='-f, --firstarg=param1, --secondarg param2, '
                      '--thirdarg=param3a param3b,--fourtharg param4a param4b,'
                      '--fiftharg'
        )
        self.empty_task = Task.objects.create(
            name='Test Task', command=self.app_command,
            repetition_period='day', repetition_rate=2,
            arguments=''
        )
        self.launch_reports = [
            LaunchReport.objects.create(task=self.task, invocation_result=LaunchReport.RESULT_OK)
            for _ in range(5)
        ]

    def test_interval_in_seconds(self):
        self.assertEqual(self.task.interval_in_seconds, 172800)  # Expected to be 2 days in seconds

    def test_args(self):
        result = ['-f', '--fiftharg']  # Arguments without params
        self.assertEqual(self.task.args, result)

    def test_empty_task_args(self):
        result = []
        self.assertEqual(self.empty_task.args, result)

    def test_options(self):
        result = {
            'firstarg': 'param1',
            'secondarg': 'param2',
            'thirdarg': 'param3a param3b',
            'fourtharg': 'param4a param4b'
        }
        self.assertEqual(self.task.options, result)

    def test_empty_task_options(self):
        result = {}
        self.assertEqual(self.empty_task.options, result)

    def test_complete_args(self):
        result = [
            '-f',
            '--firstarg', 'param1', '--secondarg', 'param2',
            '--thirdarg', 'param3a param3b', '--fourtharg', 'param4a param4b',
            '--fiftharg',
        ]
        self.assertEqual(self.task.complete_args, result)

    def test_empty_task_complete_args(self):
        result = []
        self.assertEqual(self.empty_task.complete_args, result)

    def test_prune_reports(self):
        self.task.prune_reports(n=2)  # Try to leave just two reports
        self.assertEqual(LaunchReport.objects.filter(task=self.task).count(), 2)

    def test_str(self):
        self.assertEqual(str(self.task), 'Test Task (idle)')

    def test_compute_cache(self):
        # Let's simulate that a new execution report was created after compute_cache function ran
        latest_report = LaunchReport.objects.create(task=self.task, invocation_result=LaunchReport.RESULT_FAILED)
        self.assertNotEqual(self.task.cached_last_invocation_datetime, latest_report.invocation_datetime)
        self.assertNotEqual(self.task.cached_last_invocation_result, latest_report.invocation_result)

        self.task.compute_cache()  # Run the function

        self.assertEqual(self.task.cached_last_invocation_datetime, latest_report.invocation_datetime)
        self.assertEqual(self.task.cached_last_invocation_result, latest_report.invocation_result)


class LogTestCase(TestCase):
    def setUp(self):
        # First create a LaunchReport instance, as it is a foreign key for Log
        self.app_command = AppCommand.objects.create(name='Test Command', active=True)
        self.task = Task.objects.create(
            name='Test Task', command=self.app_command,
            repetition_period='day', repetition_rate=2,
            arguments='-f, --firstarg=param1, --secondarg param2, '
                      '--thirdarg=param3a param3b,--fourtharg param4a param4b,'
                      '--fiftharg'
        )
        self.launch_report = LaunchReport.objects.create(
            task=self.task,
            invocation_result=LaunchReport.RESULT_OK
        )

        # Then initialise your Log instance here
        self.log = Log.objects.create(
            launch_report=self.launch_report,
            level="INFO",
            message="Test log message"
        )

    def test_str(self):
        self.assertEqual(str(self.log), f'Log {self.log.id}: {self.log.level} at {self.log.timestamp}')


class TaskCategoryTestCase(TestCase):
    def setUp(self):
        # Initialise your TaskCategory instance here
        self.task_category = TaskCategory.objects.create(name="Test Category")

    def test_str(self):
        self.assertEqual(str(self.task_category), self.task_category.name)
