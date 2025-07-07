from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
# Import the @login_required decorator for function-based views
#from django.contrib.auth.decorators import login_required

from .forms import JobPostingForm, CandidateForm
from .models import JobPosting, Employee, Candidate 

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
            context['candidates'] = [] # NEW

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
