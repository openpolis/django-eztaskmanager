from django.conf import settings
from django.contrib import admin, messages
from django.contrib.admin.actions import delete_selected
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from pytz import timezone

from eztaskmanager.models import AppCommand, LaunchReport, Task, TaskCategory
from eztaskmanager.services.queues import TaskQueueException
from eztaskmanager.settings import (EZTASKMANAGER_N_LINES_IN_REPORT_LOG,
                                    EZTASKMANAGER_SHOW_LOGVIEWER_LINK)


def convert_to_local_dt(dt):
    """Convert datetime into local datetime, if django settings are set up to use TZ.

    Datetime fields in django store datetimes as UTC date, if the USE_TZ setting is set.
    To have the correct datetime sent to the admin, without using the django templating
    system, the conversion needs to be done manually.
    """
    try:
        if settings.USE_TZ:
            local_tz = timezone(settings.TIME_ZONE)
            dt = local_tz.normalize(dt.astimezone(local_tz))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except AttributeError:
        return ""


@admin.register(AppCommand)
class AppCommandAdmin(admin.ModelAdmin):
    """Admin options for application commands."""

    change_form_template = "admin/appcommand_changeform.html"
    list_display = ("app_name", "name", "active")
    list_display_links = ("name", )
    list_editable = ("active",)
    list_filter = ("active",)
    ordering = ("app_name", "name")
    readonly_fields = ("app_name", "name")
    search_field = ("app_name", "name")

    def has_add_permission(self, request, obj=None):
        """Return False to avoid to add an object."""
        return False

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Override the default changeform_view method."""
        extra_context = extra_context or {}
        extra_context["show_save_and_continue"] = False
        extra_context["show_save"] = False
        return super().changeform_view(request, object_id, extra_context=extra_context)


class BulkDeleteMixin(object):
    """A mixin used within ModelAdmin extensions.

    It overrides the default bulk delete action with a method that invokes
    delete() on each item in the queryset.

    This can be useful whenever an overridden delete() method fo each model
    instance to be deleted should be invoked, instead of the default sql bulk
    delete shortcut used by the default action.

    See:
    https://stackoverflow.com/questions/6321940
    """

    class SafeDeleteQuerysetWrapper(object):
        """Override the queryset returned by the model's manager to intercept delete.

        Implement __iter__, __getattr__, __getitem__ and __len__ to quack like a dict,
        like django querysets do.

        Implement _safe_delete, invoking delete() on each items in the wrapped_queryset
        """

        def __init__(self, wrapped_queryset):
            """Init method."""
            self.wrapped_queryset = wrapped_queryset

        def __getattr__(self, attr):
            """Getattr method."""
            return self._safe_delete

        def __iter__(self):
            """Yield obj from wrapped queryset."""
            for obj in self.wrapped_queryset:
                yield obj

        def __getitem__(self, index):
            """Get item method."""
            return self.wrapped_queryset[index]

        def __len__(self):
            """Len method."""
            return len(self.wrapped_queryset)

        def _safe_delete(self):
            """Safe delete method."""
            for obj in self.wrapped_queryset:
                obj.delete()

    def get_actions(self, request):
        """Override ModelAdmin's get_actions, replacing the `delete_selected` item."""
        actions = getattr(super(BulkDeleteMixin, self), "get_actions")(request)  # noqa
        actions["delete_selected"] = (
            BulkDeleteMixin.action_safe_bulk_delete,
            "delete_selected",
            _("Delete selected %(verbose_name_plural)s"),
        )
        return actions

    def action_safe_bulk_delete(self, request, queryset):
        """Wrap the delete_selected method with the SafeDeleteQuerysetWrapper.

        That a confirmation form is presented to the user before deletion,
        and delete() is overridden with _safe_delete()
        """
        qs_wrapper = BulkDeleteMixin.SafeDeleteQuerysetWrapper(queryset)
        return delete_selected(self, request, qs_wrapper.wrapped_queryset)


class LaunchReportMixin(object):
    """
    Overrides some of the methods of the ModelAdmin.

    Provide a log_tail custom field showing the last lines of the log
    and a link to a logviewer.
    """

    @mark_safe
    def log_tail_html(self, report):
        """Return the last lines of the log and a link to a logviewer."""
        n_max_lines = EZTASKMANAGER_N_LINES_IN_REPORT_LOG
        lines = "<pre>"
        lines += report.log_tail(n_max_lines)
        if EZTASKMANAGER_SHOW_LOGVIEWER_LINK:
            last_report_url = reverse("eztaskmanager:live_log_viewer", args=(report.pk,))
            lines += _(
                (
                    "\n\n<a href='{0}' target='_blank'>"
                    "Show the log messages</a>"
                )
            ).format(last_report_url)
        lines += "</pre>"
        return lines


# @admin.register(LaunchReport)
class LaunchReportAdmin(LaunchReportMixin, admin.ModelAdmin):
    """Admin options for reports."""

    date_hierarchy = "invocation_datetime"
    fields = readonly_fields = (
        "task",
        "invocation_result",
        "invocation_datetime",
        "log_tail_html",
        "n_log_errors",
        "n_log_warnings",
    )
    list_display = ("task", "invocation_result", "invocation_datetime")
    list_filter = ("invocation_result",)
    ordering = ("-invocation_datetime", "-id")
    search_field = ("task__name", "task__status", "task__spooler_id")

    def has_add_permission(self, request, obj=None):
        """Return False to avoid to add an object."""
        return False

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        """Override the default changeform_view method."""
        extra_context = extra_context or {}
        extra_context["show_save_and_continue"] = False
        extra_context["show_save"] = False
        return super().changeform_view(request, object_id, extra_context=extra_context)


class LaunchReportInline(LaunchReportMixin, admin.TabularInline):
    """An inline for related reports."""

    max_num = 5
    extra = 0
    fields = readonly_fields = (
        "invocation_result", "invocation_datetime", "log_tail_html", "n_log_errors", "n_log_warnings",
    )
    ordering = [
        "-invocation_datetime",
    ]
    model = LaunchReport
    show_change_link = True

    def has_add_permission(self, request, obj=None):
        """Return False to avoid to add an object."""
        return False


class TaskInline(admin.TabularInline):
    """An inline for tasks, to use inside TaskCategory detail view."""

    extra = 0
    fields = readonly_fields = ("name", "arguments", "status_str")
    model = Task
    show_change_link = True

    def status_str(self, obj):
        """Return the string representation of status/last result/next ride."""
        status_str = obj.status + "/"
        if obj.cached_last_invocation_datetime:
            last_invocation_dt = convert_to_local_dt(obj.cached_last_invocation_datetime)
            s = (
                f"{last_invocation_dt}: "
                f"{obj.cached_last_invocation_result} - "
                f"{obj.cached_last_invocation_n_errors}E, "
                f"{obj.cached_last_invocation_n_warnings}W"
            )
        else:
            s = "-"

        status_str += s + "/"
        if obj.cached_next_ride:
            s = f"{convert_to_local_dt(obj.cached_next_ride)}"
        else:
            s = "-"
        status_str += s
        return status_str

    status_str.short_description = "Status/Last result/Next ride"
    status_str.allow_tags = True


@admin.register(TaskCategory)
class TaskCategoryAdmin(admin.ModelAdmin):
    """Admin options for task categories."""

    inlines = [TaskInline]
    list_display = ("name",)


@admin.register(Task)
class TaskAdmin(BulkDeleteMixin, admin.ModelAdmin):
    """Admin options for tasks.

    Use BulkDeleteMixin, in order to invoke obj.delete() for every selected tasks.
    This is needed in order to use the Task.delete method, that stops the task before
    removing the DB record.
    """

    actions = ["launch_tasks", "stop_tasks"]
    change_form_template = "admin/custom_changeform.html"
    inlines = [LaunchReportInline]
    list_display = (
        "name_desc",
        "invocation",
        "status",
        "last_result_with_logviewer_link",
        "cached_last_invocation_datetime",
        "cached_next_ride",
        "repetition",
    )
    list_display_links = ('name_desc',)
    list_filter = ("status", "cached_last_invocation_result", "category")
    ordering = ("-cached_last_invocation_datetime",)
    fieldsets = (
        (
            "Definition",
            {"fields": ("name", "command", "arguments", "category", "note")},
        ),
        (
            "Scheduling",
            {"fields": (
                "scheduling", "repetition_period", "repetition_rate", "cached_next_ride", "scheduled_job_id"
            )},
        ),
        (
            "Last execution",
            {
                "fields": (
                    "status",
                    "cached_last_invocation_datetime",
                    "last_result_with_logviewer_link",
                    "cached_last_invocation_n_errors",
                    "cached_last_invocation_n_warnings",
                )
            },
        ),
    )
    readonly_fields = (
        "status",
        "scheduled_job_id",
        "cached_last_invocation_datetime",
        "last_result_with_logviewer_link",
        "cached_next_ride",
        "cached_last_invocation_n_errors",
        "cached_last_invocation_n_warnings",
    )
    save_as = True
    save_on_top = True
    search_fields = ("name", "command__app_name", "command__name")

    def launch_tasks(self, request, queryset):
        """Put many tasks in the queue."""
        from eztaskmanager.services.queues import get_task_service

        service = get_task_service()
        for task in queryset:
            service.add(task)
        self.message_user(request, f'{len(queryset)} tasks launched.')

    launch_tasks.short_description = 'Launch selected tasks'

    def stop_tasks(self, request, queryset):
        """Remove many tasks from the queue."""
        from eztaskmanager.services.queues import get_task_service

        service = get_task_service()
        for task in queryset:
            service.remove(task)
        self.message_user(request, f'{len(queryset)} tasks stopped.')

    stop_tasks.short_description = 'Stop selected tasks'

    def repetition(self, obj):
        """Return the string representation of the repetition."""
        if obj.repetition_rate and obj.repetition_period:
            return f"{obj.repetition_rate} {obj.repetition_period}"
        else:
            return "-"

    repetition.short_description = _("Repetition rate")

    def name_desc(self, obj):
        """Show the note on mouse over."""
        return format_html(
            f"<span title=\"{obj.note}\">{obj.name}</span>"
        )

    name_desc.short_description = _("Name")

    def invocation(self, obj):
        """Show the command name, with arguments."""
        return format_html(
            f"<span style=\"font-weight: normal; font-family: Courier\"><b>{obj.command.name}</b> <br/>"
            f"{' '.join(obj.arguments.split(','))}</span>"
        )

    invocation.short_description = _("Invocation")

    def last_result_with_logviewer_link(self, obj):
        """Show the last result, with a log to the logviewer."""
        s = "-"
        link_text = _("Show log messages")
        last_report = obj.launchreport_set.order_by('invocation_datetime').last()
        result = obj.cached_last_invocation_result
        if result:
            s = result.upper()
            if EZTASKMANAGER_SHOW_LOGVIEWER_LINK:
                last_report_url = reverse("eztaskmanager:live_log_viewer", args=(last_report.id,))
                s = format_html(f"{s} - <a href=\"{last_report_url}\" target=\"_blank\">{link_text}</a>")
        return s
    last_result_with_logviewer_link.short_description = _("Last result")

    def cached_last_invocation_datetime(self, obj):
        """Return the string representation of the next ride."""
        if obj.cached_last_invocation_datetime:
            return f"{convert_to_local_dt(obj.cached_last_invocation_datetime)}"
        else:
            return "-"

    def response_change(self, request, task):
        """Determine the HttpResponse for the change_view stage."""
        if "_start-task" in request.POST:
            from eztaskmanager.services.queues import get_task_service

            service = get_task_service()
            try:
                service.add(task)
                self.message_user(
                    request,
                    "This task was successfully launched. Reload the page to see the logs.",
                    level=messages.SUCCESS
                )
            except TaskQueueException as ex:
                self.message_user(
                    request,
                    ex, level=messages.ERROR
                )
            return HttpResponseRedirect(".")
        if "_stop-task" in request.POST:
            from eztaskmanager.services.queues import get_task_service

            service = get_task_service()
            service.remove(task)
            self.message_user(
                request, "This task was successfully stopped", level=messages.SUCCESS
            )
            return HttpResponseRedirect(".")
        return super().response_change(request, task)
