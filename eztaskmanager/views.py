"""Define Django views for the taskmanager app."""
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from eztaskmanager.models import LaunchReport


class LogViewerView(TemplateView):
    """Class LogViewerView displays a log viewer page with log information for a specific report."""

    template_name = "log_viewer.html"

    @staticmethod
    def get_report_lines(report):
        """Return the log lines for this report."""
        return report.get_log_lines()

    def get_context_data(self, **kwargs):
        """Return the context data for the view."""
        context = super().get_context_data(**kwargs)
        log_level = self.request.GET.get("log_level", "ALL").lower()
        levels = ["warning", "error"]
        pk = context.get("pk", None)
        try:
            report = LaunchReport.objects.get(pk=pk)
        except LaunchReport.DoesNotExist:
            log = _("No log for the report {pk}.").format(pk=pk)
        else:
            log_lines = self.get_report_lines(report)
            context["log_error"] = {
                "lines": (x for x in log_lines if "ERROR" in x),
                "n": report.n_log_errors,
            }
            context["log_warning"] = {
                "lines": (x for x in log_lines if "WARNING" in x),
                "n": report.n_log_warnings,
            }
            context["log_all"] = {"lines": log_lines, "n": report.n_log_lines}
            if log_level in levels or log_level == "all":
                log = "\n".join(context["log_" + log_level]["lines"])
            else:
                log = _("The available levels are: ERROR or WARNING")
        context["log_txt"] = log
        context["log_levels"] = levels
        context["selected_log_level"] = log_level
        return context


class LiveLogViewerView(TemplateView):
    """A template view to view the rolling report log."""

    template_name = "live_log_viewer.html"

    def get_context_data(self, **kwargs):
        """Return the context data for the view, removing the offset file, to allow reading log lines from the start."""
        context = super().get_context_data(**kwargs)
        pk = context.get("pk", None)

        try:
            report = LaunchReport.objects.get(pk=pk)
            context['report'] = report
            context['task'] = report.task
            context['task_arguments'] = report.task.arguments.split(',')
        except LaunchReport.DoesNotExist:
            pass

        return context


class AjaxReadLogLines(LogViewerView):
    """Read log lines starting from an offset, as JsonResponse.

    New log size and task status are included in the response.
    """

    def render_to_response(self, context, **response_kwargs):
        """
        Render a response with JSON data.

        Args:
            self: The instance of the class calling the method.
            context (dict): A dictionary containing the context data.
            **response_kwargs: Additional keyword arguments used for the response.

        Returns:
            JsonResponse: A response object with JSON data containing the following keys:
                - new_log_lines (list): List of log lines.
                - task_status (str): The status of the task.
                - log_size (int): The size of the log.

        Raises:
            None.
        """
        pk = context.get("pk", None)
        offset = int(self.request.GET.get('offset', 0))
        try:
            report = LaunchReport.objects.get(pk=pk)
            task_status = report.task.status
        except LaunchReport.DoesNotExist:
            log_lines = [_("No log for the report {pk}.").format(pk=pk), ]
            task_status = None
            log_size = 0
        else:
            log_lines, log_size = report.read_log_lines(offset)

        return JsonResponse({
            'new_log_lines': log_lines,
            'task_status': task_status,
            'log_size': log_size
        })
