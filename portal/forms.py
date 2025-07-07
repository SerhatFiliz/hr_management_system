from django import forms
from .models import JobPosting, Candidate

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
