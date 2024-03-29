import re
from io import StringIO
from typing import Dict

from django.apps import apps
from django.core.management import load_command_class
from django.db import models
from django.utils.translation import gettext_lazy as _

from eztaskmanager.settings import EZTASKMANAGER_N_REPORTS_INLINE


class AppCommand(models.Model):
    """An application command representation."""

    name = models.CharField(max_length=100)
    app_name = models.CharField(max_length=100)
    active = models.BooleanField(default=True)

    def get_command_class(self):
        """Get the command class."""
        return load_command_class(app_name=self.app_name, name=self.name)

    @property
    def help_text(self):
        """Get the command help text."""
        output = StringIO()
        command_class = self.get_command_class()
        command_class.create_parser("", self.name).print_help(file=output)
        return output.getvalue()

    def __str__(self):
        """Return the string representation of the app command."""
        return f"{self.app_name}: {self.name}"

    class Meta:
        """Django model options."""

        verbose_name = _("Command")
        verbose_name_plural = _("Commands")


class LaunchReport(models.Model):
    """A report of a task execution with log."""

    RESULT_NO = ""
    RESULT_OK = "ok"
    RESULT_FAILED = "failed"
    RESULT_ERRORS = "errors"
    RESULT_WARNINGS = "warnings"
    RESULT_CHOICES = (
        (RESULT_NO, "---"),
        (RESULT_OK, "OK"),
        (RESULT_FAILED, "FAILED"),
        (RESULT_ERRORS, "ERRORS"),
        (RESULT_WARNINGS, "WARNINGS"),
    )

    task = models.ForeignKey("Task", on_delete=models.CASCADE)
    invocation_result = models.CharField(
        max_length=20, choices=RESULT_CHOICES, default=RESULT_NO
    )
    invocation_datetime = models.DateTimeField(auto_now_add=True)

    @classmethod
    def get_notification_handlers(cls):
        return apps.get_app_config('eztaskmanager').notification_handlers

    def get_log_lines(self):
        # Format the log entries as you like, here is an example
        log_lines = [
            f"{log.timestamp} - {log.level} - {log.message}"
            for log in self.logs.order_by('timestamp')
        ]
        return log_lines

    def read_log_lines(self, offset: int):
        """Uses an offset to read lines of the llog related to the report (self) starting from the offset

            :param: offset lines to start from

            :return: 2-tuple (list, int)
              - list of lines of log records from offset
              - the number of total lines

            """
        log_lines = [
            f"{log.timestamp} - {log.level} - {log.message}"
            for log in self.logs.all()
        ]
        return log_lines[offset:], len(log_lines)

    def log_tail(self, n_lines=10):
        """
        Return the last lines of the logs of a launch_report
        """
        # Get the related logs
        logs = self.logs.order_by('-timestamp')[:n_lines]
        total_logs = self.logs.count()

        hidden_lines = total_logs - n_lines
        report_lines = []
        if hidden_lines > 0:
            report_lines.append(f"{hidden_lines} lines hidden ...")

        for log in reversed(logs):
            # Format the log entries as you like, here is an example
            log_line = f"{log.timestamp} - {log.level} - {log.message}"
            report_lines.append(log_line)

        report = "\n".join(report_lines)
        return report

    @property
    def n_log_lines(self):
        return self.logs.count()

    @property
    def n_log_errors(self):
        return self.logs.filter(level="ERROR").count()

    @property
    def n_log_warnings(self):
        return self.logs.filter(level="WARNING").count()

    def delete(self, *args, **kwargs):
        task = self.task
        # call the parent delete method
        super().delete(*args, **kwargs)
        # re-calculate cache
        task.compute_cache()

    def __str__(self):
        """Return the string representation of the app command."""
        return (
            f"LaunchReport {self.task.name} {self.invocation_result}"
            f" {self.invocation_datetime}"
        )


class Log(models.Model):
    launch_report = models.ForeignKey(
        'LaunchReport',
        on_delete=models.CASCADE,
        related_name='logs'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    level = models.CharField(max_length=10)
    message = models.TextField()

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f'Log {self.id}: {self.level} at {self.timestamp}'


class TaskCategory(models.Model):
    """A task category, used to group tasks when numbers go up."""

    name = models.CharField(max_length=255)

    def __str__(self):
        """Return the string representation of the task category."""
        return self.name

    class Meta:
        """Django model options."""

        verbose_name = _("Task category")
        verbose_name_plural = _("Tasks categories")


class Task(models.Model):
    """
    A command related task.

    Represents a management command with a defined set of arguments (
    """

    REPETITION_PERIOD_MINUTE = "minute"
    REPETITION_PERIOD_HOUR = "hour"
    REPETITION_PERIOD_DAY = "day"
    REPETITION_PERIOD_WEEK = "week"
    REPETITION_PERIOD_MONTH = "month"
    REPETITION_PERIOD_CHOICES = (
        (REPETITION_PERIOD_MINUTE, "MINUTE"),
        (REPETITION_PERIOD_HOUR, "HOUR"),
        (REPETITION_PERIOD_DAY, "DAY"),
        (REPETITION_PERIOD_MONTH, "MONTH"),
    )

    STATUS_IDLE = "idle"
    STATUS_SPOOLED = "spooled"
    STATUS_SCHEDULED = "scheduled"
    STATUS_STARTED = "started"
    STATUS_CHOICES = (
        (STATUS_IDLE, "IDLE"),
        (STATUS_SPOOLED, "SPOOLED"),
        (STATUS_SCHEDULED, "SCHEDULED"),
        (STATUS_STARTED, "STARTED"),
    )

    name = models.CharField(max_length=255)
    command = models.ForeignKey(
        AppCommand, on_delete=models.CASCADE, limit_choices_to={"active": True}
    )
    arguments = models.TextField(
        blank=True,
        help_text=_(
            'Separate arguments with a comma ","'
            'and parameters with a blank space " ". '
            "eg: -f, --secondarg param1 param2, --thirdarg=pippo, --thirdarg"
        ),
    )
    category = models.ForeignKey(
        TaskCategory,
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        help_text=_("Choose a category for this task"),
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_IDLE, editable=False
    )
    scheduling = models.DateTimeField(
        blank=True, null=True,
        verbose_name=_("Initial scheduling")
    )
    repetition_period = models.CharField(
        max_length=20, choices=REPETITION_PERIOD_CHOICES, blank=True
    )
    repetition_rate = models.PositiveSmallIntegerField(blank=True, null=True)

    note = models.TextField(
        blank=True, null=True, help_text=_("A note on how this task is used.")
    )

    scheduled_job_id = models.CharField(
        max_length=64,
        blank=True, null=True,
        help_text=_("A unique identifier for the scheduled job, if any")
    )
    cached_last_invocation_datetime = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Last datetime")
    )
    cached_last_invocation_result = models.CharField(
        max_length=20,
        choices=LaunchReport.RESULT_CHOICES,
        blank=True,
        null=True,
        verbose_name=_("Last result"),
    )
    cached_last_invocation_n_errors = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_("Errors")
    )
    cached_last_invocation_n_warnings = models.PositiveIntegerField(
        null=True, blank=True, verbose_name=_("Warnings")
    )
    cached_next_ride = models.DateTimeField(
        blank=True, null=True, verbose_name=_("Next execution time"),
    )

    @property
    def interval_in_seconds(self):
        """
        Returns the interval in seconds based on the repetition period and rate.

        Returns:
            int: The interval in seconds.

        Example:
            # Create an instance of the class
            obj = MyClass()

            # Set the repetition period and rate
            obj.repetition_period = 'day'
            obj.repetition_rate = 2

            # Calculate the interval in seconds
            result = obj.interval_in_seconds()  # Returns 2 * 24 * 60 * 60

        """
        period_to_seconds = {
            self.REPETITION_PERIOD_MINUTE: 60,
            self.REPETITION_PERIOD_HOUR: 60 * 60,
            self.REPETITION_PERIOD_DAY: 24 * 60 * 60,
            self.REPETITION_PERIOD_WEEK: 7 * 24 * 60 * 60,
            self.REPETITION_PERIOD_MONTH: 30 * 24 * 60 * 60
        }

        return period_to_seconds[self.repetition_period] * self.repetition_rate

    @property
    def _args_dict(self):
        """
        Method: _args_dict

        Description:
        This method returns a dictionary containing arguments and their corresponding parameters.
        It parses the 'arguments' attribute of the instance and splits it into individual arguments
        * using a comma as a delimiter. Each argument is then further split into chunks using whitespace or
          an equals sign as a separator. The first chunk is considered the argument name, while
        * the second chunk, if present, is considered the parameter. The resulting arguments and parameters
          are stored in the dictionary 'res'.

        Parameters:
        - None

        Returns:
        - res (dict): A dictionary containing argument-parameter pairs.
          If the 'arguments' attribute is empty or consists of whitespace characters only,
          an empty dictionary is returned.

        Example usage:
        ```
        instance = MyClass()
        arguments = "arg1, arg2=param2, arg3 = param3"
        result = instance._args_dict()  # { 'arg1': None, 'arg2': 'param2', 'arg3': 'param3' }
        ```
        """
        res = {}
        if not self.arguments or self.arguments.strip() == "":
            return res
        args = re.split(r"\s*,\s*", self.arguments)
        for arg in args:
            arg_chunks = arg.split("=")
            argument = arg_chunks[0]
            try:
                params = arg_chunks[1]
            except IndexError:
                params = None
            res[argument] = params
        return res

    @property
    def args(self):
        """Get the task args."""
        return [f"{x}" for x, y in self._args_dict.items() if not y]

    @property
    def options(self):
        """Get the task options."""
        return {
            f"{x}".strip("-").replace("-", "_"): f"{y}"
            for x, y in self._args_dict.items()
            if y
        }

    @property
    def complete_args(self):
        """
        Returns a list containing all the non-null values from the dictionary of arguments.
        Get all task args in order to avoid problems with required options.

        :return: A list containing non-null argument values.

        As suggested here:
        https://stackoverflow.com/questions/32036562/call-command-argument-is-required
        """
        return list(
            filter(
                lambda x: x is not None,
                (
                    item
                    for sublist in [(k, v) for k, v in self._args_dict.items()]
                    for item in sublist
                ),
            )
        )

    def compute_cache(self):
        reports = self.launchreport_set.order_by('-invocation_datetime')
        if reports.exists():
            latest_report = reports[0]  # get the latest execution report

            self.cached_last_invocation_datetime = latest_report.invocation_datetime
            self.cached_last_invocation_result = latest_report.invocation_result
            self.cached_last_invocation_n_errors = latest_report.n_log_errors
            self.cached_last_invocation_n_warnings = latest_report.n_log_warnings
            # self.cached_next_ride = latest_report.next_ride
        else:
            # no reports, set all cached values to None
            self.cached_last_invocation_datetime = None
            self.cached_last_invocation_result = None
            self.cached_last_invocation_n_errors = None
            self.cached_last_invocation_n_warnings = None
            self.cached_next_ride = None

        self.save()

    def prune_reports(self, n: int = EZTASKMANAGER_N_REPORTS_INLINE):
        """Delete all Task's LaunchReports except latest `n`"""
        if n:
            last_n_reports_ids = (
                LaunchReport.objects.filter(task=self)
                .order_by("-id")[:n]
                .values_list("id", flat=True)
            )
            LaunchReport.objects.filter(task=self).exclude(
                pk__in=list(last_n_reports_ids)
            ).delete()
            self.compute_cache()

    def __str__(self):
        """Return the string representation of the task."""
        return f"{self.name} ({self.status})"

    class Meta:
        """Django model options."""

        verbose_name = _("Task")
        verbose_name_plural = _("Tasks")
