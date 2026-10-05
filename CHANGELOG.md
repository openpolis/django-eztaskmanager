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

## [0.5.2] - 2026-04-26

### Fixed

- Documentation examples of `EZTASKMANAGER_NOTIFICATION_HANDLERS` used `'failure'` as level, which is not a valid key of `LEVEL_MAPPING` and silently fell back to level 0, so notifications fired on any non-ok result instead of only on failures. The correct key is `'failed'`.

## [0.5.1] - 2025-10-25

### Fixed

- Tasks could be scheduled more than once in Redis Queue, and executed twice, after stack restarts, deployments or manual re-activation. `RQTaskQueueService` now cancels the existing scheduled job before creating a new one, handles job ids that no longer exist in Redis, and logs deduplication events.

### Added

- Tests for the deduplication scenarios; development and testing section in `README.md`.

## [0.5.0] - 2025-01-03

### Changed

- Dependencies upgraded: `django-rq` 3, `rq-scheduler` 0.14, Django 5.1, Celery 5.4. **Backward incompatible**: requires `rq` 2 and `django-rq` 3; use 0.4.3 with earlier `rq` releases.

## [0.4.3] - 2024-07-25

### Changed

- The `collectcommands` and `test_command` management commands extend `LoggerEnabledCommand`, so their output is logged to the database.

## [0.4.2] - 2024-07-24

### Changed

- Tests for stopping a started task; release instructions updated in the developer documentation.

## [0.4.1] - 2024-07-24

### Fixed

- Stopping a task resets its status even when the corresponding scheduled job no longer exists in the queue.

## [0.4.0] - 2024-05-28

### Changed

- Django and Celery are optional dependencies (extras), so the package can be installed with either queue backend; `beautifulsoup4` moved to the development dependencies.

## [0.3.8] - 2024-05-28

### Added

- Italian translation.

## [0.3.7] - 2024-05-28

### Changed

- The queue service imports `django_rq` or `celery` conditionally, depending on which one is installed.

## [0.3.6] - 2024-05-28

### Fixed

- Clear `ImportError` when neither `django_rq` nor Celery is installed. Not published on PyPI: first available in 0.3.7.

## [0.3.1] – [0.3.5] - 2024-04-09

### Changed

- Release workflow fixes and documentation updates (introduction, developer guide); no changes to the package code. Only 0.3.1 was published on PyPI.

## [0.3.0] - 2024-04-09

Not published on PyPI.

### Changed

- GitHub Actions versions updated in the release workflow.

## [0.2.0] - 2024-04-09

Not published on PyPI.

### Fixed

- Packaging: `pyproject.toml` declares the `eztaskmanager` package explicitly, after the distribution was renamed `django-eztaskmanager`.

## [0.1.0] - 2024-04-09

### Added

- Started new project based on `django-uwsgi-taskmanagers` (https://github.com/openpolis/django-uwsgi-taskmanager).
- Let go of the uwsgi spooler in favor of Redis queue manager. This change provides a more reliable and flexible queuing system, enhancing the project's overall endurance.
- Redirected logs from the file system to the database. This approach is an effort to centralize the information and to make log analysis more consolidated and convenient.
- The testing strategy has been fortified with comprehensive unit tests, ensuring that our code is bug-resistant and future modifications do not break existing functionalities.
- Email and Slack notifications of task results.
- Scheduling and repetition interval computation in the `Task` model.
- Sphinx documentation on Read the Docs; GitHub Actions workflow for lint and tests (Django 3.2, 4, 5).

### Changed

- Improved the handling of UTC times to prevent tasks from changing their scheduled hours during repeated executions. This helps keep tasks inline and their executions predictable.
- Refined the possible states of a task to idle, started, or scheduled - a paradigm shift intended to minimize complexity and enhance clarity.
- Implemented a failsafe to prevent tasks from being scheduled in the past. This change slams the door on any potential temporal anomalies that could lead to unexpected behavior.
- License changed from MIT to AGPL.
- Published on PyPI as `django-eztaskmanager`.

### Fixed

- Bulk delete of tasks from the admin.

