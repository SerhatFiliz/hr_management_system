# portal/views.py

# --- Standard Python Libraries ---
import json  # For working with JSON data format (used in our API view).
import re    # For using regular expressions (used to split the AI's response).
import requests # For making HTTP requests to external services (like the Hugging Face API).

# --- Django Core Libraries ---
from django.conf import settings  # To access variables from our project's settings.py file (like API keys).
from django.contrib.auth.decorators import login_required # A function decorator to protect views by requiring login.
from django.contrib.auth.mixins import LoginRequiredMixin # A class mixin to protect views by requiring login.
from django.http import JsonResponse # To send responses in JSON format, used for our API view.
from django.shortcuts import get_object_or_404, redirect, render # Common utility functions.
from django.urls import reverse_lazy # To look up URL paths by their given name.
from django.views.decorators.csrf import csrf_exempt # To bypass security checks for our internal API view.
from django.views.generic import (CreateView, DeleteView, TemplateView,
                                  UpdateView) # Django's built-in "factories" for common tasks.

# --- Local Application Imports ---
# Imports from other files within this 'portal' app. The '.' means 'from the same directory'.
from .forms import CandidateForm, JobPostingForm
from .models import Candidate, Employee, JobPosting


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
