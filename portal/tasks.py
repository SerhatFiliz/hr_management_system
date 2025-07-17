# Import the 'shared_task' decorator from Celery.
# This decorator allows you to create tasks without having to import the Celery app instance directly.
from celery import shared_task
import time
from django.utils import timezone
from .models import JobPosting, Candidate # We need the Candidate model to create new profiles.
import PyPDF2 # The PDF library we just installed.
import io # A library to handle file streams in memory.
import base64 # A library to encode/decode binary data into text.


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

# The '@shared_task' decorator registers this function as a Celery task.
# This means it can be called asynchronously and will be executed by a Celery worker.
@shared_task
def process_single_cv(file_content_b64, original_filename, company_id, created_by_id):
    """
    Processes a single uploaded CV file in the background.
    
    This task receives the file content and necessary IDs, extracts the text from the PDF,
    and (in the future) will send this text to an AI service to create a candidate profile.

    Args:
        file_content_b64 (str): The binary content of the PDF file, encoded as a base64 string.
                                We use base64 because it's a safe way to pass binary data
                                through Celery's messaging system (which prefers text).
        original_filename (str): The original name of the uploaded file, used for logging.
        company_id (int): The ID of the company to associate the new candidate with.
        created_by_id (int): The ID of the user who uploaded the CV.
    """
    print(f"--- [Celery Task] Starting to process CV: {original_filename} ---")
    try:
        # Step 1: Decode the file content.
        # The file content arrives as a base64 text string. We need to decode it
        # back into its original binary form before we can read it as a PDF.
        file_content = base64.b64decode(file_content_b64)
        
        # Step 2: Read the PDF from memory.
        # Instead of saving the file to the disk first, we use 'io.BytesIO'.
        # This creates a temporary, in-memory binary file, which is more efficient.
        pdf_file = io.BytesIO(file_content)
        
        # Step 3: Use PyPDF2 to read the PDF structure.
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        
        # Step 4: Extract text from all pages of the PDF.
        extracted_text = ""
        for page in pdf_reader.pages:
            # We add the text from each page to our 'extracted_text' string.
            # 'or ""' is a safety measure in case a page has no text.
            extracted_text += page.extract_text() or ""

        # Step 5: Validate the extracted text.
        # If the text is empty or just whitespace, we can't process it.
        if not extracted_text.strip():
            print(f"[Celery Task] Could not extract any text from {original_filename}.")
            return f"Failed: No text found in {original_filename}"

        print(f"[Celery Task] Successfully extracted text from {original_filename}. Length: {len(extracted_text)} chars.")
        
        # --- NEXT STEP (To be implemented) ---
        # This is where the magic will happen. We will add the logic to:
        # 1. Send this 'extracted_text' to an AI API.
        # 2. The AI will return structured data (e.g., {'first_name': 'John', 'last_name': 'Doe', 'email': 'john.doe@email.com'}).
        # 3. We will use that data to create a new Candidate object in the database.
        #
        # For now, we just print the first 200 characters to confirm text extraction works.
        print("[Celery Task] Extracted Text (first 200 chars):", extracted_text[:200])
        
        # Example of what the future code will look like:
        # ai_data = call_ai_service(extracted_text)
        # Candidate.objects.create(
        #     first_name=ai_data.get('first_name'),
        #     last_name=ai_data.get('last_name'),
        #     email=ai_data.get('email'),
        #     company_id=company_id,
        #     created_by_id=created_by_id
        # )

        return f"Successfully processed {original_filename}"

    except Exception as e:
        # This is a general catch-all for any unexpected errors during the process
        # (e.g., a corrupted PDF file). We log the error to the console.
        print(f"[Celery Task] CRITICAL ERROR processing {original_filename}: {e}")
        return f"Failed: {e}"
    
    """
    If a task is user-initiated (a button click, a form submission, etc.), we need a View to handle that request.
    If a task is time-initiated (every night at 4:00, every hour, etc.), we need a Celery Beat timer, not a View, to handle that request.
    """