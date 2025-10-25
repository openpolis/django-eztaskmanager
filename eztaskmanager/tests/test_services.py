# Unittest Test case
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

import eztaskmanager
from eztaskmanager.models import Task, LaunchReport
from eztaskmanager.services.notifications import SlackNotificationHandler, LEVEL_MAPPING, MESSAGES, \
    EmailNotificationHandler, get_base_url, emit_notifications

from eztaskmanager.services.queues import get_task_service, TaskQueueException
tsq_imported_module = None
try:
    from eztaskmanager.services.queues import RQTaskQueueService
    tsq_imported_module = 'rq'
except ImportError:
    try:
        from eztaskmanager.services.queues import CeleryTaskQueueService
        tsq_imported_module = 'celery'
    except ImportError:
        raise ImportError('Could not import a TaskQueueService: celery or django-rq must be installed')


class GetTaskServiceTest(TestCase):

    @patch('django_rq.get_queue', return_value=MagicMock())
    @patch('django_rq.get_scheduler', return_value=MagicMock())
    @patch('eztaskmanager.services.queues.EZTASKMANAGER_QUEUE_SERVICE_TYPE', new='RQ')
    def test_get_task_service_with_rq(self, mock_get_scheduler, mock_get_queue):
        """
        Test get_task_service function for 'RQ' service type
        """
        if tsq_imported_module == 'rq':
            service = get_task_service()

            # Assert that RQTaskQueueService instance is returned when 'RQ' is the type
            self.assertIsInstance(service, RQTaskQueueService)

            mock_get_queue.assert_called_once_with('default')
            mock_get_scheduler.assert_called_once_with('default', interval=60)
            self.assertIsInstance(
                service.queue, MagicMock
            )
            self.assertIsInstance(
                service.scheduler, MagicMock
            )

    @patch('eztaskmanager.services.queues.EZTASKMANAGER_QUEUE_SERVICE_TYPE', new='Celery')
    def test_get_task_service_with_celery(self):
        """
        Test get_task_service function for non 'RQ' service type
        """
        if tsq_imported_module == 'celery':
            service = get_task_service()

            # Assert that CeleryTaskQueueService instance is returned when type is not 'RQ'
            self.assertIsInstance(service, CeleryTaskQueueService)


class TestRQTaskQueueService(TestCase):

    @patch('django_rq.get_queue', return_value=MagicMock())
    @patch('django_rq.get_scheduler', return_value=MagicMock())
    @patch('eztaskmanager.services.run_management_command')
    @patch('eztaskmanager.services.queues.RQTaskQueueService.fetch_job_with_next_time')
    def test_add_non_periodic_task(
            self,
            mock_fetch_job_with_next_time, mock_run_management_command,
            mock_get_scheduler, mock_get_queue
    ):
        if tsq_imported_module == 'rq':
            # Create the instance of the RQTaskQueueService
            service = RQTaskQueueService()

            # Create a mock Task instance
            mock_task = MagicMock()
            mock_task.scheduling = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
            mock_task.scheduling_utc = timezone.make_aware(
                datetime.strptime(mock_task.scheduling, "%Y-%m-%d %H:%M:%S")
            )
            mock_task.interval_in_seconds = None
            mock_task.is_periodic = False
            mock_task.id = 1

            # mock fetch_job_with_next_time to return a demonstration value
            mock_fetch_job_with_next_time.return_value = ('Demo Ride', 'Demo time')

            # mock run_management_command to return a demonstration value
            mock_run_management_command.return_value = 'Demo Value'

            # determine the return value of scheduler.schedule and queue.enqueue
            mock_rq_enqueued_job = MagicMock(id='001-002-003-004')
            service.scheduler.enqueue_at.return_value = mock_rq_enqueued_job

            # Call the method
            service.add(mock_task)

            # Assert the methods were called with the right parameters
            service.scheduler.enqueue_at.assert_called_once_with(
                mock_task.scheduling_utc,
                mock_run_management_command, mock_task.id
            )

            # Assert that the task has been assigned the correct attributes
            self.assertEqual(mock_task.scheduled_job_id, mock_rq_enqueued_job.id)
            self.assertEqual(mock_task.status, Task.STATUS_SCHEDULED)
            self.assertEqual(mock_task.cached_next_ride, mock_fetch_job_with_next_time.return_value[1])

            # If the task does not contain the schedule attribute, the queue.enqueue method should be called
            mock_task.scheduling = None
            service.add(mock_task)
            service.queue.enqueue.assert_called_once_with(mock_run_management_command, mock_task.id)

    @patch('django_rq.get_queue', return_value=MagicMock())
    @patch('django_rq.get_scheduler', return_value=MagicMock())
    @patch('eztaskmanager.services.run_management_command')
    @patch('eztaskmanager.services.queues.RQTaskQueueService.fetch_job_with_next_time')
    def test_add_periodic_task(
            self,
            mock_fetch_job_with_next_time, mock_run_management_command,
            mock_get_scheduler, mock_get_queue
    ):
        if tsq_imported_module == 'rq':

            # Create the instance of the RQTaskQueueService
            service = RQTaskQueueService()

            # Create a mock Task instance
            mock_task = MagicMock()
            mock_task.scheduling = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
            mock_task.scheduling_utc = timezone.make_aware(
                datetime.strptime(mock_task.scheduling, "%Y-%m-%d %H:%M:%S")
            )
            mock_task.interval_in_seconds = 86400
            mock_task.is_periodic = True
            mock_task.id = 1

            # mock fetch_job_with_next_time to return a demonstration value
            mock_fetch_job_with_next_time.return_value = ('Demo Ride', 'Demo time')

            # mock run_management_command to return a demonstration value
            mock_run_management_command.return_value = 'Demo Value'

            # determine the return value of scheduler.schedule and queue.enqueue
            mock_rq_scheduled_job = MagicMock(id='001-001-001-001')
            mock_rq_enqueued_job = MagicMock(id='002-002-002-002')
            service.scheduler.schedule.return_value = mock_rq_scheduled_job
            service.queue.enqueue.return_value = mock_rq_enqueued_job

            # Call the method
            service.add(mock_task)

            # Assert the methods were called with the right parameters
            service.scheduler.schedule.assert_called_once_with(
                mock_task.scheduling_utc,
                mock_run_management_command, [mock_task.id],
                interval=mock_task.interval_in_seconds,
                result_ttl=int(1.5 * mock_task.interval_in_seconds)
            )

            # Assert that the task has been assigned the correct attributes
            self.assertEqual(mock_task.scheduled_job_id, mock_rq_scheduled_job.id)
            self.assertEqual(mock_task.status, Task.STATUS_SCHEDULED)
            self.assertEqual(mock_task.cached_next_ride, mock_fetch_job_with_next_time.return_value[1])

            # If the task does not contain the schedule attribute, the queue.enqueue method should be called
            mock_task.scheduling = False
            service.add(mock_task)
            service.queue.enqueue.assert_called_once_with(mock_run_management_command, mock_task.id)

    @patch('django_rq.get_queue', return_value=MagicMock())
    @patch('django_rq.get_scheduler', return_value=MagicMock())
    @patch('eztaskmanager.services.run_management_command')
    @patch('eztaskmanager.services.queues.RQTaskQueueService.fetch_job_with_next_time')
    def test_add_with_exception(
            self,
            mock_fetch_job_with_next_time, mock_run_management_command,
            mock_get_scheduler, mock_get_queue
    ):
        if tsq_imported_module == 'rq':
            # Setup
            service = RQTaskQueueService()
            mock_task = MagicMock()
            mock_task.scheduling = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
            mock_task.scheduling_utc = timezone.make_aware(
                datetime.strptime(mock_task.scheduling, "%Y-%m-%d %H:%M:%S")
            )
            mock_run_management_command.return_value = 'Demo Value'
            mock_fetch_job_with_next_time.return_value = ('Demo Ride', 'Demo time')

            # Call the method and assert it raises the expected exception
            with self.assertRaises(TaskQueueException) as context:
                service.add(mock_task)

            # Assert the exception message is as expected
            self.assertTrue('It is not possible to schedule tasks in the past' in str(context.exception))

    @patch('django_rq.get_scheduler', return_value=MagicMock())
    @patch('eztaskmanager.services.queues.RQTaskQueueService.fetch_job_with_next_time')
    def test_remove(self, mock_fetch_job_with_next_time, mock_get_scheduler):
        if tsq_imported_module == 'rq':
            # Create the instance of the RQTaskQueueService
            service = RQTaskQueueService()

            # Create a mock Task instance
            mock_task = MagicMock()
            mock_task.id = 1
            mock_task.scheduled_job_id = 'job-id'

            mock_job = MagicMock(id='job-id')
            mock_fetch_job_with_next_time.return_value = (mock_job, 'next_time')

            # Call the method
            service.remove(mock_task)

            # Assert the methods were called with the right parameters
            mock_fetch_job_with_next_time.assert_called_once_with(mock_task)

            # Assert the methods were called with the right parameters
            service.scheduler.cancel.assert_called_once_with(mock_job)

            # Assert the task attributes are correctly updated
            self.assertEqual(mock_task.scheduled_job_id, None)
            self.assertEqual(mock_task.cached_next_ride, None)
            self.assertEqual(mock_task.status, Task.STATUS_IDLE)
            mock_task.save.assert_called_once()

    @patch('django_rq.get_scheduler', return_value=MagicMock())
    @patch('eztaskmanager.services.queues.RQTaskQueueService.fetch_job_with_next_time')
    def test_remove_non_existing_job(self, mock_fetch_job_with_next_time, mock_get_scheduler):
        if tsq_imported_module == 'rq':
            # Create the instance of the RQTaskQueueService
            service = RQTaskQueueService()

            # Create a mock Task instance in Started status
            mock_task = MagicMock()
            mock_task.scheduled_job_id = 'job-id'
            mock_task.cached_next_ride = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d %H:%M:%S")
            mock_task.status = Task.STATUS_STARTED

            # mock the return value of fetch_job_with_next_time
            # no job is found (there's some sort of condition)
            mock_fetch_job_with_next_time.return_value = (None, None)

            # Call the method
            service.remove(mock_task)

            # Assert the methods were called with the right parameters
            mock_fetch_job_with_next_time.assert_called_once_with(mock_task)

            # Assert scheduler.cancel was not called
            service.scheduler.cancel.assert_not_called()

            # Assert the task attributes were reset
            # The task status is now Idle
            assert not mock_task.scheduled_job_id
            assert not mock_task.cached_next_ride
            assert mock_task.status == Task.STATUS_IDLE
            mock_task.save.assert_called()

    @patch('django_rq.get_scheduler', return_value=MagicMock())
    def test_fetch_job_with_next_time_job_exists(self, mock_get_scheduler):
        if tsq_imported_module == 'rq':
            # Create the instance of the RQTaskQueueService
            service = RQTaskQueueService()

            # Create a mock task
            mock_task = MagicMock()
            mock_task.scheduled_job_id = 'job-id'

            # mock the return value of scheduler.get_jobs
            mock_job = MagicMock(id='job-id')
            next_time = datetime.now() + timedelta(days=1)
            service.scheduler.get_jobs.return_value = [(mock_job, next_time)]

            # Call the method
            job, next_run_time = service.fetch_job_with_next_time(mock_task)

            # Assert the method returns the correct job and next_time
            self.assertEqual(job, mock_job)
            self.assertEqual(next_run_time, timezone.make_aware(next_time, timezone=timezone.timezone.utc))

    @patch('django_rq.get_scheduler', return_value=MagicMock())
    def test_fetch_job_with_next_time_job_not_exists(self, mock_scheduler):
        if tsq_imported_module == 'rq':
            # Create the instance of the RQTaskQueueService
            service = RQTaskQueueService()

            # Create a mock task
            mock_task = MagicMock()
            mock_task.scheduled_job_id = 'job_id'

            # mock the return value of scheduler.get_jobs
            mock_scheduler.get_jobs.return_value = [(MagicMock(id='other_job_id'), 'next_time')]

            # Call the method
            job, next_time = service.fetch_job_with_next_time(mock_task)

            # Assert the method returns None, None if the job is not found
            self.assertEqual(job, None)
            self.assertEqual(next_time, None)


class TestSlackNotificationHandler(TestCase):

    @patch('slack_sdk.WebClient')
    def test_init(self, mock_webclient):
        # Setup
        token = 'token'
        channel = '#test-channel'
        level = 2

        # Execution
        handler = SlackNotificationHandler(token, channel, level)

        # Assertion
        mock_webclient.assert_called_with(token=token)
        self.assertEqual(handler.channel, channel)
        self.assertEqual(handler.level, level)

    @patch('eztaskmanager.services.notifications.get_base_url')
    @patch('slack_sdk.WebClient')
    def test_handle(self, mock_webclient, mock_get_base_url):
        # Setup
        token = 'token'
        channel = '#test-channel'
        level = 2
        handler = SlackNotificationHandler(token, channel, level)

        mock_get_base_url.return_value = "test.com"
        mock_webclient_instance = mock_webclient.return_value
        mock_report = MagicMock()
        mock_report.task.name = 'test_task'
        mock_report.invocation_datetime.strftime.return_value = 'test_time'
        mock_report.n_log_warnings = 1
        mock_report.n_log_errors = 2
        mock_report.id = 1
        mock_report.log_tail.return_value = 'log_tail'
        mock_report.invocation_result = LaunchReport.RESULT_ERRORS

        result = LEVEL_MAPPING[mock_report.invocation_result]

        formatted_message = MESSAGES[result].format(
            task_name=mock_report.task.name,
            invocation_time=mock_report.invocation_datetime.strftime("%x %X"),
            n_warnings=mock_report.n_log_warnings,
            n_errors=mock_report.n_log_errors,
        )

        expected_channel = channel
        expected_blocks = [
            {"type": "context", "elements": [{"type": "mrkdwn", "text": "django-eztaskmanager"}]},
            {"type": "section", "text": {"type": "mrkdwn", "text": formatted_message}},
            {"type": "context", "elements": [{"type": "mrkdwn", "text": "<http://test.com{}|Full logs>".format(
                reverse('eztaskmanager:live_log_viewer', args=(mock_report.id,)))}]},
            {"type": "section",
             "text": {"type": "mrkdwn", "text": "Logs tail:\n```{}```".format(mock_report.log_tail())}},
        ]

        # Execution
        handler.handle(mock_report)

        # Assertion
        mock_webclient_instance.chat_postMessage.assert_called_with(channel=expected_channel, blocks=expected_blocks)


class TestEmailNotificationHandler(TestCase):

    def test_init(self):
        # Setup
        from_email = 'from@email.it'
        recipients = ['addr_1@example.com', 'addr_2@example.com']
        level = 2

        # Execution
        handler = EmailNotificationHandler(from_email, recipients, level)

        # Assertion
        self.assertEqual(handler.from_email, from_email)
        self.assertEqual(handler.recipients, recipients)
        self.assertEqual(handler.level, level)

    @patch('eztaskmanager.services.notifications.send_mail')
    def test_handle(self, mock_send_mail):
        # Setup
        from_email = 'from@email.it'
        recipients = ['addr_1@example.com', 'addr_2@example.com']
        level = 2
        handler = EmailNotificationHandler(from_email, recipients, level)

        mock_report = MagicMock()
        mock_report.task.name = 'test_task'
        mock_report.invocation_datetime.strftime.return_value = 'test_time'
        mock_report.n_log_warnings = 1
        mock_report.n_log_errors = 2
        mock_report.id = 1
        mock_report.log_tail.return_value = 'log_tail'
        mock_report.invocation_result = LaunchReport.RESULT_ERRORS

        # Execution
        handler.handle(mock_report)

        result = LEVEL_MAPPING[mock_report.invocation_result]

        # Assertion
        mock_send_mail.assert_called_with(
            subject=MESSAGES[result],
            message=MESSAGES[result].format(
                task_name=mock_report.task.name,
                invocation_time=mock_report.invocation_datetime.strftime("%x %X"),
                n_warnings=mock_report.n_log_warnings,
                n_errors=mock_report.n_log_errors,
            ),
            from_email=handler.from_email,
            recipient_list=handler.recipients,
            fail_silently=True
        )


class TestGetBaseUrl(TestCase):

    @patch('eztaskmanager.services.notifications.apps.get_app_config')
    @patch.object(eztaskmanager.services.notifications, 'EZTASKMANAGER_BASE_URL', new="https://test2.com")
    def test_get_base_url_returns_value(self, mock_get_app_config):
        # Arrange
        test_domain = 'test1.com'
        mock_get_app_config.return_value.get_current.return_value.domain = test_domain

        # Act
        result = get_base_url()

        # Assert
        self.assertEqual(test_domain, result)

    @patch('eztaskmanager.services.notifications.apps.get_app_config')
    @patch.object(eztaskmanager.services.notifications, 'EZTASKMANAGER_BASE_URL', new="https://test2.com")
    def test_get_base_url_does_not_return_value(self, mock_get_app_config):
        # Arrange
        mock_get_app_config.return_value.get_current.return_value.domain = None

        # Act
        result = get_base_url()

        # Assert
        self.assertEqual("test2.com", result)


class TestRQTaskQueueServiceDeduplication(TestCase):
    """
    Test suite for task deduplication logic in RQTaskQueueService.

    These tests verify that the service properly handles duplicate scheduling
    scenarios that can occur during stack restarts, CI/CD deployments, or
    manual re-activation of tasks.
    """

    @patch('django_rq.get_queue', return_value=MagicMock())
    @patch('django_rq.get_scheduler', return_value=MagicMock())
    @patch('eztaskmanager.services.run_management_command')
    @patch('eztaskmanager.services.queues.RQTaskQueueService.fetch_job_with_next_time')
    def test_add_task_without_existing_job_id(
            self,
            mock_fetch_job_with_next_time, mock_run_management_command,
            mock_get_scheduler, mock_get_queue
    ):
        """
        Test that a task without an existing scheduled_job_id is added normally
        without triggering deduplication logic.
        """
        if tsq_imported_module == 'rq':
            service = RQTaskQueueService()

            mock_task = MagicMock()
            mock_task.scheduled_job_id = None  # No existing job
            mock_task.scheduling = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
            mock_task.scheduling_utc = timezone.make_aware(
                datetime.strptime(mock_task.scheduling, "%Y-%m-%d %H:%M:%S")
            )
            mock_task.is_periodic = False
            mock_task.id = 1

            mock_rq_job = MagicMock(id='new-job-001')
            service.scheduler.enqueue_at.return_value = mock_rq_job
            mock_fetch_job_with_next_time.return_value = ('job', 'next_time')

            service.add(mock_task)

            # Assert scheduler.cancel was NOT called (no deduplication needed)
            service.scheduler.cancel.assert_not_called()

            # Assert new job was created
            service.scheduler.enqueue_at.assert_called_once()
            self.assertEqual(mock_task.scheduled_job_id, 'new-job-001')

    @patch('django_rq.get_queue', return_value=MagicMock())
    @patch('django_rq.get_scheduler', return_value=MagicMock())
    @patch('eztaskmanager.services.run_management_command')
    @patch('eztaskmanager.services.queues.RQTaskQueueService.fetch_job_with_next_time')
    def test_add_task_with_existing_valid_job_id(
            self,
            mock_fetch_job_with_next_time, mock_run_management_command,
            mock_get_scheduler, mock_get_queue
    ):
        """
        Test that a task with an existing scheduled_job_id that still exists in Redis
        will have the old job cancelled before creating a new one.
        """
        if tsq_imported_module == 'rq':
            service = RQTaskQueueService()

            mock_task = MagicMock()
            mock_task.scheduled_job_id = 'old-job-123'  # Existing job
            mock_task.name = 'test_task'
            mock_task.id = 42
            mock_task.scheduling = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
            mock_task.scheduling_utc = timezone.make_aware(
                datetime.strptime(mock_task.scheduling, "%Y-%m-%d %H:%M:%S")
            )
            mock_task.is_periodic = False

            mock_new_job = MagicMock(id='new-job-456')
            service.scheduler.enqueue_at.return_value = mock_new_job
            mock_fetch_job_with_next_time.return_value = ('job', 'next_time')

            # Mock successful cancellation (job exists in Redis)
            service.scheduler.cancel.return_value = None

            service.add(mock_task)

            # Assert old job was cancelled
            service.scheduler.cancel.assert_called_once_with('old-job-123')

            # Assert new job was created
            service.scheduler.enqueue_at.assert_called_once()
            self.assertEqual(mock_task.scheduled_job_id, 'new-job-456')

    @patch('django_rq.get_queue', return_value=MagicMock())
    @patch('django_rq.get_scheduler', return_value=MagicMock())
    @patch('eztaskmanager.services.run_management_command')
    @patch('eztaskmanager.services.queues.RQTaskQueueService.fetch_job_with_next_time')
    def test_add_task_with_orphaned_job_id(
            self,
            mock_fetch_job_with_next_time, mock_run_management_command,
            mock_get_scheduler, mock_get_queue
    ):
        """
        Test that a task with an existing scheduled_job_id that no longer exists
        in Redis (orphaned) will handle the cancellation exception gracefully
        and still create a new job.
        """
        if tsq_imported_module == 'rq':
            service = RQTaskQueueService()

            mock_task = MagicMock()
            mock_task.scheduled_job_id = 'orphaned-job-999'  # Job doesn't exist in Redis
            mock_task.name = 'test_task'
            mock_task.id = 99
            mock_task.scheduling = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
            mock_task.scheduling_utc = timezone.make_aware(
                datetime.strptime(mock_task.scheduling, "%Y-%m-%d %H:%M:%S")
            )
            mock_task.is_periodic = False

            mock_new_job = MagicMock(id='new-job-789')
            service.scheduler.enqueue_at.return_value = mock_new_job
            mock_fetch_job_with_next_time.return_value = ('job', 'next_time')

            # Mock failed cancellation (job doesn't exist in Redis)
            service.scheduler.cancel.side_effect = Exception("Job not found in Redis")

            # Should not raise exception
            service.add(mock_task)

            # Assert cancellation was attempted
            service.scheduler.cancel.assert_called_once_with('orphaned-job-999')

            # Assert new job was still created despite cancellation failure
            service.scheduler.enqueue_at.assert_called_once()
            self.assertEqual(mock_task.scheduled_job_id, 'new-job-789')

    @patch('django_rq.get_queue', return_value=MagicMock())
    @patch('django_rq.get_scheduler', return_value=MagicMock())
    @patch('eztaskmanager.services.run_management_command')
    @patch('eztaskmanager.services.queues.RQTaskQueueService.fetch_job_with_next_time')
    def test_add_periodic_task_with_existing_job_id(
            self,
            mock_fetch_job_with_next_time, mock_run_management_command,
            mock_get_scheduler, mock_get_queue
    ):
        """
        Test that a periodic task with an existing scheduled_job_id properly
        cancels the old job before creating a new periodic schedule.
        """
        if tsq_imported_module == 'rq':
            service = RQTaskQueueService()

            mock_task = MagicMock()
            mock_task.scheduled_job_id = 'old-periodic-job-111'
            mock_task.name = 'periodic_task'
            mock_task.id = 55
            mock_task.scheduling = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
            mock_task.scheduling_utc = timezone.make_aware(
                datetime.strptime(mock_task.scheduling, "%Y-%m-%d %H:%M:%S")
            )
            mock_task.is_periodic = True
            mock_task.interval_in_seconds = 3600

            mock_new_job = MagicMock(id='new-periodic-job-222')
            service.scheduler.schedule.return_value = mock_new_job
            mock_fetch_job_with_next_time.return_value = ('job', 'next_time')

            service.add(mock_task)

            # Assert old job was cancelled
            service.scheduler.cancel.assert_called_once_with('old-periodic-job-111')

            # Assert new periodic job was created
            service.scheduler.schedule.assert_called_once()
            self.assertEqual(mock_task.scheduled_job_id, 'new-periodic-job-222')

    @patch('django_rq.get_queue', return_value=MagicMock())
    @patch('django_rq.get_scheduler', return_value=MagicMock())
    @patch('eztaskmanager.services.run_management_command')
    @patch('eztaskmanager.services.queues.RQTaskQueueService.fetch_job_with_next_time')
    def test_multiple_rapid_rescheduling(
            self,
            mock_fetch_job_with_next_time, mock_run_management_command,
            mock_get_scheduler, mock_get_queue
    ):
        """
        Test that multiple rapid re-scheduling attempts properly handle
        deduplication each time without issues.
        """
        if tsq_imported_module == 'rq':
            service = RQTaskQueueService()

            mock_task = MagicMock()
            mock_task.name = 'rapid_reschedule_task'
            mock_task.id = 77
            mock_task.scheduling = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
            mock_task.scheduling_utc = timezone.make_aware(
                datetime.strptime(mock_task.scheduling, "%Y-%m-%d %H:%M:%S")
            )
            mock_task.is_periodic = False

            mock_fetch_job_with_next_time.return_value = ('job', 'next_time')

            # First scheduling (no existing job)
            mock_task.scheduled_job_id = None
            mock_job1 = MagicMock(id='job-001')
            service.scheduler.enqueue_at.return_value = mock_job1
            service.add(mock_task)
            self.assertEqual(mock_task.scheduled_job_id, 'job-001')

            # Second scheduling (has existing job from first scheduling)
            mock_job2 = MagicMock(id='job-002')
            service.scheduler.enqueue_at.return_value = mock_job2
            service.add(mock_task)
            self.assertEqual(mock_task.scheduled_job_id, 'job-002')

            # Third scheduling (has existing job from second scheduling)
            mock_job3 = MagicMock(id='job-003')
            service.scheduler.enqueue_at.return_value = mock_job3
            service.add(mock_task)
            self.assertEqual(mock_task.scheduled_job_id, 'job-003')

            # Assert scheduler.cancel was called twice (second and third time)
            self.assertEqual(service.scheduler.cancel.call_count, 2)

    @patch('django_rq.get_queue', return_value=MagicMock())
    @patch('django_rq.get_scheduler', return_value=MagicMock())
    @patch('eztaskmanager.services.run_management_command')
    def test_immediate_execution_with_existing_job_id(
            self,
            mock_run_management_command,
            mock_get_scheduler, mock_get_queue
    ):
        """
        Test that immediate execution (no scheduling) DOES trigger deduplication
        if task has a scheduled_job_id from a previous schedule.

        This is correct behavior - it cleans up orphaned scheduled jobs even when
        switching to immediate execution.
        """
        if tsq_imported_module == 'rq':
            service = RQTaskQueueService()

            mock_task = MagicMock()
            mock_task.scheduled_job_id = 'leftover-job-888'
            mock_task.name = 'immediate_task'
            mock_task.scheduling = None  # Immediate execution
            mock_task.id = 88

            mock_new_job = MagicMock(id='immediate-job-999')
            service.queue.enqueue.return_value = mock_new_job

            service.add(mock_task)

            # Assert scheduler.cancel WAS called to clean up the old scheduled job
            service.scheduler.cancel.assert_called_once_with('leftover-job-888')

            # Assert immediate execution was queued
            service.queue.enqueue.assert_called_once_with(mock_run_management_command, mock_task.id)


class TestEmitNotifications(TestCase):

    def setUp(self):
        mock_report = MagicMock()
        mock_report.task.name = 'test_task'
        mock_report.invocation_datetime.strftime.return_value = 'test_time'
        mock_report.n_log_warnings = 1
        mock_report.n_log_errors = 2
        mock_report.id = 1
        mock_report.log_tail.return_value = 'log_tail'

        self.report = mock_report

    @patch('eztaskmanager.services.notifications.SlackNotificationHandler')
    @patch('eztaskmanager.services.notifications.EmailNotificationHandler')
    def test_emit_notifications_with_result(self, mock_email_handler, mock_slack_handler):
        self.report.invocation_result = LaunchReport.RESULT_ERRORS
        self.report.get_notification_handlers.return_value = {
            'email': mock_email_handler,
            'slack': mock_slack_handler
        }

        # Call the function to be tested
        emit_notifications(self.report)

        # Assert that the expected methods were called with the correct parameters
        mock_slack_handler.handle.assert_called_once_with(self.report)
        mock_email_handler.handle.assert_called_once_with(self.report)


    @patch('eztaskmanager.services.notifications.SlackNotificationHandler')
    @patch('eztaskmanager.services.notifications.EmailNotificationHandler')
    def test_emit_notifications_no_result(self, mock_email_handler, mock_slack_handler):
        self.report.invocation_result = None
        self.report.get_notification_handlers.return_value = {
            'email': mock_email_handler,
            'slack': mock_slack_handler
        }

        # Call the function to be tested
        res = emit_notifications(self.report)

        # Assert that the expected methods were called with the correct parameters
        assert res is None
        mock_slack_handler.handle.assert_not_called()
        mock_email_handler.handle.assert_not_called()
