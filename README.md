## The mission

This Django application empowers the efficient management and scheduling of asynchronous tasks within the Django Admin, 
featuring task notifications and report generation capabilities. 


## Main features

- Use standard django management commands as tasks 'templates'
- Import available management commands through a meta-management command, as possible templates for tasks
- Start and stop tasks manually via admin
- Schedule point and periodic tasks via django admin
- Use RQ (rq + rq-scheduler) or Celery (celery + celery-beat) for queue management
- Check or download the generated reports/logs
- Live logs streaming view, with filters on errors and warnings for tasks debugging
- Get notifications via Slack or email when a task succeeds or fails
