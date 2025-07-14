# Import the necessary libraries.
import os
from celery import Celery

# --- Django Integration ---
# This line is crucial for Celery to work with Django.
# It sets the DJANGO_SETTINGS_MODULE environment variable for the Celery command-line program.
# This tells Celery where to find your Django project's settings file.
# Replace 'hr_management_system.settings' with your actual project's settings path if it's different.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hr_management_system.settings')

# --- Celery Application Instance ---
# Here, we create an instance of the Celery application.
# We give it a name, which is typically the name of the Django project ('hr_management_system').
# This instance is the main entry point for everything Celery-related, like creating tasks and managing workers.
app = Celery('hr_management_system')

# --- Configuration ---
# This method configures the Celery instance using the settings from your Django settings.py file.
# The 'namespace="CELERY"' argument means that Celery will look for all configuration keys
# in your settings.py that start with the prefix "CELERY_".
# For example, it will find CELERY_BROKER_URL, CELERY_RESULT_BACKEND, etc.
app.config_from_object('django.conf:settings', namespace='CELERY')

# --- Task Discovery ---
# This method tells Celery to automatically find task modules in all of your installed Django apps.
# Celery will look for a file named 'tasks.py' in each app directory (e.g., 'portal/tasks.py').
# This is the standard way to organize your tasks and keep them modular.
app.autodiscover_tasks()

# --- Example Debug Task ---
# This is a simple example task to test if Celery is working correctly.
# The '@app.task' decorator registers this function as a Celery task.
# 'bind=True' means that the task will have access to a 'self' argument,
# which contains request information and context about the task's execution.
@app.task(bind=True)
def debug_task(self):
    # This will print the request context of the task to the Celery worker's console.
    # It's a useful way to debug and confirm that tasks are being executed.
    print(f'Request: {self.request!r}')
