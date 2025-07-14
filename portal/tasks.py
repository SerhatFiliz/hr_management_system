# Import the 'shared_task' decorator from Celery.
# This decorator allows you to create tasks without having to import the Celery app instance directly.
from celery import shared_task
import time

# The '@shared_task' decorator registers this function as a Celery task.
# This means the Celery worker can find and execute it.
@shared_task
def test_task():
    """
    A simple test task that prints a message to the worker's console.
    """
    # We will print a message to see if the task starts.
    print("Test task started...")
    # We add a 5-second delay to simulate a long-running task.
    # This helps confirm that the task is running asynchronously in the background.
    time.sleep(5)
    # We print another message to confirm the task has finished.
    print("Test task finished!")
    return "Task completed successfully!"