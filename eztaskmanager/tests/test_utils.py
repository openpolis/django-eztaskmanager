from datetime import datetime
from datetime import timezone as dt_timezone

from django.test import TestCase, override_settings

from eztaskmanager.utils import format_local_dt


@override_settings(USE_TZ=True, TIME_ZONE='Europe/Rome')
class FormatLocalDtTestCase(TestCase):

    def test_summer_time(self):
        dt = datetime(2026, 10, 5, 7, 49, 7, tzinfo=dt_timezone.utc)
        self.assertEqual(format_local_dt(dt), "2026-10-05 09:49:07 CEST")

    def test_winter_time(self):
        dt = datetime(2025, 11, 13, 7, 15, 0, tzinfo=dt_timezone.utc)
        self.assertEqual(format_local_dt(dt), "2025-11-13 08:15:00 CET")

    def test_none(self):
        self.assertEqual(format_local_dt(None), "")

    def test_not_a_datetime(self):
        self.assertEqual(format_local_dt("not a datetime"), "")

    def test_naive_datetime_is_not_converted(self):
        dt = datetime(2026, 10, 5, 7, 49, 7)
        self.assertEqual(format_local_dt(dt), "2026-10-05 07:49:07")

    @override_settings(USE_TZ=False)
    def test_without_use_tz(self):
        dt = datetime(2026, 10, 5, 7, 49, 7)
        self.assertEqual(format_local_dt(dt), "2026-10-05 07:49:07")
