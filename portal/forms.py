from django import forms
from .models import JobPosting

class JobPostingForm(forms.ModelForm):
    """
    A form for creating and updating JobPosting instances.
    """
    class Meta:
        # Specifies the model this form is linked to.
        model = JobPosting

        # 'company' and 'created_by' will be set automatically in the view,
        fields = ['title', 'description', 'is_active']