# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [0.5.3] - 2026-10-05

### Changed

- Dates and times are now shown in the local time zone (`TIME_ZONE`) with the zone abbreviation, e.g. `2026-10-05 09:49:07 CEST`, instead of UTC. This applies to the log lines in the admin, in the log viewer and in notifications (`LaunchReport.get_log_lines`, `read_log_lines`, `log_tail`, via the new `Log.formatted_line`), to the launch time in Slack and email notifications, to the next execution of tasks and the launch date of reports in the admin, and to the "Launched at" field of the log viewer (#12, closes #13).
- `eztaskmanager.admin.convert_to_local_dt` is kept as an alias of the new `eztaskmanager.utils.format_local_dt`, but its output now includes the time zone abbreviation.
- `admin.py` no longer imports `pytz`; the dependency is still declared in `pyproject.toml` but is no longer used by the code.
- Removed Python 3.8 and 3.9 from the CI test matrix; Django 3.2 is now tested only on Python 3.10. `pyproject.toml` already declares `python = ">=3.10"`.

### Known issues

- Periodic tasks start a few seconds later every day, and do not follow daylight saving time changes (#11); not addressed in this release.

## [0.1.0]

### Added

- Started new project based on `django-uwsgi-taskmanagers` (https://github.com/openpolis/django-uwsgi-taskmanager).
- Let go of the uwsgi spooler in favor of Redis queue manager. This change provides a more reliable and flexible queuing system, enhancing the project's overall endurance.
- Redirected logs from the file system to the database. This approach is an effort to centralize the information and to make log analysis more consolidated and convenient.
- The testing strategy has been fortified with comprehensive unit tests, ensuring that our code is bug-resistant and future modifications do not break existing functionalities.

### Changed

- Improved the handling of UTC times to prevent tasks from changing their scheduled hours during repeated executions. This helps keep tasks inline and their executions predictable.
- Refined the possible states of a task to idle, started, or scheduled - a paradigm shift intended to minimize complexity and enhance clarity.
- Implemented a failsafe to prevent tasks from being scheduled in the past. This change slams the door on any potential temporal anomalies that could lead to unexpected behavior.

