import json  # For working with JSON data format (used in our API view).
import re    # For using regular expressions (used to split the AI's response).
import requests # For making HTTP requests to external services (like the Hugging Face API).
import os  # For accessing environment variables (like API keys).
# --- Django Core Libraries ---
from django.views import View # The base class for creating class-based views.
from django.conf import settings  # To access variables from our project's settings.py file (like API keys).
from django.contrib.auth.decorators import login_required # A function decorator to protect views by requiring login.
from django.contrib.auth.mixins import LoginRequiredMixin # A class mixin to protect views by requiring login.
from django.http import JsonResponse # To send responses in JSON format, used for our API view.
from django.shortcuts import get_object_or_404, redirect, render # Common utility functions.
from django.urls import reverse_lazy # To look up URL paths by their given name.
from django.views.decorators.csrf import csrf_exempt # To bypass security checks for our internal API view.
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView, DetailView # Django's built-in "factories" for common tasks.
from django.contrib import messages # To show messages to the user (like success or error notifications).

from .tasks import process_single_cv # We import our new Celery task.
import base64 # We need this to encode the file content.
from django.core.files.base import ContentFile
from django.urls import reverse

# --- Local Application Imports ---
# Imports from other files within this 'portal' app. The '.' means 'from the same directory'.
from .forms import CandidateForm, JobPostingForm, ApplicationForm, ApplicationStatusForm
from .models import Candidate, Employee, JobPosting, Application


class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Displays the main dashboard, acting as the central hub for the user.
    """
    template_name = 'portal/dashboard.html'

    def get_context_data(self, **kwargs):
        """
        CRITICAL METHOD: This method prepares and sends data from our Python
        backend to the HTML template. It's how our template knows what to display.
        """
        context = super().get_context_data(**kwargs)
        
        try:
            employee = self.request.user.employee
            context['company'] = employee.company
            context['job_postings'] = JobPosting.objects.filter(company=employee.company)
            context['candidates'] = Candidate.objects.filter(company=employee.company)
        except Employee.DoesNotExist:
            # Safely handle cases where a user (like a superuser) has no employee profile.
            context['company'] = None
            context['job_postings'] = []
            context['candidates'] = []

        context['user'] = self.request.user
        return context

"""
# --- Function-Based Equivalent for DashboardView ---
@login_required
def dashboard_function(request):
    context = {}
    try:
        employee = request.user.employee
        context['company'] = employee.company
        context['job_postings'] = JobPosting.objects.filter(company=employee.company)
        context['candidates'] = Candidate.objects.filter(company=employee.company)
    except Employee.DoesNotExist:
        context['company'] = None
        context['job_postings'] = []
        context['candidates'] = []
    
    context['user'] = request.user
    return render(request, 'portal/dashboard.html', context)
"""
#-----------------------------------------------------------------------------------------------------------

class JobPostingCreateView(LoginRequiredMixin, CreateView):
    """
    Provides a form to create a new job posting.
    """
    model = JobPosting
    form_class = JobPostingForm
    template_name = 'portal/job_posting_editor.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        """
        CRITICAL METHOD: This method is called after the form is submitted and
        validated, but just before it's saved to the database. We use it
        to add data that the user didn't provide, like the creator's identity.
        """
        form.instance.company = self.request.user.employee.company
        form.instance.created_by = self.request.user.employee
        return super().form_valid(form)

"""
# --- Function-Based Equivalent for JobPostingCreateView ---
@login_required
def job_posting_create_function(request):
    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        if form.is_valid():
            job_posting = form.save(commit=False)
            job_posting.company = request.user.employee.company
            job_posting.created_by = request.user.employee
            job_posting.save()
            return redirect('dashboard')
    else:
        form = JobPostingForm()
    return render(request, 'portal/job_posting_editor.html', {'form': form})
"""
#-----------------------------------------------------------------------------------------------------------

class JobPostingUpdateView(LoginRequiredMixin, UpdateView):
    """
    Provides a form to edit an existing job posting.
    """
    model = JobPosting
    form_class = JobPostingForm
    template_name = 'portal/job_posting_editor.html'
    success_url = reverse_lazy('dashboard')

    def get_queryset(self):
        """
        CRITICAL METHOD (SECURITY): This method filters which objects the user
        is allowed to see or edit. By filtering for the user's company, we
        prevent them from accessing data from other companies.
        """
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.user.employee.company)

"""
# --- Function-Based Equivalent for JobPostingUpdateView ---
@login_required
def job_posting_update_function(request, pk):
    job_posting = get_object_or_404(JobPosting, pk=pk, company=request.user.employee.company)
    if request.method == 'POST':
        form = JobPostingForm(request.POST, instance=job_posting)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        form = JobPostingForm(instance=job_posting)
    return render(request, 'portal/job_posting_editor.html', {'form': form})
"""
#-----------------------------------------------------------------------------------------------------------

class JobPostingDeleteView(LoginRequiredMixin, DeleteView):
    """
    Handles the deletion of a JobPosting object.
    
    This view is specifically designed to work with the AJAX request sent
    from the dashboard's JavaScript. It returns a JSON response to signal
    success or failure, instead of redirecting the entire page.
    """
    # 1. model: Specifies that this view operates on the 'JobPosting' model.
    model = JobPosting
    
    # 2. success_url: This is a fallback. If a non-AJAX request ever reaches this
    #    view, it will redirect to the dashboard after deletion.
    success_url = reverse_lazy('dashboard')

    def post(self, request, *args, **kwargs):
        """
        Overrides the default post method to handle our custom logic.
        This method is triggered when our JavaScript sends the 'POST' request.
        """
        # Get the specific JobPosting object that the user wants to delete.
        self.object = self.get_object()
        
        # Check the request headers to see if it's an AJAX call.
        # Our JavaScript adds the 'X-Requested-With' header to identify itself.
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if is_ajax:
            # If it's an AJAX request, delete the object from the database.
            self.object.delete()
            # Return a JSON response with a success flag.
            # Our JavaScript will receive this and know it can remove the row from the table.
            return JsonResponse({'success': True})
        else:
            # If it's a standard browser request (not from our script),
            # let the parent DeleteView handle it, which will result in a redirect.
            return super().post(request, *args, **kwargs)

    def get_queryset(self):
        """
        A crucial security feature. This ensures that users can only delete jobs 
        that belong to their own company. It prevents a user from guessing a URL
        (e.g., /jobs/123/delete/) and deleting another company's data.
        """
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.user.employee.company)

"""
# --- Function-Based Equivalent for JobPostingDeleteView ---
@login_required
def job_posting_delete_function(request, pk):
    job_posting = get_object_or_404(JobPosting, pk=pk, company=request.user.employee.company)
    if request.method == 'POST':
        job_posting.delete()
        return redirect('dashboard')
    return render(request, 'portal/job_posting_confirm_delete.html', {'object': job_posting})
"""
#-----------------------------------------------------------------------------------------------------------

class CandidateCreateView(LoginRequiredMixin, CreateView):
    """
    Provides a form to create a new candidate profile, including resume upload.
    """
    model = Candidate
    form_class = CandidateForm
    template_name = 'portal/candidate_editor.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        """
        CRITICAL METHOD: Just like when creating a job posting, this method
        automatically assigns the correct company and creator to the new
        candidate profile before saving.
        """
        form.instance.company = self.request.user.employee.company
        form.instance.created_by = self.request.user.employee
        return super().form_valid(form)

"""
# --- Function-Based Equivalent for CandidateCreateView ---
@login_required
def candidate_create_function(request):
    if request.method == 'POST':
        # request.FILES is necessary to handle file uploads
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.company = request.user.employee.company
            candidate.created_by = request.user.employee
            candidate.save()
            return redirect('dashboard')
    else:
        form = CandidateForm()
    return render(request, 'portal/candidate_editor.html', {'form': form})
"""
#-----------------------------------------------------------------------------------------------------------
class CandidateUpdateView(LoginRequiredMixin, UpdateView):
    """
    Handles the updating of an existing Candidate profile.
    """
    # model: This view works with the Candidate model.
    model = Candidate
    
    # form_class: It reuses the same form we use for creating candidates.
    form_class = CandidateForm
    
    # template_name: It reuses the same editor template.
    template_name = 'portal/candidate_editor.html'
    
    # success_url: Redirects back to the dashboard after a successful update.
    success_url = reverse_lazy('dashboard')

    def get_queryset(self):
        """
        SECURITY FEATURE: Ensures a user can ONLY edit candidates
        that belong to their own company.
        """
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.user.employee.company)

    def form_valid(self, form):
        """
        Adds a success message when the form is successfully updated.
        """
        messages.success(self.request, f"Candidate profile for {self.object.first_name} {self.object.last_name} has been updated.")
        return super().form_valid(form)
    
#-----------------------------------------------------------------------------------------------------------
class CandidateDeleteView(LoginRequiredMixin, DeleteView):
    """
    Handles the deletion of a Candidate profile.
    This view is now updated to handle both standard browser requests
    and modern AJAX requests from our dashboard.
    """
    # model: This view works with the Candidate model.
    model = Candidate
    
    # success_url: Redirects back to the dashboard. This is now used as a 
    # fallback for non-AJAX requests.
    success_url = reverse_lazy('dashboard')
    
    # template_name: The HTML file for the confirmation page. This is also
    # a fallback for users without JavaScript or for direct navigation to the URL.
    template_name = 'portal/candidate_confirm_delete.html'

    def get_queryset(self):
        """
        SECURITY FEATURE: This method is unchanged and is crucial.
        It ensures a user can ONLY see or delete candidates that belong 
        to their own company, preventing unauthorized access.
        """
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.user.employee.company)

    def form_valid(self, form):
        """
        MODIFIED: This method is called when a POST request is valid.
        We've updated it to differentiate between an AJAX request and a 
        standard form submission.
        """
        # First, we check if the incoming request is an AJAX request.
        # Our JavaScript adds the 'X-Requested-With' header, which we check for here.
        is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        if is_ajax:
            # If it's an AJAX request:
            # 1. We perform the deletion by calling the parent's method.
            super().form_valid(form)
            # 2. We return a JSON response to signal success to our JavaScript.
            #    We don't add a message because there's no page reload to display it.
            #    The success is shown visually by removing the row from the table.
            return JsonResponse({'success': True})
        else:
            # If it's a standard browser request (non-AJAX):
            # 1. We add a success message that will be displayed on the next page.
            messages.success(self.request, f"Candidate profile for {self.object.first_name} {self.object.last_name} has been deleted.")
            # 2. We call the parent's method, which will handle the deletion
            #    and return the standard HttpResponseRedirect to the 'success_url'.
            return super().form_valid(form)

    def post(self, request, *args, **kwargs):
        """
        We are overriding the post method to call form_valid.
        This ensures our logic in form_valid runs correctly.
        DeleteView by default may not use a form, so explicitly calling
        form_valid from post makes our logic robust.
        """
        self.object = self.get_object()
        # The 'form' argument to form_valid can be a dummy one as DeleteView doesn't rely on its contents.
        form = self.get_form() 
        return self.form_valid(form)
#-----------------------------------------------------------------------------------------------------------
class JobPostingDetailView(LoginRequiredMixin, DetailView):
    """
    Displays the details of a single JobPosting.
    This view is responsible for showing a specific job posting and, eventually,
    the list of candidates who have applied for it.
    """
    # model: Tells the DetailView which database table to look into.
    model = JobPosting
    
    # template_name: Specifies the HTML file that will be used to display the details.
    # We will create this file in the next steps.
    template_name = 'portal/job_posting_detail.html'
    
    # context_object_name: This sets the name of the variable that will hold the
    # JobPosting object in our template. Instead of the default 'object',
    # we'll use 'job_posting' which is more descriptive.
    context_object_name = 'job_posting'

    def get_queryset(self):
        """
        SECURITY FEATURE: This is a critical method for security.
        It ensures that a user can only view the details of job postings
        that belong to their own company. It filters the objects before
        the DetailView tries to find one by its ID (pk).
        """
        # Get the default queryset (which is all JobPosting objects).
        queryset = super().get_queryset()
        # Filter it down to only the objects associated with the current user's company.
        return queryset.filter(company=self.request.user.employee.company)


"""
# --- Function-Based Equivalent for JobPostingDetailView ---
# The @login_required decorator does the same job as LoginRequiredMixin.
@login_required
def job_posting_detail_function(request, pk):
    # This single line does the work of both 'model' and 'get_queryset'.
    # It tries to get a JobPosting object with the given 'pk'.
    # CRUCIALLY, it will only find it if the object's company matches
    # the logged-in user's company. Otherwise, it raises a 404 Not Found error.
    job_posting = get_object_or_404(JobPosting, pk=pk, company=request.user.employee.company)
    
    # This creates the context dictionary that will be sent to the template.
    # This line is the equivalent of 'context_object_name = "job_posting"'.
    context = {
        'job_posting': job_posting
    }
    
    # This renders the specified template with the context data.
    # This line is the equivalent of 'template_name = "..."'.
    return render(request, 'portal/job_posting_detail.html', context)
"""

#-----------------------------------------------------------------------------------------------------------

# These decorators run before the view function. They are like security guards.
@csrf_exempt      # This guard allows requests from our JavaScript without a standard form CSRF token.
@login_required   # This guard checks if the user is logged in before allowing them to proceed.
def generate_job_title_view(request):
    """
    Acts as a private API endpoint. It does not render a page but
    communicates with an external AI service and returns data (JSON).
    """
    # First, we only allow this function to work if data is being SENT to it.
    if request.method == 'POST':
        # We wrap the entire process in a try...except block. This is a safety net.
        # If anything goes wrong (e.g., internet is down, AI service is busy),
        # the 'except' block will catch the error and prevent our server from crashing.
        try:
            # Get the raw data sent from the JavaScript 'fetch' call.
            data = json.loads(request.body)
            # Safely get the 'description' value from the data. If it doesn't exist, use an empty string.
            description = data.get('description', '')

            # If the user didn't send any description text, return an error immediately.
            if not description:
                return JsonResponse({'error': 'Description cannot be empty.'}, status=400)

            # This is the data package (payload) we will send to the Hugging Face API.
            # It contains the text we want the AI to process.
            api_payload = {
                "inputs": description,
                "parameters": {"max_length": 50, "min_length": 5}
            }
            
            # This is our "ID card" for the API. It proves we have permission to use the service.
            # The secret key is read safely from settings.py, which reads it from the .env file.
            headers = {"Authorization": f"Bearer {settings.HUGGING_FACE_API_KEY}"}

            # This is where our server talks to the outside world.
            # It sends our payload and headers to the AI service and waits for a response.
            # The 'timeout=30' prevents our server from waiting forever if the AI is slow.
            response = requests.post(
                settings.AI_SUMMARIZATION_MODEL_URL, 
                headers=headers, 
                json=api_payload,
                timeout=30
            )

            # This is a smart way to handle API errors. If the response is not successful (e.g., 404, 500),
            # this block tries to give a more user-friendly error message.
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    api_error_message = error_data.get('error', 'Unknown API error.')
                    # Specifically check if the error is because the AI model is loading.
                    if 'is currently loading' in api_error_message:
                        estimated_time = error_data.get('estimated_time', 20)
                        user_message = f"The AI model is currently warming up. Please try again in {estimated_time:.0f} seconds."
                        return JsonResponse({'error': user_message}, status=503) # 503 means "Service Unavailable"
                    return JsonResponse({'error': f"API Error: {api_error_message}"}, status=response.status_code)
                except json.JSONDecodeError:
                    return JsonResponse({'error': f"API returned a non-JSON response: {response.text}"}, status=response.status_code)

            # If the request was successful, parse the JSON response from the AI.
            result = response.json()
            
            # Prepare a default title, just in case the AI fails to generate one.
            generated_title = "New Job Posting"
            # Safely check if the response is in the expected format (a list with at least one item).
            if result and isinstance(result, list) and len(result) > 0:
                # Safely get the 'summary_text' from the response.
                title_from_api = result[0].get('summary_text')
                if title_from_api:
                    # This is our logic to fix the "long sentence" problem.
                    # We split the summary into sentences and take only the first one.
                    sentences = re.split(r'(?<=[.!?])\s+', title_from_api)
                    if sentences and sentences[0]:
                        generated_title = sentences[0]

            # Send the final, cleaned title back to the JavaScript that made the request.
            return JsonResponse({'title': generated_title.strip()})

        # This catches specific errors, like the request taking too long.
        except requests.exceptions.Timeout:
            return JsonResponse({'error': 'The request to the AI model timed out. The model might be loading. Please try again.'}, status=504)
        # This is a general catch-all for any other unexpected errors.
        except Exception as e:
            return JsonResponse({'error': f'An unexpected server error occurred: {str(e)}'}, status=500)

    # If the request was not a POST, return an error.
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

#-----------------------------------------------------------------------------------------------------------
class ApplicationCreateView(LoginRequiredMixin, CreateView):
    """
    Handles the creation of a new Application, linking a Candidate to a JobPosting.
    """
    model = Application
    form_class = ApplicationForm
    template_name = 'portal/application_form.html'

    def get_context_data(self, **kwargs):
        """
        CRITICAL: Adds the specific 'job_posting' object to the context.
        This makes the job posting's details (like its title and pk)
        available for use directly within the template.
        """
        context = super().get_context_data(**kwargs)
        # Get the JobPosting object from the URL's pk and add it to the context.
        context['job_posting'] = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        return context

    def get_form_kwargs(self):
        """
        This method passes the 'job_posting' object to the ApplicationForm's
        __init__ method, so the form can correctly filter the candidate list.
        """
        kwargs = super().get_form_kwargs()
        kwargs['job_posting'] = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        return kwargs

    def form_valid(self, form):
        """
        This method automatically sets the 'job_posting' for the new application
        before it is saved to the database.
        """
        job_posting = get_object_or_404(JobPosting, pk=self.kwargs['pk'])
        form.instance.job_posting = job_posting
        
        messages.success(self.request, f"Successfully applied {form.instance.candidate.first_name} to the job '{job_posting.title}'.")
        
        return super().form_valid(form)

    def get_success_url(self):
        """
        Redirects the user back to the detail page of the job posting
        after a successful application.
        """
        return reverse_lazy('job-detail', kwargs={'pk': self.object.job_posting.pk})
    
    
#------------------------------------------------------------------------------------------------------------
class ApplicationUpdateView(LoginRequiredMixin, UpdateView):
    """
    Handles updating the status of an existing Application.
    """
    # model: This view works with the Application model.
    model = Application
    
    # form_class: It uses the simple form we just created.
    form_class = ApplicationStatusForm
    
    # template_name: The HTML file that will render the form.
    template_name = 'portal/application_status_form.html'

    def get_context_data(self, **kwargs):
        """
        Adds the application object itself to the context. This is useful
        for displaying details about the application on the form page,
        like the candidate's name and the job title.
        """
        context = super().get_context_data(**kwargs)
        # The 'object' is automatically provided by DetailView/UpdateView.
        # We add it to the context with a more descriptive name.
        context['application'] = self.get_object()
        return context

    def get_queryset(self):
        """
        SECURITY FEATURE: This is a critical security method.
        It ensures a user can ONLY update applications that belong to a job
        posting from their own company.
        """
        queryset = super().get_queryset()
        # The 'job_posting__company' lookup traverses the foreign key relationship.
        return queryset.filter(job_posting__company=self.request.user.employee.company)

    def get_success_url(self):
        """
        Redirects the user back to the detail page of the job posting
        to which the application belongs.
        """
        # self.object refers to the Application instance that was just updated.
        return reverse_lazy('job-detail', kwargs={'pk': self.object.job_posting.pk})

    def form_valid(self, form):
        """
        Adds a success message when the form is successfully updated.
        """
        messages.success(self.request, f"Status for {self.object.candidate.first_name}'s application has been updated.")
        return super().form_valid(form)

#-----------------------------------------------------------------------------------------------------------
"""
# We use a class-based view (CBV) for better organization of GET and POST logic.
# LoginRequiredMixin is a security feature. It acts as a guard, ensuring that
# only logged-in users can access this page. If a non-logged-in user tries to
# access it, they will be redirected to the login page.
class BulkCVUploadView(LoginRequiredMixin, View):
    
    # Handles the bulk CV upload page.
    # - The get() method displays the upload form.
    # - The post() method handles the submitted files and delegates them to Celery.
    
    def get(self, request, *args, **kwargs):
        
        # This method is called when a user visits the page with a GET request.
        # Its only job is to render and display the 'bulk_cv_upload.html' template.
         
        return render(request, 'portal/bulk_cv_upload.html')

    def post(self, request, *args, **kwargs):
        
        # This method is called when the user submits the form (a POST request).
        # This is where the main logic happens.
        
        # 'request.FILES' is a dictionary-like object that holds all uploaded files.
        # We use .getlist('cv_files') to get all files uploaded with the name 'cv_files'
        # from our HTML form's <input type="file" name="cv_files" multiple> tag.
        cv_files = request.FILES.getlist('cv_files')
        
        # A simple validation to check if any files were actually selected by the user.
        if not cv_files:
            messages.error(request, "No files were selected for upload.")
            return redirect('candidate-bulk-upload')

        # --- DELEGATING TO CELERY ---
        # Instead of processing the files here and making the user wait,
        # we loop through the files and create a background job for each one.
        for cv_file in cv_files:
            # We read the entire binary content of the uploaded file.
            file_content = cv_file.read()
            # We then encode this binary content into a base64 text string.
            # This is a safe and reliable way to pass file data as an argument
            # to a Celery task, as Celery's messaging system prefers text.
            file_content_b64 = base64.b64encode(file_content).decode('utf-8')
            
            # This is the key step. We call our task with '.delay()'.
            # '.delay()' is a shortcut to send the task to the Celery queue (Redis).
            # It immediately returns without waiting for the task to finish.
            # We pass all the necessary information for the task to run independently.
            process_single_cv.delay(
                file_content_b64,              # The encoded content of the CV file.
                cv_file.name,                   # The original filename for logging.
                request.user.employee.company.id, # The ID of the company.
                request.user.id                 # The ID of the user who uploaded the file.
            )

        # Provide immediate feedback to the user that their request has been accepted.
        messages.success(request, f"{len(cv_files)} CVs have been successfully queued for processing. You can continue working.")
        
        # Redirect the user back to the dashboard. They don't have to wait.
        return redirect('dashboard')
"""

# ==============================================================================
# VIEW 1: BulkCVUploadView
# Description: A simple Class-Based View (CBV) to display the initial upload page.
# ==============================================================================
class BulkCVUploadView(LoginRequiredMixin, View):
    """
    Handles displaying the interactive bulk CV upload page.
    The 'LoginRequiredMixin' ensures that only logged-in users can access this page.
    """
    def get(self, request, *args, **kwargs):
        """
        This method is called when a user navigates to this page with a GET request.
        Its only job is to render and return the corresponding HTML template.
        All the complex logic is now handled by the JavaScript on that page and the API views below.
        """
        return render(request, 'portal/bulk_cv_upload.html')

#-------------------------------------------------------------------------------------------

# ==============================================================================
# API VIEW 1: The CV Parser (For the Bulk Upload feature)
# Description: A Function-Based View (FBV) that acts as an API endpoint.
#              Its sole purpose is to receive a CV file and return parsed data.
# ==============================================================================

# @csrf_exempt: This decorator is used because our JavaScript 'fetch' call sends the CSRF token
#               in a header, not as a standard form field. This tells Django to allow the request.
# @login_required: Ensures only authenticated users can use this API endpoint.
@csrf_exempt
@login_required
def parse_cv_api_view(request):
    """
    API endpoint that receives a single CV file, processes it to extract
    information, but DOES NOT save it to the database.
    It returns the extracted information as JSON for the frontend JavaScript.
    """
    # Step 1: Check if the request is a POST request and contains a file. This is a security and validation step.
    if request.method == 'POST' and request.FILES.get('cv_file'):
        
        # Step 2: Get the file object from the request.
        cv_file = request.FILES['cv_file']
        
        # Step 3: Read the binary content of the file and encode it into a Base64 string.
        # Base64 is a safe way to transport binary data (like a PDF) within text-based systems like JSON or Celery tasks.
        file_content_b64 = base64.b64encode(cv_file.read()).decode('utf-8')
        
        # Step 4: Call our main background task/function ('process_single_cv') to do the actual work.
        # This view acts as a "bridge" to our core logic. We explicitly tell it NOT to create a candidate.
        result_data = process_single_cv(
            file_content_b64,
            cv_file.name,
            request.user.employee.company.id,
            request.user.id,
            create_candidate=False  # CRITICAL: This ensures we only parse the data, not save it.
        )
        
        # Step 5: Check the result from the task.
        if isinstance(result_data, dict) and 'error' not in result_data:
            # If the result is a dictionary without an error key, it was successful.
            # Return the data as a JSON response with a 200 OK status.
            return JsonResponse(result_data)
        else:
            # If the task returned an error, package it into a JSON error response.
            error_message = result_data.get('error') if isinstance(result_data, dict) else str(result_data)
            # Return with a status of 400 (Bad Request) to indicate a client-side or processing error.
            return JsonResponse({'error': error_message, 'original_filename': cv_file.name}, status=400)
            
    # If the request is not POST or doesn't have a file, return a generic error.
    return JsonResponse({'error': 'Invalid request.'}, status=400)


# ==============================================================================
# API VIEW 2: The Candidate Saver (For the Bulk Upload feature)
# Description: This API endpoint receives the final, user-approved list of candidates
#              from the bulk upload page and saves them to the database.
# ==============================================================================
@csrf_exempt
@login_required
def save_candidates_api_view(request):
    """
    API endpoint that receives a list of approved candidate data in JSON format,
    creates the Candidate objects, and saves their resume files.
    """
    if request.method == 'POST':
        try:
            # Step 1: Parse the JSON data sent in the body of the request from our JavaScript.
            data = json.loads(request.body)
            candidates_to_save = data.get('candidates', [])
            
            # Step 2: Loop through each candidate object in the received list.
            for cand_data in candidates_to_save:
                email = cand_data.get('email')
                
                # Step 3: Check if a candidate with this email already exists for this company to avoid duplicates.
                if email and not Candidate.objects.filter(email=email, company=request.user.employee.company).exists():
                    
                    # Step 4: Create a new Candidate object in the database with the provided data.
                    new_candidate = Candidate.objects.create(
                        company=request.user.employee.company,
                        first_name=cand_data.get('first_name', 'Unknown'),
                        last_name=cand_data.get('last_name', 'Unknown'),
                        email=email,
                        created_by=request.user.employee
                    )
                    
                    # Step 5: Handle the resume file.
                    file_content_b64 = cand_data.get('file_content_b64')
                    original_filename = cand_data.get('original_filename', 'resume.pdf')
                    
                    if file_content_b64:
                        # Decode the Base64 string back into its original binary bytes.
                        file_content = base64.b64decode(file_content_b64)
                        # Use Django's 'ContentFile' to treat these bytes as a file and save it to the 'resume' field.
                        new_candidate.resume.save(original_filename, ContentFile(file_content), save=True)

            # Step 6: After the loop finishes, return a successful JSON response.
            # This response includes a 'redirect_url', which the JavaScript will use to navigate the user to the dashboard.
            return JsonResponse({
                'success': True,
                'message': f'{len(candidates_to_save)} candidates were processed.',
                'redirect_url': reverse('dashboard')
            })

        except Exception as e:
            # If any part of the process fails, catch the exception and return a server error response.
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Invalid request method.'}, status=405)


# ==============================================================================
# API VIEW 3: The CV Parser (For the Auto-fill feature)
# Description: This is a new, dedicated API endpoint for the "Auto-fill from CV" button
#              on the single candidate creation form.
# ==============================================================================
@csrf_exempt
@login_required
def parse_cv_for_autofill_api(request):
    """
    API endpoint that receives a single CV file, calls our existing AI task to parse it,
    and returns the extracted data as JSON to the form's JavaScript.
    It is architecturally clean to have a separate endpoint for this distinct feature.
    """
    # Step 1: Check for a POST request with a file.
    if request.method == 'POST' and request.FILES.get('cv_file'):
        
        # Step 2: Get the file and encode it to Base64.
        cv_file = request.FILES['cv_file']
        file_content_b64 = base64.b64encode(cv_file.read()).decode('utf-8')
        
        # Step 3: REUSE our main 'process_single_cv' task. This is efficient and avoids code duplication.
        result_data = process_single_cv(
            file_content_b64=file_content_b64,
            original_filename=cv_file.name,
            company_id=request.user.employee.company.id,
            created_by_id=request.user.id,
            create_candidate=False # Again, we ensure no candidate is created here.
        )
        
        # Step 4: Check the result and return the appropriate JSON response.
        if isinstance(result_data, dict) and 'error' not in result_data:
            return JsonResponse(result_data)
        else:
            error_message = result_data.get('error') if isinstance(result_data, dict) else str(result_data)
            return JsonResponse({'error': error_message}, status=400)
            
    return JsonResponse({'error': 'Invalid request. A file must be provided.'}, status=400)