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
@shared_task
def process_single_cv(file_content_b64, original_filename, company_id, created_by_id):
    """
    Processes a single CV using an AI-first approach with a RegEx fallback.
    This task is designed to be robust and handle potential failures gracefully.
    """
    print(f"--- [Celery Task] Starting to process CV: {original_filename} ---")
    # This is the main try...except block. It's a safety net for the entire task.
    # If any completely unexpected error occurs, this will catch it and prevent the worker from crashing.
    try:
        # --- Step 1: Decode the File and Extract Raw Text ---
        # This part of the code is responsible for preparing the data for processing.
        file_content = base64.b64decode(file_content_b64)
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        extracted_text = ""
        for page in pdf_reader.pages:
            extracted_text += page.extract_text() or ""

        # If the PDF is empty or unreadable, we stop here.
        if not extracted_text.strip():
            print(f"[Celery Task] Could not extract text from {original_filename}.")
            return f"Failed: No text found in {original_filename}"

        # --- Initialize variables to hold the data we find ---
        email = None
        first_name = "Unknown"
        last_name = "Unknown"

        # This inner try...except block is for the AI part specifically.
        # It allows us to "try" the AI method first, and if it fails for ANY reason,
        # we can "catch" the error and switch to our fallback method without crashing the whole task.
        try:
            # --- Step 2 (Primary Method): Parse Information with the Google Gemini API ---
            # This is our preferred method. We always try this first.
            print(f"[Celery Task] Attempting to parse with Google Gemini API for {original_filename}...")
            genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

            # We create a very specific instruction ("prompt") for the AI.
            prompt = (
                "You are an expert HR assistant. From the following CV text, extract the "
                "first_name, last_name, and email into a valid JSON object. "
                "If a piece of information cannot be found, set its value to null. "
                f"Return ONLY the JSON object and nothing else. \n\nCV Text: ```{extracted_text[:10000]}```"
            )
            
            # We select the model and send our prompt to the Gemini API.
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            generated_text = response.text
            
            # We search for a JSON block within the AI's response.
            json_match = re.search(r'\{.*\}', generated_text, re.DOTALL)
            if not json_match:
                # If no JSON is found, we raise an error to trigger the 'except' block below.
                raise ValueError("No valid JSON found in AI response.")
                
            # If JSON is found, we parse it and extract the data.
            parsed_data = json.loads(json_match.group(0))
            email = parsed_data.get('email')
            first_name = parsed_data.get('first_name') or "Unknown"
            last_name = parsed_data.get('last_name') or "Unknown"
            print(f"[Celery Task] Successfully parsed data using AI for {original_filename}.")

        except Exception as api_error:
            # --- Step 2 (Fallback Method): If the AI method fails, this code runs. ---
            # This is our "Plan B". It makes our system resilient.
            print(f"[Celery Task] AI processing failed: {api_error}. Falling back to RegEx parser.")
            
            # We use a regular expression to find a standard email address in the ORIGINAL text.
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', extracted_text)
            if email_match:
                email = email_match.group(0)
                print(f"[Celery Task] Found email using RegEx fallback: {email}")

            # We use a simple regex to find a potential name (two capitalized words).
            name_match = re.search(r'([A-Z][a-z]+)\s+([A-Z][a-z]+)', extracted_text)
            if name_match:
                first_name = name_match.group(1)
                last_name = name_match.group(2)
                print(f"[Celery Task] Found potential name using RegEx fallback: {first_name} {last_name}")

        # --- Step 3: Validate Data and Create the Candidate Profile ---
        # This part of the code runs regardless of whether the data came from the AI or the RegEx fallback.
        
        # An email is essential. If we couldn't find one with either method, we stop.
        if not email:
            print(f"[Celery Task] Could not find an email in {original_filename} using any method. Skipping.")
            return f"Failed: Email not found in {original_filename}"

        # To prevent duplicates, we check if a candidate with this email already exists for this company.
        if Candidate.objects.filter(email=email, company_id=company_id).exists():
            print(f"[Celery Task] A candidate with the email {email} already exists. Skipping.")
            return f"Skipped: Candidate already exists for {original_filename}"

        # We fetch the related Company and User objects from the database using their IDs.
        company = Company.objects.get(id=company_id)
        created_by_user = User.objects.get(id=created_by_id)

        # We create the new Candidate object in the database with the data we found.
        new_candidate = Candidate.objects.create(
            company=company,
            first_name=first_name,
            last_name=last_name,
            email=email,
            created_by=created_by_user.employee # The model requires an Employee instance.
        )
        
        # We attach the original PDF file to the newly created candidate profile.
        new_candidate.resume.save(original_filename, ContentFile(file_content), save=True)

        print(f"[Celery Task] Successfully created new candidate: {new_candidate.first_name} {new_candidate.last_name}")
        return f"Successfully processed {original_filename} and created a new candidate."

    except Exception as e:
        # This is the final safety net. It catches any other unexpected errors.
        print(f"[Celery Task] CRITICAL ERROR processing {original_filename}: {e}")
        return f"Failed: {e}"
