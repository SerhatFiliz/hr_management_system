from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin

from .forms import JobPostingForm
from .models import JobPosting, Employee 

class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Displays the main dashboard for a logged-in user.
    It also lists all job postings associated with the user's company.
    """
    template_name = 'portal/dashboard.html'

    def get_context_data(self, **kwargs):
        """Adds user, company, and job postings to the template context."""
        context = super().get_context_data(**kwargs)
        
        # Get the current logged-in user's employee profile
        try:
            employee = self.request.user.employee
            context['company'] = employee.company
            # Filter job postings to show only those from the user's company
            context['job_postings'] = JobPosting.objects.filter(company=employee.company)
        except Employee.DoesNotExist:
            # Handle cases where a user might not have an associated employee profile
            context['company'] = None
            context['job_postings'] = []

        context['user'] = self.request.user
        return context

class JobPostingCreateView(LoginRequiredMixin, CreateView): #Thanks to CreateView, it is defined as a class, not a function.
    """
    Handles the creation of a new JobPosting.
    - Inherits from LoginRequiredMixin to ensure only logged-in users can access it.
    - Inherits from CreateView to get all the form handling logic for free.
    """
    # Specifies the model this view will work with.
    model = JobPosting
    
    # Specifies the form class to use for creating the model instance.
    form_class = JobPostingForm
    
    # Specifies the path to the HTML template that will render the form.
    template_name = 'portal/job_posting_editor.html'
    
    # Specifies the URL to redirect to after the form is successfully submitted.
    # 'reverse_lazy' is used to prevent circular import issues.
    success_url = reverse_lazy('dashboard')

    def form_valid(self, form):
        """
        This method is called when valid form data has been POSTed.
        It's overridden here to automatically set the 'company' and 'created_by'
        fields before saving the object to the database.
        """
        # Set the company of the job posting to the current user's company.
        form.instance.company = self.request.user.employee.company
        # Set the creator of the job posting to the current user's employee profile.
        form.instance.created_by = self.request.user.employee
        
        # Call the parent class's form_valid method to save the object
        # and perform the redirect.
        return super().form_valid(form)


"""@login_required
def job_posting_create_function(request):
    # 1. Adım: Eğer istek POST ise (form gönderilmişse)
    if request.method == 'POST':
        form = JobPostingForm(request.POST)
        # 2. Adım: Form geçerli mi diye kontrol et
        if form.is_valid():
            # 3. Adım: Kaydetmeden önce nesneyi al
            job_posting = form.save(commit=False)
            # 4. Adım: Eksik bilgileri manuel olarak ata
            job_posting.company = request.user.employee.company
            job_posting.created_by = request.user.employee
            # 5. Adım: Şimdi veritabanına kaydet
            job_posting.save()
            # 6. Adım: Kullanıcıyı dashboard'a yönlendir
            return redirect('dashboard')
    # 7. Adım: Eğer istek GET ise (sayfa ilk kez açılıyorsa)
    else:
        form = JobPostingForm()

    # 8. Adım: Formu (boş veya hatalı) şablona gönder
    return render(request, 'portal/job_posting_editor.html', {'form': form})
    """

class JobPostingUpdateView(LoginRequiredMixin, UpdateView):
    """
    Handles the updating of an existing JobPosting.
    """
    model = JobPosting
    form_class = JobPostingForm
    template_name = 'portal/job_posting_editor.html' # Aynı editör şablonunu kullanabiliriz
    success_url = reverse_lazy('dashboard')

    def get_queryset(self):
        """
        Ensures that users can only edit job postings belonging to their own company.
        This is a critical security measure.
        """
        # Start with all job postings
        queryset = super().get_queryset()
        # Filter them to return only the ones that belong to the current user's company
        return queryset.filter(company=self.request.user.employee.company)
    

class JobPostingDeleteView(LoginRequiredMixin, DeleteView):
    """
    Handles the deletion of a JobPosting.
    Shows a confirmation page before deleting.
    """
    model = JobPosting
    # Silme işlemi başarılı olunca kullanıcıyı dashboard'a yönlendir.
    success_url = reverse_lazy('dashboard')
    # Silme onayı için kullanılacak şablonun adı.
    template_name = 'portal/job_posting_confirm_delete.html'

    def get_queryset(self):
        """
        Ensures that users can only delete job postings belonging to their own company.
        """
        queryset = super().get_queryset()
        return queryset.filter(company=self.request.user.employee.company)