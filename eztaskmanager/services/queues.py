import datetime
from abc import ABC, abstractmethod

import django_rq
from celery import shared_task, Celery
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from eztaskmanager.settings import EZTASKMANAGER_QUEUE_SERVICE_TYPE
from eztaskmanager.models import Task


class TaskQueueService(ABC):
    """
    Abstract base class for managing task queues.
    """
    @abstractmethod
    def add(self, task):  # pragma: no cover
        pass

    @abstractmethod
    def remove(self, task):  # pragma: no cover
        pass


def get_task_service():

    if EZTASKMANAGER_QUEUE_SERVICE_TYPE == 'RQ':
        return RQTaskQueueService()
    else:
        return CeleryTaskQueueService()


class TaskQueueException(Exception):
    pass


class RQTaskQueueService(TaskQueueService):
    """
    A subclass of TaskQueueService that manages tasks using RQ (Redis Queue).

    Attributes:
        queue (Queue): The default RQ queue.

    Methods:
        - add(task, at=None): Enqueues a task to be executed either immediately or at a specific time.
        - remove(task): Cancels a task if it is currently in the queue.

    """

    def __init__(self):
        self.queue = django_rq.get_queue('default')
        self.scheduler = django_rq.get_scheduler('default', interval=60)

    def add(self, task: Task):
        """
        Args:
            task: The task to be added.

        Returns:
            The job created for the task, either scheduled or enqueued for immediate execution.

        Raises:
             Exception: If there is an error while launching the task.

        """
        from eztaskmanager.services import run_management_command

        if task.scheduling and task.scheduling_utc < timezone.now():
            raise TaskQueueException(_("It is not possible to schedule tasks in the past"))

        try:
            if task.scheduling:
                if task.is_periodic:
                    # schedule execution at a point in time, with periodicity
                    rq_job = self.scheduler.schedule(
                        task.scheduling_utc,
                        run_management_command, [task.id],
                        interval=task.interval_in_seconds,
                        result_ttl=int(1.5 * task.interval_in_seconds)
                    )
                else:
                    # schedule execution at a point in time, with periodicity
                    rq_job = self.scheduler.enqueue_at(
                        task.scheduling_utc,
                        run_management_command, task.id
                    )
                task.scheduled_job_id = rq_job.id
                task.status = Task.STATUS_SCHEDULED
                job_id, task.cached_next_ride = self.fetch_job_with_next_time(task)
                task.save()
            else:
                # enqueue for immediate execution
                rq_job = self.queue.enqueue(run_management_command, task.id)
            return rq_job
        except Exception as e:
            raise TaskQueueException(_(f"Failed to add task: {e}"))

    def fetch_job_with_next_time(self, task):
        try:
            job_id, next_time = next(
                (j, next_time) for j, next_time in self.scheduler.get_jobs(with_times=True)
                if j.id == task.scheduled_job_id
            )
            next_time = timezone.make_aware(next_time, timezone=timezone.timezone.utc)
            return job_id, next_time
        except StopIteration:
            return None, None

    def remove(self, task):
        job, next_time = self.fetch_job_with_next_time(task)

        if job:
            self.scheduler.cancel(job)
            task.scheduled_job_id = None
            task.cached_next_ride = None
            task.status = Task.STATUS_IDLE
            task.save()


@shared_task
def execute_management_command(task):
    """Wrap the management command executor for celery"""
    from eztaskmanager.services import run_management_command

    return run_management_command(task)


class CeleryTaskQueueService(TaskQueueService):
    """
    A subclass of TaskQueueService that manages tasks using Celery.
    """

    def __init__(self):
        self.app = Celery(
            'tasks',
            broker='redis://redis:6379/1', backend='redis://redis:6379:2'
        )

    def add(self, task: Task):
        try:
            if task.scheduling:
                delay = task.scheduling - datetime.datetime.now()
                self.app.send_task(
                    'eztaskmanager.services.queues.execute_management_command',
                    args=[task],
                    countdown=delay.total_seconds()
                )
            else:
                self.app.send_task('eztaskmanager.services.queues.execute_management_command', args=[task])

            return True
        except Exception as e:
            print(f"Error while launching task: {e}")

    def remove(self, task):
        try:
            # With Celery, it's not straightforward to remove a task from the queue
            # The recommended way to stop a task is to revoke it
            self.app.control.revoke(task.id)
        except Exception as e:
            print(f"Error while halting task: {e}")
