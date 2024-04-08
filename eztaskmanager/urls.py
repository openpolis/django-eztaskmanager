"""Define Django urls for the taskmanager app."""
from django.urls import path

from eztaskmanager.views import (AjaxReadLogLines, LiveLogViewerView,
                                 LogViewerView)

app_name = "eztaskmanager"

urlpatterns = [
    path("logviewer/<int:pk>/", LogViewerView.as_view(), name="log_viewer"),
    path("livelogviewer/<int:pk>/", LiveLogViewerView.as_view(), name="live_log_viewer"),
    path("read_loglines/<int:pk>/", AjaxReadLogLines.as_view(), name='ajax_read_log_lines')
]
