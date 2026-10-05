"""Utilities shared by admin, models and notifications."""

from datetime import datetime

from django.conf import settings
from django.utils import timezone


def format_local_dt(dt):
    """Format a datetime in the local time zone (settings.TIME_ZONE), with the zone abbreviation.

    Datetime fields in django store datetimes as UTC dates, if the USE_TZ setting is set.
    Where they are rendered outside of the django templating system (admin methods,
    log lines, notifications) the conversion needs to be done manually, otherwise
    they are printed in UTC.

    Example: "2026-10-05 09:49:07 CEST". Naive datetimes are formatted as they are,
    without a zone. Returns an empty string for None or any non-datetime value.
    """
    if not isinstance(dt, datetime):
        return ""
    if settings.USE_TZ and timezone.is_aware(dt):
        return timezone.localtime(dt).strftime("%Y-%m-%d %H:%M:%S %Z")
    return dt.strftime("%Y-%m-%d %H:%M:%S")
