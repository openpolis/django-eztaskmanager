import logging
from typing import Optional

from django.core.management import call_command

from eztaskmanager.models import LaunchReport, Task
from eztaskmanager.services.logger import (DatabaseLogHandler,
                                           verbosity2loglevel)
from eztaskmanager.services.notifications import emit_notifications
from eztaskmanager.services.queues import get_task_service


def run_management_command(task_id: int):
    """
    Execute a management command.

    Creates a LaunchReport for this execution.

    :param task_id: The task object representing the management command to be executed.
    :type task_id: int

    :return: None
    """
    task: Optional[Task] = None

    # Define your format
    fmt = '%(asctime)s - %(levelname)s - %(message)s'
    datefmt = '%m-%d-%Y %H:%M:%S'  # You can define the date format as per your requirement
    formatter = logging.Formatter(fmt, datefmt)

    local_logger = logging.getLogger("eztaskmanager.services.logger")

    # task re-hydration
    try:
        task: Task = Task.objects.get(id=task_id)
        local_logger.setLevel(verbosity2loglevel(int(task.options.get('verbosity', 1))))
    except Task.DoesNotExist:
        local_logger.error(f"Task with id {task_id} not found")
    finally:
        local_logger.info('Finished')

    if task is not None:
        service = get_task_service()
        report = LaunchReport(task=task)
        report.save()

        task.prune_reports()

        result = LaunchReport.RESULT_OK

        # Check and Set DatabaseLogHandler
        if not any(isinstance(handler, DatabaseLogHandler) for handler in local_logger.handlers):
            handler = DatabaseLogHandler(report.id)
            local_logger.addHandler(handler)

        # Check and Set StreamHandler
        if not any(isinstance(handler, logging.StreamHandler) for handler in local_logger.handlers):
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            local_logger.addHandler(handler)

        local_logger.info('Starting')
        task_original_status = task.status
        task.status = Task.STATUS_STARTED
        task.save()

        # Execute the command
        try:
            call_command(task.command.name, *task.complete_args, launch_report_id=report.id)
        except Exception as e:
            result = LaunchReport.RESULT_FAILED
            local_logger.error(f"EXCEPTION raised: {e}")
        finally:
            local_logger.info('Finished')

        if result != LaunchReport.RESULT_FAILED:
            if report.n_log_errors:
                result = LaunchReport.RESULT_ERRORS
            elif report.n_log_warnings:
                result = LaunchReport.RESULT_WARNINGS

        report.invocation_result = result
        report.save()

        task.cached_last_invocation_result = report.invocation_result
        task.cached_last_invocation_n_errors = report.n_log_errors
        task.cached_last_invocation_n_warnings = report.n_log_warnings
        task.cached_last_invocation_datetime = report.invocation_datetime
        task.status = task_original_status

        _, task.cached_next_ride = service.fetch_job_with_next_time(task)

        # a non-periodic task is set back to IDLE and its scheduled job id set to None
        if task.status == Task.STATUS_SCHEDULED and not task.is_periodic:
            task.status = Task.STATUS_IDLE
            task.scheduled_job_id = None

        task.save()

        # Finally, emit notifications
        try:
            emit_notifications(report)
        except Exception:
            pass
