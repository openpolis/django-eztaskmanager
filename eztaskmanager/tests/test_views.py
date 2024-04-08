from unittest.mock import MagicMock, patch

from django.http import JsonResponse
from django.test import TestCase, RequestFactory
from django.utils import timezone

from eztaskmanager.models import LaunchReport, AppCommand, Task, Log
from eztaskmanager.views import LogViewerView, AjaxReadLogLines, LiveLogViewerView


class LogViewerViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = LogViewerView()

    @patch('eztaskmanager.models.LaunchReport')  # replace with the actual path to your Report model
    def test_get_report_lines(self, mock_report):
        mock_lines = ['log line 1', 'log line 2', 'log line 3']
        mock_report.get_log_lines.return_value = mock_lines

        result = self.view.get_report_lines(mock_report)

        self.assertEqual(result, mock_lines)

    @patch.object(LaunchReport, 'objects')
    def test_get_context_data(self, mock_objects):
        # Arrange
        expected_log_lines = ['ERROR line', 'WARNING line', 'NORMAL line']

        mock_report = mock_objects.get.return_value
        mock_report.pk = 1
        mock_report.n_log_errors = 1
        mock_report.n_log_warnings = 1
        mock_report.n_log_lines = len(expected_log_lines)
        mock_report.get_log_lines.return_value = expected_log_lines

        request = self.factory.get(f'/logviewer/{mock_report.pk}?log_level=all')  # replace with your actual url
        request.session = {}  # Django requires session to be manually added
        view = LogViewerView()
        view.setup(request)

        # Act
        context = view.get_context_data(**{'pk': 1})  # replace with the actual scheme of your kwargs

        # Assert
        self.assertEqual(context['log_all']['lines'], expected_log_lines)
        # perform more `assertEqual` tests here to validate the rest of your context

    @patch.object(LaunchReport, 'objects')
    def test_get_context_data_no_log(self, mock_objects):
        report_pk = 1

        mock_objects.get.side_effect = LaunchReport.DoesNotExist
        expected_error_message = f"No log for the report {report_pk}."

        request = self.factory.get(f'/logviewer{report_pk}?log_level=all')  # replace with your actual url
        request.session = {}  # Django requires session to be manually added
        view = LogViewerView()
        view.setup(request)

        # Act
        context = view.get_context_data(**{'pk': 1})  # replace with the actual scheme of your kwargs

        # Assert
        self.assertEqual(context['log_txt'], expected_error_message)
        self.assertEqual(context['log_levels'], ["warning", "error"])
        self.assertEqual(context['selected_log_level'], "all")

    @patch.object(LaunchReport, 'objects')
    def test_get_context_data_no_level(self, mock_objects):
        # Arrange
        expected_log_lines = ['ERROR line', 'WARNING line', 'NORMAL line']

        mock_report = mock_objects.get.return_value
        mock_report.pk = 1
        mock_report.n_log_errors = 1
        mock_report.n_log_warnings = 1
        mock_report.n_log_lines = len(expected_log_lines)
        mock_report.get_log_lines.return_value = expected_log_lines

        request = self.factory.get(f'/logviewer/{mock_report.pk}?log_level=pippo')  # replace with your actual url
        request.session = {}  # Django requires session to be manually added
        view = LogViewerView()
        view.setup(request)

        # Act
        context = view.get_context_data(**{'pk': 1})  # replace with the actual scheme of your kwargs

        # Assert
        self.assertEqual(context['log_txt'], 'The available levels are: ERROR or WARNING')
        # perform more `assertEqual` tests here to validate the rest of your context


class LiveLogViewerViewTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = LiveLogViewerView()



    @patch.object(LaunchReport, 'objects')
    def test_get_context_data(self, mock_objects):
        mock_report = mock_objects.get.return_value
        mock_report.pk = 1
        mock_report.task = MagicMock()
        mock_report.task.id = 1
        mock_report.task.arguments = "--limit=30,--verbosity=3"

        request = self.factory.get(f'/livelogviewer/{mock_report.pk}?log_level=all')
        request.session = {}
        self.view.setup(request)

        context = self.view.get_context_data(pk=1)

        # Asserts

        # Validate that our "report" and "task" context variables exist
        self.assertIn('report', context)
        self.assertIn('task', context)
        self.assertIn('task_arguments', context)

        # Validate the value of our context variables
        self.assertEqual(context['report'], mock_report)
        self.assertEqual(context['task'], mock_report.task)
        self.assertEqual(context['task_arguments'], mock_report.task.arguments.split(','))

    @patch.object(LaunchReport, 'objects')
    def test_non_existing_report_get_context_data(self, mock_objects):
        mock_report = mock_objects.get.return_value
        mock_report.pk = 1
        mock_report.task = MagicMock()
        mock_report.task.id = 1
        mock_report.task.arguments = "--limit=30,--verbosity=3"

        # When get method is called with nonexistent pk, raise DoesNotExist exception
        def side_effect(*args, **kwargs):
            if kwargs.get('pk') == mock_report.pk:
                return mock_report
            else:
                raise LaunchReport.DoesNotExist
        mock_objects.get.side_effect = side_effect

        request = self.factory.get(f'/livelogviewer/{mock_report.pk + 1}?log_level=all')
        request.session = {}
        self.view.setup(request)

        context = self.view.get_context_data(pk=2)

        self.assertNotIn('report', context)
        self.assertNotIn('task', context)
        self.assertNotIn('task_arguments', context)


class TestAjaxReadLogLines(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.view = AjaxReadLogLines()
        # Assuming you have a model instance to be queried
        self.app_command = AppCommand.objects.create(app_name='Test', name='Test command', active=False)
        self.task = Task.objects.create(
            command=self.app_command, name='Test task',
            arguments="--verbosity=3,--limit=30",
            status = Task.STATUS_IDLE
        )
        self.launch_report = LaunchReport.objects.create(
            task=self.task,
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

    def test_render_to_response_with_existing_report(self):
        request = self.factory.get('/dummy_url', {'offset': 5})  # assuming offset is 5
        self.view.request = request
        context = {'pk': self.launch_report.pk}
        response = self.view.render_to_response(context)
        expected_response = JsonResponse({
            'new_log_lines': [],  # replace with expected log lines
            'task_status': self.launch_report.task.status,
            'log_size': self.launch_report.n_log_lines
        })
        self.assertEqual(response.content, expected_response.content)

    def test_render_to_response_with_non_existing_report(self):
        request = self.factory.get('/dummy_url', {'offset': 5})  # assuming offset is 5
        self.view.request = request
        non_existent_pk = self.launch_report.pk + 1
        context = {'pk': non_existent_pk}
        response = self.view.render_to_response(context)
        expected_response = JsonResponse({
            'new_log_lines': ["No log for the report {pk}.".format(pk=non_existent_pk), ],
            'task_status': None,
            'log_size': 0
        })
        self.assertEqual(response.content, expected_response.content)
