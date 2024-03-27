from enum import Enum


class TaskState(Enum):
    IDLE = 'idle'
    SCHEDULED = 'scheduled'
    STARTED = 'started'


class TaskService:

    @staticmethod
    def start_task(task):
        if task.state != TaskState.IDLE.value:
            raise Exception("Cannot start task that is not idle.")
        # start task. you'll need to implement this method
        task.state = TaskState.STARTED.value
        task.save()  # assuming task is a Django model

    @staticmethod
    def schedule_task(task, start_time):
        if task.state != TaskState.IDLE.value:
            raise Exception("Cannot schedule task that is not idle.")
        # schedule task for start_time. You'll need to implement this.
        task.state = TaskState.SCHEDULED.value
        task.save()

    @staticmethod
    def stop_task(task):
        if task.state != TaskState.STARTED.value:
            raise Exception("Cannot stop task that is not started.")
        # stop the task. You'll need to implement this.
        task.state = TaskState.IDLE.value
        task.save()