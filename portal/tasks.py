# Import the 'shared_task' decorator from Celery.
# This decorator allows you to create tasks without having to import the Celery app instance directly.
from celery import shared_task
import time

from django.utils import timezone
from .models import JobPosting # We need to import our JobPosting model to interact with it.

#----------------------------------------------------------------------------------------

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

#----------------------------------------------------------------------------------------

# This is the new function that Celery Beat will run on a schedule.
@shared_task
def deactivate_expired_postings():
    """
    This task finds all active job postings whose closing date has passed
    and deactivates them.
    """
    # Get the current time. timezone.now() is Django's way of getting the current
    # time, and it's aware of the project's time zone settings.
    now = timezone.now()
    
    # Print a message to the worker's console so we know the task has started.
    print(f"Running deactivate_expired_postings task at {now}...")
    
    # This is the core of our logic. We query the database for JobPosting objects.
    # We are looking for postings that meet two conditions:
    # 1. is_active=True  -> The posting is currently active.
    # 2. closing_date__lt=now -> The posting's closing date is less than (lt) the current time.
    #    '__lt' is Django's syntax for 'less than'.
    expired_postings = JobPosting.objects.filter(is_active=True, closing_date__lt=now)
    
    # We check if the query found any expired postings.
    if expired_postings.exists():
        # .update() is a very efficient way to update multiple objects at once.
        # It performs a single database query to set 'is_active' to False for all
        # found postings, instead of looping through them one by one.
        count = expired_postings.update(is_active=False)
        
        # We print a success message showing how many postings were updated.
        message = f"Successfully deactivated {count} expired job posting(s)."
        print(message)
        return message
    else:
        # If no expired postings were found, we also print a message.
        message = "No expired job postings to deactivate."
        print(message)
        return message