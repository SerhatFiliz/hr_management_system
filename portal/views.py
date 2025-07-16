import json  # For working with JSON data format (used in our API view).
import re    # For using regular expressions (used to split the AI's response).
import requests # For making HTTP requests to external services (like the Hugging Face API).
import os  # For accessing environment variables (like API keys).
# --- Django Core Libraries ---
from django.conf import settings  # To access variables from our project's settings.py file (like API keys).
from django.contrib.auth.decorators import login_required # A function decorator to protect views by requiring login.
from django.contrib.auth.mixins import LoginRequiredMixin # A class mixin to protect views by requiring login.
from django.http import JsonResponse # To send responses in JSON format, used for our API view.
from django.shortcuts import get_object_or_404, redirect, render # Common utility functions.
from django.urls import reverse_lazy # To look up URL paths by their given name.
from django.views.decorators.csrf import csrf_exempt # To bypass security checks for our internal API view.
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView, DetailView # Django's built-in "factories" for common tasks.
from django.contrib import messages # To show messages to the user (like success or error notifications).

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
    Provides a confirmation page for deleting a job posting.
    """
    model = JobPosting
    success_url = reverse_lazy('dashboard')
    template_name = 'portal/job_posting_confirm_delete.html'

    def get_queryset(self):
        """
        CRITICAL METHOD (SECURITY): Same as in UpdateView, this ensures
        a user can ONLY delete objects that belong to their own company.
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
    Provides a confirmation page for deleting a Candidate profile.
    """
    # model: This view works with the Candidate model.
    model = Candidate
    
    # success_url: Redirects back to the dashboard after a successful deletion.
    success_url = reverse_lazy('dashboard')
    
    # template_name: The HTML file that will be used for the confirmation page.
    template_name = 'portal/candidate_confirm_delete.html'

    def get_queryset(self):
        """
        SECURITY FEATURE: Ensures a user can ONLY delete candidates
        that belong to their own company.
        """
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.user.employee.company)

    def form_valid(self, form):
        """
        Adds a success message when the form is successfully submitted (deletion is confirmed).
        """
        messages.success(self.request, f"Candidate profile for {self.object.first_name} {self.object.last_name} has been deleted.")
        return super().form_valid(form)

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
                settings.HUGGING_FACE_API_URL, 
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
