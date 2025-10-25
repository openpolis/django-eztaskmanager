# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

django-eztaskmanager is a Django application for managing Django management commands asynchronously via the admin interface, using Redis Queue (RQ) or Celery. It's a port and evolution of django-uwsgi-taskmanager.

## Development Commands

### Setup
```bash
# Install dependencies using Poetry
poetry install

# For development with demo project
cd demoproject
python manage.py migrate
python manage.py createsuperuser
python manage.py collectcommands --excludecore
```

### Running the Demo Project
```bash
cd demoproject

# Start Django development server
python manage.py runserver

# Start RQ worker (in separate terminal)
python manage.py rqworker

# Start RQ scheduler (in separate terminal)
python manage.py rqscheduler --verbosity=3
```

### Testing
```bash
# Run all tests (uses Poetry virtualenv and Django test runner)
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
poetry run python demoproject/manage.py test --verbosity=2

# Run specific test module
poetry run python demoproject/manage.py test eztaskmanager.tests.test_services -v 2

# Run with coverage
poetry run coverage run demoproject/manage.py test
poetry run coverage report
```

### Code Quality
```bash
# Format code with black
black eztaskmanager/

# Run flake8 linting
flake8 eztaskmanager/

# Type checking with mypy
mypy eztaskmanager/
```

### Documentation
```bash
# Build documentation
cd docs
make html

# Auto-rebuild documentation on changes
sphinx-autobuild . _build/html
```

## Architecture

### Core Components

**Models** (`eztaskmanager/models.py`):
- `AppCommand`: Represents Django management commands that can be executed asynchronously
- `Task`: Links a command with specific arguments, scheduling, and repetition settings
- `LaunchReport`: Records of task executions with results
- `Log`: Individual log entries for each launch report
- `TaskCategory`: Groups tasks for organization

**Queue Services** (`eztaskmanager/services/queues.py`):
- Abstract `TaskQueueService` interface for queue implementations
- `RQTaskQueueService`: Redis Queue implementation
- `CeleryTaskQueueService`: Celery implementation (experimental)
- Service selection via `EZTASKMANAGER_QUEUE_SERVICE_TYPE` setting

**Logger** (`eztaskmanager/services/logger.py`):
- `LoggerEnabledCommand`: Base class for management commands that need logging to database
- `DatabaseLogHandler`: Custom logging handler that writes to the `Log` model
- Commands should inherit from `LoggerEnabledCommand` instead of Django's `BaseCommand`

**Task Execution Flow** (`eztaskmanager/services/__init__.py`):
1. `run_management_command(task_id)` is the main entry point called by queue workers
2. Creates a `LaunchReport` for tracking
3. Executes the command via `call_command()` with `launch_report_id` parameter
4. Logs are captured via `DatabaseLogHandler` and written to the database
5. Task status and cache fields are updated
6. Notifications are emitted based on result

**Admin Interface** (`eztaskmanager/admin.py`):
- `TaskAdmin`: Primary interface for creating/managing tasks
- Custom actions: `launch_tasks`, `stop_tasks`
- Live log viewer integration
- Inline display of recent `LaunchReport` instances

### Key Patterns

**Custom Management Commands**:
- Must inherit from `LoggerEnabledCommand` for database logging
- Commands receive `launch_report_id` parameter automatically
- Use `self.logger` for logging (not `self.stdout.write()`)

**Task Scheduling**:
- Point-in-time execution: Set `scheduling` field only
- Periodic execution: Set `scheduling`, `repetition_period`, and `repetition_rate`
- Tasks transition through states: IDLE → SCHEDULED → STARTED → IDLE

**Caching Strategy**:
- Tasks cache last execution results to avoid JOIN queries in list views
- `compute_cache()` recalculates cached fields from latest `LaunchReport`
- `prune_reports(n)` keeps only the latest N reports per task

**Notification System** (`eztaskmanager/services/notifications.py`):
- Configured via `EZTASKMANAGER_NOTIFICATION_HANDLERS` setting
- Supports Slack and Email handlers
- Notifications triggered based on result level (ok/warnings/errors/failure)

## Settings

All settings are optional and prefixed with `EZTASKMANAGER_`:

- `EZTASKMANAGER_QUEUE_SERVICE_TYPE`: 'RQ' or 'Celery' (default: 'RQ')
- `EZTASKMANAGER_N_LINES_IN_REPORT_LOG`: Lines shown in admin log tail (default: 10)
- `EZTASKMANAGER_N_REPORTS_INLINE`: Number of reports shown inline (default: 5)
- `EZTASKMANAGER_SHOW_LOGVIEWER_LINK`: Show log viewer links (default: True)
- `EZTASKMANAGER_BASE_URL`: Base URL for notification links (default: None)
- `EZTASKMANAGER_NOTIFICATION_HANDLERS`: Dict of notification handler configs (default: {})

## Important Implementation Details

**Argument Parsing** (`Task._args_dict`):
- Arguments stored as comma-separated string
- Parsed into args (no value) and options (with value)
- Complex regex parsing handles `--flag`, `--option=value`, `--option value` formats
- `complete_args` property returns flat list for `call_command()`

**Queue Integration**:
- RQ uses `django_rq.get_queue('default')` and `get_scheduler('default')`
- Scheduled jobs store `scheduled_job_id` for cancellation
- Periodic tasks use `scheduler.schedule()` with interval
- Point tasks use `scheduler.enqueue_at()` for one-time execution

**Database Logging**:
- `DatabaseLogHandler` intercepts Python logging calls
- Logs written to `Log` model with FK to `LaunchReport`
- Commands must accept `--launch_report_id` parameter
- Handler added automatically in `LoggerEnabledCommand.execute()`

## Version Management

Uses `bump2version` for version bumping:
```bash
# Bump patch version (0.5.0 → 0.5.1)
bump2version patch

# Bump minor version (0.5.0 → 0.6.0)
bump2version minor

# Bump major version (0.5.0 → 1.0.0)
bump2version major
```

Configuration in `.bumpversion.cfg`.
