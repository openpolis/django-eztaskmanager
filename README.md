## The mission

Django application that allows the easy management of scheduled, long, asynchronous tasks, 
within the django admin site, through django-rq or django-celery.

## Main features

- Use standard django management commands as tasks 'templates'
- Import available management commands through a management command itself, as possible models for tasks
- Start and stop tasks manually via admin
- Schedule point and periodic tasks via django admin
- Check or download the generated reports/logs
- Get notifications via Slack or email when a task fails
