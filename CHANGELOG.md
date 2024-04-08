# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


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

