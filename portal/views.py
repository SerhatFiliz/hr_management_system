from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
# Import the @login_required decorator for function-based views
#from django.contrib.auth.decorators import login_required

from .forms import JobPostingForm, CandidateForm
from .models import JobPosting, Employee, Candidate 

import json  # The standard Python library that allows reading and writing JSON data.
import requests  # A popular library that allows Python to send requests to external websites/APIs.
from django.http import JsonResponse  # A special tool in Django that returns a response in JSON format instead of an HTML page.
from django.views.decorators.csrf import csrf_exempt  # A "special permission card" that disables security checks for a specific view.
from django.conf import settings  # Allows access to variables (like an API key) defined in the project's settings.py file.
from django.contrib.auth.decorators import login_required  # A security guard that ensures only logged-in users can run a specific function.
class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Displays the main dashboard for a logged-in user.
    It also lists all job postings and candidates associated with the user's company.
    """
    template_name = 'portal/dashboard.html'

    def get_context_data(self, **kwargs):
        """Adds user, company, job postings, and candidates to the template context."""
        context = super().get_context_data(**kwargs)
        
        try:
            employee = self.request.user.employee
            context['company'] = employee.company
            # Filter job postings to show only those from the user's company
            context['job_postings'] = JobPosting.objects.filter(company=employee.company)
            # Filter candidates to show only those from the user's company
            context['candidates'] = Candidate.objects.filter(company=employee.company)
        except Employee.DoesNotExist:
            # Handle cases where a user might not have an associated employee profile
            context['company'] = None
            context['job_postings'] = []
            context['candidates'] = [] 

        context['user'] = self.request.user
        return context


"""
# --- Function-Based Equivalent for DashboardView ---
# The @login_required decorator is used instead of the LoginRequiredMixin in classes.
@login_required
def dashboard_function(request):
    # The same logic as in the get_context_data method is implemented here.
    context = {}
    try:
        employee = request.user.employee
        context['company'] = employee.company
        context['job_postings'] = JobPosting.objects.filter(company=employee.company)
    except Employee.DoesNotExist:
        context['company'] = None
        context['job_postings'] = []
    
    context['user'] = request.user
    
    # Finally, the template is rendered with the context.
    return render(request, 'portal/dashboard.html', context)
"""

# -------------------------------------------Job Posting Creation View --------------------------------
class JobPostingCreateView(LoginRequiredMixin, CreateView):
    """
    Handles the creation of a new JobPosting.
    """
    model = JobPosting
    form_class = JobPostingForm
    template_name = 'portal/job_posting_editor.html'
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        """
        It's overridden here to automatically set the 'company' and 'created_by'
        fields before saving the object to the database.
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

# -------------------------------------------Job Posting Update View --------------------------------
class JobPostingUpdateView(LoginRequiredMixin, UpdateView):
    """
    Handles the updating of an existing JobPosting.
    """
    model = JobPosting
    form_class = JobPostingForm
    template_name = 'portal/job_posting_editor.html'
    success_url = reverse_lazy('dashboard')

    def get_queryset(self):
        """
        Ensures that users can only edit job postings belonging to their own company.
        """
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.user.employee.company)

"""
# --- Function-Based Equivalent for JobPostingUpdateView ---
@login_required
def job_posting_update_function(request, pk):
    # The security logic from get_queryset is implemented here with get_object_or_404.
    # This line tries to find the posting, but ONLY if it belongs to the user's own company.
    # If it's not found or belongs to another company, it raises a 404 "Not Found" error.
    job_posting = get_object_or_404(JobPosting, pk=pk, company=request.user.employee.company)
    
    if request.method == 'POST':
        # The form is populated with both the submitted data and the existing instance.
        form = JobPostingForm(request.POST, instance=job_posting)
        if form.is_valid():
            form.save()
            return redirect('dashboard')
    else:
        # The form is populated only with the existing instance's data (on initial page load).
        form = JobPostingForm(instance=job_posting)
        
    return render(request, 'portal/job_posting_editor.html', {'form': form})
"""

# -------------------------------------------Job Posting Deletion View --------------------------------
class JobPostingDeleteView(LoginRequiredMixin, DeleteView):
    """
    Handles the deletion of a JobPosting.
    """
    model = JobPosting
    success_url = reverse_lazy('dashboard')
    template_name = 'portal/job_posting_confirm_delete.html'

    def get_queryset(self):
        """
        Ensures that users can only delete job postings belonging to their own company.
        """
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.user.employee.company)

"""
# --- Function-Based Equivalent for JobPostingDeleteView ---
@login_required
def job_posting_delete_function(request, pk):
    # Security is again handled with get_object_or_404.
    job_posting = get_object_or_404(JobPosting, pk=pk, company=request.user.employee.company)
    
    # The delete operation must only be done via a POST request.
    if request.method == 'POST':
        job_posting.delete()
        return redirect('dashboard')
        
    # On a GET request, the confirmation page is shown.
    # 'object' is the default context name used by DeleteView.
    return render(request, 'portal/job_posting_confirm_delete.html', {'object': job_posting})
"""
# -------------------------------------------Candidate Creation View --------------------------------
class CandidateCreateView(LoginRequiredMixin, CreateView):
    """
    Handles the creation of a new Candidate, including resume upload.
    """
    # Specifies the model this view will work with.
    model = Candidate
    
    # Specifies the form class to use.
    form_class = CandidateForm
    
    # Specifies the HTML template to render the form.
    template_name = 'portal/candidate_editor.html'
    
    # Redirects to the dashboard after successful creation.
    # We might change this later to a candidate list page.
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        """
        Overrides the default form_valid method to automatically set
        the 'company' and 'created_by' fields for the new candidate.
        """
        # Set the company of the candidate to the current user's company.
        form.instance.company = self.request.user.employee.company
        # Set the creator of the candidate to the current user's employee profile.
        form.instance.created_by = self.request.user.employee
        
        # Call the parent class's method to save the object and redirect.
        return super().form_valid(form)

@csrf_exempt
@login_required
def generate_job_title_view(request):
    """
    Receives a job description, sends it to the specified Hugging Face model,
    and returns a summarized title. This version has improved error handling.
    """
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            description = data.get('description', '')

            if not description:
                return JsonResponse({'error': 'Description cannot be empty.'}, status=400)

            # Payload for the summarization model (facebook/bart-large-cnn)
            api_payload = {
                "inputs": description,
                # Parameters to control the output length, as per project requirements.
                "parameters": {"max_length": 50, "min_length": 5}
            }
            
            headers = {"Authorization": f"Bearer {settings.HUGGING_FACE_API_KEY}"}

            # Send request with a 30-second timeout.
            response = requests.post(
                settings.HUGGING_FACE_API_URL, 
                headers=headers, 
                json=api_payload,
                timeout=30
            )

            # Handle non-200 responses gracefully
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    api_error_message = error_data.get('error', 'Unknown API error.')
                    # Check for the common "model is loading" error
                    if 'is currently loading' in api_error_message:
                        estimated_time = error_data.get('estimated_time', 20)
                        user_message = f"The AI model is currently warming up. Please try again in {estimated_time:.0f} seconds."
                        return JsonResponse({'error': user_message}, status=503) # Service Unavailable
                    return JsonResponse({'error': f"API Error: {api_error_message}"}, status=response.status_code)
                except json.JSONDecodeError:
                    return JsonResponse({'error': f"API returned a non-JSON response: {response.text}"}, status=response.status_code)

            result = response.json()
            
            # Safely parse the response for 'summary_text'
            generated_title = "New Job Posting" # Default title as per requirements.
            if result and isinstance(result, list) and len(result) > 0:
                title_from_api = result[0].get('summary_text')
                if title_from_api:
                    generated_title = title_from_api

            return JsonResponse({'title': generated_title.strip()})

        except requests.exceptions.Timeout:
            return JsonResponse({'error': 'The request to the AI model timed out. The model might be loading. Please try again.'}, status=504)
        except Exception as e:
            return JsonResponse({'error': f'An unexpected server error occurred: {str(e)}'}, status=500)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)