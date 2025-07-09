from django import forms
from .models import JobPosting, Candidate, Application

class JobPostingForm(forms.ModelForm):
    """
    A form for creating and updating JobPosting instances.
    """
    class Meta:
        # Specifies the model this form is linked to.
        model = JobPosting

        # 'company' and 'created_by' will be set automatically in the view,
        fields = ['title', 'description', 'is_active']


class CandidateForm(forms.ModelForm):
    """
    A form for creating a new Candidate instance.
    """
    class Meta:
        # Specifies the model this form is linked to.
        model = Candidate
        
        # Defines the fields to be displayed in the form.
        # The 'resume' field corresponds to the FileField in our model.
        # 'company' and 'created_by' will be set automatically in the view.
        fields = ['first_name', 'last_name', 'email', 'resume']


class ApplicationForm(forms.ModelForm):
    """
    A form for creating a new Application, linking a Candidate to a JobPosting.
    """
    # We define the 'candidate' field manually to have more control over it.
    # This will be a dropdown list (a select input).
    candidate = forms.ModelChoiceField(
        queryset=Candidate.objects.none(), # Start with an empty queryset.
        widget=forms.Select(attrs={'class': 'form-select'}) # Apply a Bootstrap class.
    )

    class Meta:
        model = Application
        # The user only needs to select the candidate.
        # The job_posting will be set automatically in the view.
        fields = ['candidate']

    def __init__(self, *args, **kwargs):
        """
        The form's __init__ method is overridden to dynamically filter the
        candidate dropdown list.
        """
        # We expect a 'job_posting' object to be passed in when the form is created.
        job_posting = kwargs.pop('job_posting')
        super().__init__(*args, **kwargs)

        # Get the company from the job posting.
        company = job_posting.company

        # Find all candidates who have already applied for this specific job.
        existing_applicants_pks = Application.objects.filter(
            job_posting=job_posting
        ).values_list('candidate__pk', flat=True)

        # Now, set the queryset for the 'candidate' field:
        # 1. Get all candidates belonging to the correct company.
        # 2. Exclude the candidates who have already applied (their PKs are in our list).
        self.fields['candidate'].queryset = Candidate.objects.filter(
            company=company
        ).exclude(
            pk__in=existing_applicants_pks
        )


class ApplicationStatusForm(forms.ModelForm):
    """
    A simple form to update only the 'status' of an Application.
    """
    class Meta:
        # This form is linked to the Application model.
        model = Application
        # It will only display and handle the 'status' field.
        fields = ['status']
        # We can apply Bootstrap classes to the generated field.
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

