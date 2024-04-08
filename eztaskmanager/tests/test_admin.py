from datetime import timedelta
from unittest.mock import patch, Mock, call, MagicMock

from bs4 import BeautifulSoup
from django.contrib import messages
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.core.management import call_command
from django.test import TestCase, RequestFactory, Client
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe

import eztaskmanager
from eztaskmanager.admin import AppCommandAdmin, LaunchReportAdmin, LaunchReportInline, convert_to_local_dt, TaskAdmin
from eztaskmanager.models import AppCommand, LaunchReport, Task, TaskCategory
from eztaskmanager.settings import EZTASKMANAGER_N_LINES_IN_REPORT_LOG


class MockSuperUser:
    is_active = True
    is_staff = False
    pk = 1

    def has_perm(self, perm):
        return True


request = RequestFactory().get('/admin')
request.user = MockSuperUser()


class AppCommandAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = AppCommandAdmin(AppCommand, self.site)

    def test_has_add_permission(self):
        self.assertEqual(self.admin.has_add_permission(request), False)

    def test_changeform_view(self):
        app_command = AppCommand.objects.create(app_name='Test', name='Test', active=False)
        response = self.admin.changeform_view(request, object_id=str(app_command.id))
        self.assertEqual(response.context_data['show_save_and_continue'], False)
        self.assertEqual(response.context_data['show_save'], False)


class LaunchReportAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = LaunchReportAdmin(LaunchReport, self.site)
        self.app_command = AppCommand.objects.create(app_name='Test', name='Test command', active=False)
        self.task = Task.objects.create(command=self.app_command, name='Test task')
        self.launch_report = LaunchReport.objects.create(task=self.task)

    def test_has_add_permission(self):
        self.assertEqual(
            self.admin.has_add_permission(request), False,
            "has_add_permission doesn't work as expected"
        )

    def test_changeform_view(self):
        response = self.admin.changeform_view(request, object_id=str(self.launch_report.id))
        self.assertEqual(response.context_data['show_save_and_continue'], False)
        self.assertEqual(response.context_data['show_save'], False)

    @patch('eztaskmanager.models.LaunchReport.log_tail')
    @patch.object(eztaskmanager.admin, 'EZTASKMANAGER_SHOW_LOGVIEWER_LINK', new=True)
    def test_log_tail_html_with_link(self, mock_log_tail):
        n_max_lines = EZTASKMANAGER_N_LINES_IN_REPORT_LOG
        expected_log_tail = "\n".join(str(i) for i in range(n_max_lines))
        mock_log_tail.return_value = expected_log_tail

        returned_html = self.admin.log_tail_html(self.launch_report)

        mock_log_tail.assert_called_once_with(n_max_lines)

        expected_html = (
            f"<pre>{expected_log_tail}\n\n"
            f"<a href='{reverse('eztaskmanager:live_log_viewer', args=(self.launch_report.pk,))}' "
            f"target='_blank'>Show the log messages</a></pre>"
        )
        self.assertEqual(returned_html, mark_safe(expected_html))

    @patch('eztaskmanager.models.LaunchReport.log_tail')
    @patch.object(eztaskmanager.admin, 'EZTASKMANAGER_SHOW_LOGVIEWER_LINK', new=False)
    def test_log_tail_html_without_link(self, mock_log_tail):
        n_max_lines = EZTASKMANAGER_N_LINES_IN_REPORT_LOG
        expected_log_tail = "\n".join(str(i) for i in range(n_max_lines))
        mock_log_tail.return_value = expected_log_tail

        returned_html = self.admin.log_tail_html(self.launch_report)

        mock_log_tail.assert_called_once_with(n_max_lines)

        expected_html = f"<pre>{expected_log_tail}</pre>"
        self.assertEqual(returned_html, mark_safe(expected_html))


class LaunchReportInlineTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = LaunchReportInline(LaunchReport, self.site)

    def test_has_add_permission(self):
        self.assertEqual(
            self.admin.has_add_permission(request), False,
            "has_add_permission doesn't work as expected"
        )


class TaskInlineTest(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        call_command('collectstatic', interactive=False)

    def setUp(self):
        self.client = Client()
        self.superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin_password')
        self.app_command = AppCommand.objects.create(app_name='Test', name='Test command', active=False)
        self.task_category = TaskCategory.objects.create(name='Test category')

    def fetch_element_text(self, task):
        response = self.client.get(reverse('admin:eztaskmanager_taskcategory_change', args=(task.id,)))
        html = response.content
        soup = BeautifulSoup(html, 'html.parser')
        element = soup.select('#task_set-0 > td:nth-child(4)')
        self.assertTrue(element, "Element not found via CSS selector")
        return element[0].text.strip()

    def test_new_idle_status_str(self):
        task = Task.objects.create(
            name='Test Task', category=self.task_category,
            command=self.app_command, status=Task.STATUS_IDLE
        )
        self.client.force_login(self.superuser)
        element_text = self.fetch_element_text(task)
        assert "idle/-/-" in element_text, "Element does not contain the string"

    def test_executed_idle_task_status_str(self):
        task = Task.objects.create(
            name='Test Task', category=self.task_category,
            command=self.app_command, status=Task.STATUS_IDLE
        )
        # Let's simulate that a new execution report was created after compute_cache function ran
        now = timezone.now()
        _ = LaunchReport.objects.create(
            task=task,
            invocation_result=LaunchReport.RESULT_OK,
            invocation_datetime=now
        )
        now_dt = convert_to_local_dt(now)
        task.compute_cache()  # compute cached values

        self.client.force_login(self.superuser)
        element_text = self.fetch_element_text(task)
        last_invocation_s = f"{now_dt}: {LaunchReport.RESULT_OK} - 0E, 0W"
        assert f"idle/{last_invocation_s}/-" in element_text, "Element does not contain the string"

    def test_new_scheduled_status_str(self):
        scheduled_time = timezone.now() + timedelta(days=1)
        scheduled_dt = convert_to_local_dt(scheduled_time)
        task = Task.objects.create(
            name='Test Task', category=self.task_category,
            command=self.app_command, status=Task.STATUS_SCHEDULED,
            cached_next_ride=scheduled_time
        )
        self.client.force_login(self.superuser)
        element_text = self.fetch_element_text(task)
        assert f"scheduled/-/{scheduled_dt}" in element_text, "Element does not contain the string"

class ConvertToLocalDtTest(TestCase):
    def test_convert_to_local_dt_exception_handling(self):
        # Pass a non-datetime value
        result = convert_to_local_dt("not a datetime")

        # Verify that exception handling worked and an empty string is returned
        self.assertEqual(result, "")


class TaskAdminTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.admin = TaskAdmin(Task, self.site)

    @patch.object(messages, "add_message")
    @patch('eztaskmanager.services.queues.get_task_service')
    def test_launch_tasks(self, mock_get_task_service, mock_add_message):
        # Setup
        mock_service = mock_get_task_service.return_value

        task1 = Mock(spec=Task)
        task2 = Mock(spec=Task)
        queryset = [task1, task2]

        # Call the method
        self.admin.launch_tasks(request, queryset)

        # Check the interactions of the mocks
        mock_get_task_service.assert_called_once()
        assert mock_service.add.call_args_list == [call(task1), call(task2)]
        mock_add_message.assert_called_once_with(
            request, messages.INFO, f'{len(queryset)} tasks launched.', extra_tags='', fail_silently=False
        )

    @patch.object(messages, "add_message")
    @patch('eztaskmanager.services.queues.get_task_service')
    def test_stop_tasks(self, mock_get_task_service, mock_add_message):
        # Setup
        mock_service = mock_get_task_service.return_value

        task1 = Mock(spec=Task)
        task2 = Mock(spec=Task)
        queryset = [task1, task2]

        # Call the method
        self.admin.stop_tasks(request, queryset)

        # Check the interactions of the mocks
        mock_get_task_service.assert_called_once()
        assert mock_service.remove.call_args_list == [call(task1), call(task2)]
        mock_add_message.assert_called_once_with(
            request, messages.INFO, f'{len(queryset)} tasks stopped.', extra_tags='', fail_silently=False
        )

    def test_repetition_no_rate_or_period(self):
        command = AppCommand.objects.create(app_name='testapp', name='testcmd')
        task = Task.objects.create(
            command=command,
        )
        self.assertEqual(self.admin.repetition(task), "-")

    def test_repetition_with_rate_and_period(self):
        command = AppCommand.objects.create(app_name='testapp', name='testcmd')
        task = Task.objects.create(
            command=command,
            repetition_rate=5, repetition_period=Task.REPETITION_PERIOD_DAY
        )
        self.assertEqual(self.admin.repetition(task), "5 day")

    def test_name_desc(self):
        command = AppCommand.objects.create(app_name='testapp', name='testcmd')
        task = Task.objects.create(
            command=command,
            name='Test command', note='A test note'
        )
        assert task.name in self.admin.name_desc(task)
        assert task.note in self.admin.name_desc(task)

    def test_name_empty_desc(self):
        command = AppCommand.objects.create(app_name='testapp', name='testcmd')
        task = Task.objects.create(
            command=command,
            name='Test command', note=''
        )
        assert task.name in self.admin.name_desc(task)
        assert 'title=""' in self.admin.name_desc(task)

    def test_invocation(self):
        command = AppCommand.objects.create(app_name='testapp', name='testcmd')
        task = Task.objects.create(
            command=command,
            arguments="--limit=90,--verbosity=3"
        )
        assert task.command.name in self.admin.invocation(task)
        assert ' '.join(task.arguments.split(',')) in self.admin.invocation(task)

    @patch.object(eztaskmanager.admin, 'EZTASKMANAGER_SHOW_LOGVIEWER_LINK', new=True)
    def test_last_result_with_link(self):
        command = AppCommand.objects.create(app_name='testapp', name='testcmd')
        task = Task.objects.create(
            command=command,
            arguments="--limit=90,--verbosity=3"
        )
        last_report = LaunchReport.objects.create(
            task=task,
            invocation_result=LaunchReport.RESULT_OK
        )
        task.compute_cache()  # compute cached values

        assert LaunchReport.RESULT_OK.lower() in self.admin.last_result_with_logviewer_link(task).lower()
        last_report_url = reverse("eztaskmanager:live_log_viewer", args=(last_report.id,))
        assert last_report_url in self.admin.last_result_with_logviewer_link(task)

    @patch.object(eztaskmanager.admin, 'EZTASKMANAGER_SHOW_LOGVIEWER_LINK', new=False)
    def test_last_result_without_link(self):
        command = AppCommand.objects.create(app_name='testapp', name='testcmd')
        task = Task.objects.create(
            command=command,
            arguments="--limit=90,--verbosity=3"
        )
        last_report = LaunchReport.objects.create(
            task=task,
            invocation_result=LaunchReport.RESULT_OK
        )
        task.compute_cache()  # compute cached values

        assert LaunchReport.RESULT_OK.upper() in self.admin.last_result_with_logviewer_link(task)
        last_report_url = reverse("eztaskmanager:live_log_viewer", args=(last_report.id,))
        assert last_report_url not in self.admin.last_result_with_logviewer_link(task)

    def test_last_invocation_datetime(self):
        command = AppCommand.objects.create(app_name='testapp', name='testcmd')
        task = Task.objects.create(
            command=command,
            arguments="--limit=90,--verbosity=3"
        )
        invocation_dt = timezone.now() - timedelta(days=1)
        invocation_str = convert_to_local_dt(invocation_dt)
        last_report = LaunchReport.objects.create(task=task)
        last_report.invocation_datetime = invocation_dt
        last_report.save()
        task.compute_cache()

        self.assertEqual(invocation_str, self.admin.cached_last_invocation_datetime(task))

    def test_empty_last_invocation_datetime(self):
        command = AppCommand.objects.create(app_name='testapp', name='testcmd')
        task = Task.objects.create(
            command=command,
            arguments="--limit=90,--verbosity=3"
        )
        task.compute_cache()

        self.assertEqual(self.admin.cached_last_invocation_datetime(task), "-")


class TaskAdminButtonsTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.admin = TaskAdmin(Task, AdminSite())

    @patch('eztaskmanager.services.queues.get_task_service')
    def test_response_change_start_task(self, mocked_service):
        request = self.factory.post('/dummyurl/', {'_start-task': 'Start+task'})
        request.user = MockSuperUser()
        request.session = 'session'
        request._messages = FallbackStorage(request)
        task = MagicMock()  # assuming Task instance
        service = MagicMock()

        mocked_service.return_value = service
        self.admin.response_change(request, task)

        service.add.assert_called_once_with(task)

    @patch('eztaskmanager.services.queues.get_task_service')
    def test_response_change_stop_task(self, mocked_service):
        request = self.factory.post('/dummyurl/', {'_stop-task': 'some value'})
        request.user = MockSuperUser()
        request.session = 'session'
        request._messages = FallbackStorage(request)
        task = MagicMock()  # assuming Task instance
        service = MagicMock()

        mocked_service.return_value = service
        self.admin.response_change(request, task)

        service.remove.assert_called_once_with(task)

    @patch('eztaskmanager.services.queues.get_task_service')
    def test_response_change_without_start_or_stop_task(self, mocked_service):
        request = self.factory.post('/dummyurl/', {'some-other-field': 'Some value'})
        request.user = MockSuperUser()
        request.session = 'session'
        request._messages = FallbackStorage(request)
        task = MagicMock()  # assuming Task instance
        service = MagicMock()

        mocked_service.return_value = service
        self.admin.response_change(request, task)

        service.add.assert_not_called()
        service.remove.assert_not_called()


class TaskAdminBulkDeleteTest(TestCase):
    def setUp(self):
        self.site = AdminSite()
        self.superuser = get_user_model().objects.create_superuser('admin', 'admin@admin.com', 'admin_password')

        self.del_request = RequestFactory().post('/admin', data={'post': 'yes'})  # changed from .get to .post
        self.del_request.user = self.superuser

    @patch.object(messages, "add_message")
    def test_bulk_delete_mixin(self, mock_add_message):
        command1 = AppCommand.objects.create(app_name='testapp', name='testcmd1')
        command2 = AppCommand.objects.create(app_name='testapp', name='testcmd2')
        task1 = Task.objects.create(name="task1", command=command1)  # supply appropriate arguments
        task2 = Task.objects.create(name="task2", command=command2)  # for your Task model here

        admin = TaskAdmin(Task, self.site)

        # test get_actions
        actions = admin.get_actions(self.del_request)
        self.assertTrue('delete_selected' in actions)

        # test action_safe_bulk_delete
        admin.action_safe_bulk_delete(self.del_request, Task.objects.all())

        self.assertEqual(Task.objects.count(), 0)

        mock_add_message.assert_called_once_with(
            self.del_request, messages.SUCCESS,
            f'Successfully deleted 2 Tasks.', extra_tags='', fail_silently=False
        )
