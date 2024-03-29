import datetime
from abc import ABC, abstractmethod

import django_rq
from celery import shared_task, Celery

from eztaskmanager.settings import EZTASKMANAGER_QUEUE_SERVICE_TYPE
from eztaskmanager.models import Task


class TaskQueueService(ABC):
    """
    Class: TaskQueueService

    Abstract base class for managing task queues.

    Methods:
    - add(task, at=None):
        - Abstract method.
        - Adds a task to the queue, for execution
        - Parameters:
            - task: The task to be added. Must be a valid task object.
            - at: Optional parameter representing the time at which the task should be launched.

    - remove(task):
        - Abstract method.
        - Removes a specific task from the queue.
        - Parameters:
            - task: The task to be dequeued. Must be a valid task object.
    """
    @abstractmethod
    def add(self, task):
        pass

    @abstractmethod
    def remove(self, task):
        pass


def get_task_service():

    if EZTASKMANAGER_QUEUE_SERVICE_TYPE == 'RQ':
        return RQTaskQueueService()
    else:
        return CeleryTaskQueueService()


class RQTaskQueueService(TaskQueueService):
    """
    A subclass of TaskQueueService that manages tasks using RQ (Redis Queue).

    Attributes:
        queue (Queue): The default RQ queue.

    Methods:
        - list_tasks(): Returns a list of all the tasks in the queue.
        - add(task, at=None): Enqueues a task to be executed either immediately or at a specific time.
        - remove(task): Cancels a task if it is currently in the queue.

    """

    def __init__(self):
        """
        Initializes an instance of the class.

        :param self: The current object instance.
        :type self: object

        :return: None
        """
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

        try:
            if task.scheduling:
                # schedule execution at a point in time, with periodicity
                rq_job = self.scheduler.schedule(
                    task.scheduling,
                    run_management_command, [task.id],
                    interval=task.interval_in_seconds,
                    result_ttl=int(1.5 * task.interval_in_seconds)
                )
                task.scheduled_job_id = rq_job.id
                task.status = Task.STATUS_SCHEDULED
                _, task.cached_next_ride = self.fetch_job_with_next_time(task)
                task.save()
            else:
                # enqueue for immediate execution
                rq_job = self.queue.enqueue(run_management_command, task.id)
            return rq_job
        except Exception as e:
            print(f"Error while launching task: {e}")

    def fetch_job_with_next_time(self, task):
        try:
            return next(
                (j, next_time) for j, next_time in self.scheduler.get_jobs(with_times=True)
                if j.id == task.scheduled_job_id
            )
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

