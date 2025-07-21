
from django import forms
from .models import JobPosting, Candidate, Application # Import all necessary models

# --- Job Posting Form ---
class JobPostingForm(forms.ModelForm):
    """
    A form for creating and updating JobPosting objects.
    We define widgets to apply Bootstrap classes automatically.
    """
    class Meta:
        model = JobPosting
        # We include all fields the user should be able to edit.
        fields = ['title', 'description', 'closing_date', 'is_active']
        
        # Widgets allow us to customize the HTML rendering of form fields.
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            # Using 'datetime-local' as the type creates a user-friendly date and time picker.
            'closing_date': forms.DateTimeInput(
                attrs={'type': 'datetime-local', 'class': 'form-control'}
            ),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

#------------------------------------------------------------------------------------------------------------------------

# --- Candidate Form ---
class CandidateForm(forms.ModelForm):
    """
    A form for creating and updating Candidate profiles.
    This form is now aligned with the updated Candidate model.
    """
    class Meta:
        model = Candidate
        # The fields list now correctly uses 'first_name' and 'last_name'.
        # The 'phone' field has been removed.
        fields = ['first_name', 'last_name', 'email', 'resume']
        
        # We define widgets for the correct field names.
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
        }

#------------------------------------------------------------------------------------------------------------------------

# --- Application Form ---
class ApplicationForm(forms.ModelForm):
    """
    A form to associate a Candidate with a JobPosting.
    This version is updated to handle the 'job_posting' kwarg from the view.
    """
    class Meta:
        model = Application
        fields = ['candidate']
        widgets = {
            'candidate': forms.Select(attrs={'class': 'form-select'}),
        }

    # --- YENİ EKLENEN METOT ---
    def __init__(self, *args, **kwargs):
        """
        We override the __init__ method to accept an extra 'job_posting' argument
        passed from the ApplicationCreateView.
        """
        # We "pop" (remove) the extra 'job_posting' argument from the kwargs.
        # We will use it, but the parent ModelForm's __init__ doesn't expect it.
        job_posting = kwargs.pop('job_posting', None)
        
        # Now, call the parent class's __init__ method with the cleaned kwargs.
        super().__init__(*args, **kwargs)
        
        # If we successfully received the job_posting object from the view...
        if job_posting:
            # ...we filter the 'candidate' field's queryset.
            # This is a great feature: it ensures that the dropdown menu for candidates
            # will only show candidates that belong to the SAME company as the job posting.
            # This prevents accidentally applying a candidate from Company A to a job in Company B.
            self.fields['candidate'].queryset = Candidate.objects.filter(company=job_posting.company)
#------------------------------------------------------------------------------------------------------------------------

# --- Application Status Form ---
class ApplicationStatusForm(forms.ModelForm):
    """
    A simple form to update the status of an application.
    """
    class Meta:
        model = Application
        # The user will only edit the 'status' field.
        fields = ['status']
        
        widgets = {
            # The status will be a dropdown menu styled with Bootstrap.
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

#------------------------------------------------------------------------------------------------------------------------

"""
from django import forms
from .models import JobPosting, Candidate, Application

class JobPostingForm(forms.ModelForm):
    
    # A form for creating and updating JobPosting instances.
    
    class Meta:
        # Specifies the model this form is linked to.
        model = JobPosting

        # 'company' and 'created_by' will be set automatically in the view,
        fields = ['title', 'description', 'requirements', 'closing_date', 'is_active']

        # Widgets allow us to customize the HTML rendering of form fields.
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            
            # We specify a widget for our new 'closing_date' field.
            # Using 'datetime-local' as the type creates a user-friendly
            # date and time picker in the browser.
            'closing_date': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                }
            ),
            
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CandidateForm(forms.ModelForm):
    
    #A form for creating a new Candidate instance.
    
    class Meta:
        # Specifies the model this form is linked to.
        model = Candidate
        
        # Defines the fields to be displayed in the form.
        # The 'resume' field corresponds to the FileField in our model.
        # 'company' and 'created_by' will be set automatically in the view.
        fields = ['first_name', 'last_name', 'email', 'resume']


class ApplicationForm(forms.ModelForm):
    
     # A form for creating a new Application, linking a Candidate to a JobPosting.
    
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
        
        # The form's __init__ method is overridden to dynamically filter the candidate dropdown list.
        
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
    
    #A simple form to update only the 'status' of an Application.
    
    class Meta:
        # This form is linked to the Application model.
        model = Application
        # It will only display and handle the 'status' field.
        fields = ['status']
        # We can apply Bootstrap classes to the generated field.
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
        }

"""

