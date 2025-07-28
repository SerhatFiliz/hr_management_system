# Import the 'shared_task' decorator from Celery.
# This decorator allows you to create tasks without having to import the Celery app instance directly.
from celery import shared_task
import time
from django.utils import timezone
from .models import JobPosting, Candidate, Company # We need the Candidate model to create new profiles.
import PyPDF2 # The PDF library we just installed.

import io # A library to handle file streams in memory.
import base64 # A library to encode/decode binary data into text.
from django.contrib.auth.models import User
import os      # To safely access environment variables (like API keys).
import requests# To make HTTP requests to the external AI API.
import json    # To parse the JSON response from the AI.
from django.core.files.base import ContentFile # To save the in-memory file to the model.
import re

import google.generativeai as genai # The official Google Gemini Python library.

import redis  # Import redis to check for task results

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
    
#-----------------------------------------------------------------------------------------

# ==============================================================================
# REDIS CONNECTION SETUP
# ==============================================================================
# We establish a connection to our Redis service. This connection will be used
# to store the results of our CV processing tasks.
# We use the same Redis instance that Celery uses, but connect to a different database (db=1)
# to keep the task results separate from Celery's internal queues.
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, db=1)


# ==============================================================================
# CELERY TASK: process_single_cv
# ==============================================================================
@shared_task
def process_single_cv(file_content_b64, original_filename, company_id, created_by_id, create_candidate=True, task_id=None):
    """
    MODIFIED: This task now accepts an optional 'task_id' and stores its final result
    in Redis. It has been further improved to handle the 'skipped' case gracefully by
    always returning the parsed candidate data, even if the candidate already exists.
    This ensures the UI can display the information correctly while indicating the skipped status.
    """
    print(f"--- [Celery Task] Starting to PARSE CV: {original_filename} (Task ID: {task_id}) ---")
    
    final_result = {}

    try:
        # --- Step 1 & 2: Decode File and Parse with AI ---
        # This part remains the same. It extracts text and gets data from the AI.
        file_content = base64.b64decode(file_content_b64)
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        extracted_text = ""
        for page in pdf_reader.pages:
            extracted_text += page.extract_text() or ""

        if not extracted_text.strip():
            raise ValueError(f"Failed: No text found in {original_filename}")

        email, first_name, last_name = None, None, None
        try:
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
            prompt = (
                "You are an expert HR assistant. From the following CV text, extract the "
                "first_name, last_name, and email into a valid JSON object. "
                "If a piece of information cannot be found, set its value to null. "
                f"Return ONLY the JSON object. \n\nCV Text: ```{extracted_text[:10000]}```"
            )
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
            if not json_match:
                raise ValueError("No valid JSON found in AI response.")
            
            parsed_data = json.loads(json_match.group(0))
            email = parsed_data.get('email')
            first_name = parsed_data.get('first_name')
            last_name = parsed_data.get('last_name')
            print(f"[Celery Task] Successfully parsed data using AI for {original_filename}.")
        except Exception as api_error:
            print(f"[Celery Task] AI processing failed: {api_error}. Falling back to RegEx.")
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', extracted_text)
            if email_match: email = email_match.group(0)
            name_match = re.search(r'([A-Z][a-z]+)\s+([A-Z][a-z]+)', extracted_text)
            if name_match:
                first_name = name_match.group(1)
                last_name = name_match.group(2)
        
        if not email:
            raise ValueError(f"Failed: Email not found in {original_filename}")

        # --- Step 3: Prepare the base result dictionary ---
        # This dictionary will be used in all success/skipped scenarios.
        parsed_result = {
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'original_filename': original_filename,
            'file_content_b64': file_content_b64,
        }

        # --- Step 4: Decide whether to create the candidate ---
        if not create_candidate:
            # This path is used by the synchronous "Auto-fill" feature.
            final_result = parsed_result
            final_result['status'] = 'SUCCESS'
        else:
            # This path is used by the asynchronous Kafka/Celery process.
            if Candidate.objects.filter(email=email, company_id=company_id).exists():
                # =================================================================
                # ===== THE FIX: Handle the 'skipped' case correctly =====
                # =================================================================
                # Previously, we only returned a simple message. Now, we return the full
                # parsed data, but add a 'skipped' status and message to it.
                # This gives the frontend all the information it needs to render the row correctly,
                # while also informing the user that the candidate already exists.
                final_result = parsed_result
                final_result['status'] = 'SKIPPED'
                final_result['message'] = f"Candidate already exists."
                print(f"[Celery Task] Skipped creating candidate (already exists): {email}")
            else:
                # If the candidate is new, create them in the database.
                company = Company.objects.get(id=company_id)
                created_by_user = User.objects.get(id=created_by_id)
                
                new_candidate = Candidate.objects.create(
                    company=company,
                    first_name=first_name or "Unknown",
                    last_name=last_name or "Unknown",
                    email=email,
                    created_by=created_by_user.employee
                )
                new_candidate.resume.save(original_filename, ContentFile(file_content), save=True)
                print(f"[Celery Task] Successfully created new candidate: {email}")
                
                # The final result is the parsed data with a success status.
                final_result = parsed_result
                final_result['status'] = 'SUCCESS'
        
    except Exception as e:
        print(f"[Celery Task] CRITICAL ERROR processing {original_filename}: {e}")
        # If any error occurs, we prepare an error result.
        final_result = {'status': 'FAILURE', 'error': str(e)}

    # --- Step 5: Store the final result in Redis if a task_id was provided ---
    if task_id:
        try:
            # We store the result dictionary (which now always contains the candidate data on success/skip)
            # as a JSON string in Redis.
            redis_client.set(task_id, json.dumps(final_result), ex=3600)
            print(f"[Celery Task] Result for task_id {task_id} stored in Redis.")
        except Exception as redis_error:
            print(f"[Celery Task] CRITICAL: Could not store result for task_id {task_id} in Redis. Error: {redis_error}")

    return final_result
