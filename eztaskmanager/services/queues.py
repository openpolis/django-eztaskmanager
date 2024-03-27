from abc import ABC, abstractmethod

import django_rq
from django.conf import settings

from eztaskmanager.settings import EZTASKMANAGER_QUEUE_SERVICE_TYPE
from eztaskmanager.models import Task
from eztaskmanager.services import run_management_command


class TaskQueueService(ABC):
    """
    Class: TaskQueueService

    Abstract base class for managing task queues.

    Methods:
    - list_tasks():
        - Abstract method.
        - Returns a list of tasks in the queue.

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
    def list_tasks(self):
        pass

    @abstractmethod
    def add(self, task, at=None):
        pass

    @abstractmethod
    def remove(self, task):
        pass


def get_task_service():

    if EZTASKMANAGER_QUEUE_SERVICE_TYPE == 'RQ':
        return RQTaskQueueService()
    else:
        raise Exception("Invalid task queue service type. Celery not yet implemented")
        # return CeleryTaskQueueService(service_config)


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
    queue = django_rq.get_queue('default')
    scheduler = django_rq.get_scheduler('default')

    def list_tasks(self):
        try:
            jobs = self.queue.jobs
            return jobs
        except Exception as e:
            print(f"Error while listing tasks: {e}")

    def add(self, task: Task, at=None):
        try:
            if at:
                rq_job = self.scheduler.enqueue_at(at, run_management_command, task)
            else:
                rq_job = self.queue.enqueue(run_management_command, task)
            return rq_job
        except Exception as e:
            print(f"Error while launching task: {e}")

    def remove(self, task):
        try:
            jobs = self.queue.jobs
            for job in jobs:
                if job.func == task:
                    job.cancel()
        except Exception as e:
            print(f"Error while halting task: {e}")
