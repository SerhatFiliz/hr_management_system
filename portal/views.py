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

from django.db.models import Q  # The 'Q' object is used to build complex queries with OR conditions.
                                # .filter(Q(condition1) | Q(condition2)) means "where condition1 OR condition2".

# TrigramSimilarity: This function calculates the similarity score (from 0.0 to 1.0) between two strings based on their shared trigrams.                   
from django.contrib.postgres.search import TrigramSimilarity  

# Greatest: This function is used to find the highest value among multiple fields, which we will use to find the best similarity match.           
from django.db.models.functions import Greatest

from kafka import KafkaProducer  # The new library to interact with Kafka.

import redis # Import redis to check for task results

import uuid  # Import the UUID library to generate unique task IDs.

# The view is now a Class-Based View (CBV) for better organization and extensibility.
# It inherits from LoginRequiredMixin to ensure only authenticated users can access it.
class DashboardView(LoginRequiredMixin, View):
    """
    This Class-Based View handles both displaying the dashboard and processing
    the candidate filter form submissions via GET requests, including vector-based search.
    """
    def get(self, request, *args, **kwargs):
        """
        The 'get' method is called whenever a user navigates to this page with a GET request.
        """
        # --- Initial Setup ---
        # Step 1: Get the company associated with the currently logged-in user.
        company = request.user.employee.company

        # Step 2: Get the base querysets for all jobs and candidates for this company.
        job_postings = JobPosting.objects.filter(company=company)
        # This is our starting point for candidates, which we will narrow down with filters.
        candidate_queryset = Candidate.objects.filter(company=company)


        # --- Step 3: Get Filter Parameters from the URL ---
        # We use request.GET.get() to safely retrieve values from the URL's query string.
        # If a parameter doesn't exist, it will default to an empty string.
        name_email_query = request.GET.get('name_email', '')
        added_by_query = request.GET.get('added_by', '')
        start_date_query = request.GET.get('start_date', '')
        end_date_query = request.GET.get('end_date', '')


        # --- Step 4: Apply Filters to the Candidate Queryset ---
        # We check each parameter and, if it has a value, we chain a .filter() method
        # to our initial candidate_queryset. This dynamically builds our database query.

        # MODIFIED: Filter by Name or Email using Trigram Similarity
        if name_email_query:
            # Step 4a: Annotate the queryset with similarity scores.
            # .annotate() adds a new temporary field to each object in the queryset.
            candidate_queryset = candidate_queryset.annotate(
                first_name_similarity=TrigramSimilarity('first_name', name_email_query),
                last_name_similarity=TrigramSimilarity('last_name', name_email_query),
                email_similarity=TrigramSimilarity('email', name_email_query),
            )
            # Step 4b: Find the best match among the calculated similarities.
            candidate_queryset = candidate_queryset.annotate(
                best_similarity=Greatest(
                    'first_name_similarity', 
                    'last_name_similarity', 
                    'email_similarity'
                )
            )
            # Step 4c: Filter out results that are not similar enough.
            similarity_threshold = 0.1
            candidate_queryset = candidate_queryset.filter(best_similarity__gt=similarity_threshold)
            # Step 4d: Order the results by the best similarity score, descending.
            candidate_queryset = candidate_queryset.order_by('-best_similarity')

        # --- Other filters remain the same ---
        if added_by_query:
            candidate_queryset = candidate_queryset.filter(created_by__id=added_by_query)
        if start_date_query:
            candidate_queryset = candidate_queryset.filter(created_at__gte=start_date_query)
        if end_date_query:
            candidate_queryset = candidate_queryset.filter(created_at__lte=end_date_query)


        # --- Step 5: Prepare Additional Data for the Template Context ---
        company_employees = Employee.objects.filter(company=company).distinct()

        # The 'context' is a Python dictionary that acts as a bridge between your backend (this view)
        # and your frontend (the HTML template). Every key in this dictionary becomes a variable
        # that you can access in your template using {{ variable_name }}.
        #
        context = {
            # 'company': This key makes the company object available in the template,
            #            so we can display its name with {{ company.name }}.
            'company': company,
            
            # 'job_postings': Passes the queryset of all job postings for this company.
            #                 In the template, we can loop through this with {% for job in job_postings %}.
            'job_postings': job_postings,
            
            # 'candidates': This is the most important data for our table. It contains the final,
            #               potentially filtered and sorted, list of candidates to display.
            'candidates': candidate_queryset,
            
            # 'company_employees': We pass this list of employees so we can dynamically populate the
            #                      "Added By" dropdown menu in our filter form.
            'company_employees': company_employees,
            
            # 'filter_values': This nested dictionary is a user-experience improvement. It sends the user's
            #                  current filter selections back to the template. The template then uses these
            #                  values to pre-fill the form fields, making the form "remember" the selections.
            'filter_values': {
                'name_email': name_email_query,
                'added_by': added_by_query,
                'start_date': start_date_query,
                'end_date': end_date_query,
            }
        }
        
        # --- Step 6: Render the Template ---
        # Finally, we render the specified HTML template, passing the 'context' dictionary
        # to it so that all our data is available for display.
        return render(request, 'portal/dashboard.html', context)

#-----------------------------------------------------------------------------------------------------------
# class DashboardView(LoginRequiredMixin, TemplateView):
#     """
#     Displays the main dashboard, acting as the central hub for the user.
#     """
#     template_name = 'portal/dashboard.html'

#     def get_context_data(self, **kwargs):
#         """
#         CRITICAL METHOD: This method prepares and sends data from our Python
#         backend to the HTML template. It's how our template knows what to display.
#         """
#         context = super().get_context_data(**kwargs)
        
#         try:
#             employee = self.request.user.employee
#             context['company'] = employee.company
#             context['job_postings'] = JobPosting.objects.filter(company=employee.company)
#             context['candidates'] = Candidate.objects.filter(company=employee.company)
#         except Employee.DoesNotExist:
#             # Safely handle cases where a user (like a superuser) has no employee profile.
#             context['company'] = None
#             context['job_postings'] = []
#             context['candidates'] = []

#         context['user'] = self.request.user
#         return context

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


#-------------------------------------------------------------------------------------------

# ==============================================================================
# KAFKA & REDIS SETUP
# ==============================================================================
# Kafka Producer connection (remains the same)
kafka_producer = None
try:
    KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS')
    KAFKA_CV_TOPIC = os.getenv('KAFKA_CV_TOPIC')
    kafka_producer = KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS.split(','),
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )
    print("Kafka Producer connected successfully.")
except Exception as e:
    print(f"CRITICAL: Could not connect to Kafka Producer. Error: {e}")

# Redis client for checking task results (remains the same)
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'redis'), port=6379, db=1)


# ==============================================================================
# (UNCHANGED VIEWS: DashboardView, BulkCVUploadView, save_candidates_api_view, etc.)
# These views are included for completeness but were not modified in this step.
# ==============================================================================
class BulkCVUploadView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return render(request, 'portal/bulk_cv_upload.html')

@csrf_exempt
@login_required
def save_candidates_api_view(request):
    # ... (code for this view is unchanged) ...
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            candidates_to_save = data.get('candidates', [])
            for cand_data in candidates_to_save:
                email = cand_data.get('email')
                if email and not Candidate.objects.filter(email=email, company=request.user.employee.company).exists():
                    new_candidate = Candidate.objects.create(
                        company=request.user.employee.company,
                        first_name=cand_data.get('first_name', 'Unknown'),
                        last_name=cand_data.get('last_name', 'Unknown'),
                        email=email, created_by=request.user.employee
                    )
                    file_content_b64 = cand_data.get('file_content_b64')
                    original_filename = cand_data.get('original_filename', 'resume.pdf')
                    if file_content_b64:
                        file_content = base64.b64decode(file_content_b64)
                        new_candidate.resume.save(original_filename, ContentFile(file_content), save=True)
            return JsonResponse({
                'success': True, 'message': f'{len(candidates_to_save)} candidates were processed.',
                'redirect_url': reverse('dashboard')
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request method.'}, status=405)

@csrf_exempt
@login_required
def parse_cv_for_autofill_api(request):
    # ... (code for this synchronous view is unchanged) ...
    if request.method == 'POST' and request.FILES.get('cv_file'):
        cv_file = request.FILES['cv_file']
        file_content_b64 = base64.b64encode(cv_file.read()).decode('utf-8')
        try:
            # Note: We are now passing the task_id to the Celery task, even for this synchronous call.
            # While not strictly necessary for the auto-fill feature itself, it's good practice for consistency and debugging.
            task_id = str(uuid.uuid4())
            result_data = process_single_cv.delay(
                file_content_b64=file_content_b64,
                original_filename=cv_file.name,
                company_id=request.user.employee.company.id,
                created_by_id=request.user.id,
                create_candidate=False,
                task_id=task_id # Pass the new task_id
            ).get(timeout=30)
            if isinstance(result_data, dict) and 'error' not in result_data:
                return JsonResponse(result_data)
            else:
                error_message = result_data.get('error') if isinstance(result_data, dict) else str(result_data)
                return JsonResponse({'error': error_message}, status=400)
        except Exception as e:
            print(f"Error in synchronous auto-fill task: {e}")
            return JsonResponse({'error': 'The CV processing timed out or failed.'}, status=500)
    return JsonResponse({'error': 'Invalid request. A file must be provided.'}, status=400)


# ==============================================================================
# API VIEW: The CV Parser (For Bulk Upload) - MODIFIED FOR POLLING
# ==============================================================================
@csrf_exempt
@login_required
def parse_cv_api_view(request):
    """
    MODIFIED: This API endpoint now generates a unique task_id for each request.
    It includes this task_id in the message to Kafka and returns it to the frontend.
    The frontend will use this task_id to poll for the result.
    """
    if kafka_producer is None:
        return JsonResponse({'error': 'Kafka service is not available.'}, status=503)

    if request.method == 'POST' and request.FILES.get('cv_file'):
        cv_file = request.FILES['cv_file']
        file_content_b64 = base64.b64encode(cv_file.read()).decode('utf-8')

        # Step 1 (NEW): Generate a unique Task ID.
        # uuid.uuid4() creates a random, universally unique identifier.
        task_id = str(uuid.uuid4())

        # Step 2: Create the message payload, now including the task_id.
        message = {
            'task_id': task_id, # Add the task_id to the message
            'file_content_b64': file_content_b64,
            'original_filename': cv_file.name,
            'company_id': request.user.employee.company.id,
            'created_by_id': request.user.id,
        }

        try:
            # Step 3: Send the message to the Kafka topic.
            kafka_producer.send(KAFKA_CV_TOPIC, value=message)
            
            # Step 4 (MODIFIED): Return the task_id to the user.
            # The frontend JavaScript will receive this and know which task to check the status of.
            return JsonResponse({
                'task_id': task_id,
                'status': 'QUEUED',
                'original_filename': cv_file.name,
            })
        except Exception as e:
            print(f"Error sending message to Kafka: {e}")
            return JsonResponse({'error': 'Could not queue CV for processing.'}, status=500)
            
    return JsonResponse({'error': 'Invalid request.'}, status=400)


# ==============================================================================
# NEW API VIEW: Task Status Checker
# ==============================================================================
@login_required
def check_task_status_api(request, task_id):
    """
    This is a new, simple API endpoint that the frontend will poll.
    It takes a task_id and checks Redis to see if the result for that task is ready.
    """
    try:
        # Step 1: Check Redis for the given task_id.
        result_json = redis_client.get(task_id)

        if result_json:
            # Step 2a: If a result is found, it means the task is complete.
            # We parse the JSON string back into a Python dictionary.
            result_data = json.loads(result_json)
            # We can optionally remove the key from Redis now that it has been retrieved.
            # redis_client.delete(task_id)
            return JsonResponse({'status': 'COMPLETE', 'data': result_data})
        else:
            # Step 2b: If no result is found, the task is still pending.
            return JsonResponse({'status': 'PENDING'})

    except Exception as e:
        print(f"Error checking task status for {task_id}: {e}")
        return JsonResponse({'status': 'FAILURE', 'error': 'An error occurred while checking task status.'}, status=500)
