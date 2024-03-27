import logging

from django.core.management import call_command

from eztaskmanager.models import LaunchReport, Task
from eztaskmanager.services.logger import verbosity2loglevel, DatabaseLogHandler


def run_management_command(task):
    """
    Executes a management command.
    Creates a LaunchReport for this execution.

    :param task: The task object representing the management command to be executed.
    :type task: Task

    :return: None
    """
    report = LaunchReport(task=task)
    report.save()

    result = LaunchReport.RESULT_OK

    # Define your format
    fmt = '%(asctime)s - %(levelname)s - %(message)s'
    datefmt = '%m-%d-%Y %H:%M:%S'  # You can define the date format as per your requirement
    formatter = logging.Formatter(fmt, datefmt)

    local_logger = logging.getLogger("eztaskmanager.services.logger")
    local_logger.setLevel(verbosity2loglevel(int(task.options.get('verbosity', 1))))

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

    task.status = Task.STATUS_STARTED
    task.save(update_fields=("status",))

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
    task.status = Task.STATUS_IDLE
    task.save()
