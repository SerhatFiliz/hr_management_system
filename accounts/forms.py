# accounts/forms.py

# Import necessary modules from Django and our project.
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
# We import the correct models from the 'portal' app as you defined them.
from portal.models import Company, Employee
from django.db import transaction

class UserRegistrationForm(UserCreationForm):
    """
    A custom form for new user registration.
    This form is designed to work with the provided Company and Employee models.
    """
    # We override the password fields directly in the class definition.
    # This is the standard and most robust way to customize parent form fields
    # and it completely avoids the 'KeyError' during form initialization.
    password = forms.CharField(
        label='Password', 
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Password confirmation', 
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    # We define the extra 'company_name' field that is not part of the default User model.
    company_name = forms.CharField(
        label='Company Name', 
        max_length=100,
        help_text='If your company is not in our system, a new one will be created.',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta(UserCreationForm.Meta):
        """
        The Meta class provides configuration for the form.
        """
        model = User
        # The fields from the User model we want to handle.
        fields = ('username',)
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    # The clean method remains unchanged.
    def clean_company_name(self):
        company_name = self.cleaned_data.get('company_name')
        if not company_name:
            raise forms.ValidationError("Company name is required.")
        return company_name

    @transaction.atomic # This ensures all database operations below are a single, safe transaction.
    def save(self, commit=True):
        """
        We override the save method to correctly handle the creation of the
        User, Company, and the crucial Employee profile that links them,
        exactly as defined in your models.
        """
        # 1. Create the User object in memory (but don't save to DB yet).
        user = super().save(commit=False)
        
        # 2. Get the company name from the form's cleaned data.
        company_name = self.cleaned_data['company_name']
        
        # 3. Find the company by name or create a new one if it doesn't exist.
        company, created = Company.objects.get_or_create(name=company_name)
        
        # 4. If commit is True, we save everything to the database.
        if commit:
            # First, save the User object to get a primary key.
            user.save()
            
            # --- THIS IS THE KEY STEP ---
            # Now, create the mandatory Employee profile.
            # This links the 'user' we just created to the 'company' we found/created.
            # This step ensures that any user registered through this form will have an
            # associated Employee profile, preventing the 'User has no employee' error.
            Employee.objects.create(user=user, company=company)
            
        # 5. Finally, return the created user object.
        return user

    
#------------------------------------------------------------------------------------------------------------------------
"""
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.core.exceptions import ValidationError

from django.contrib.auth.models import User
from .models import Company
from portal.models import Employee

class UserRegistrationForm(UserCreationForm):
    company_name = forms.CharField(
        max_length=255,
        required=True,
        label="Company Name",
        help_text="Name of the company you belong to. If it doesn't exist, it will be created and linked; otherwise, you will be linked to the existing one."
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('company_name',)

    def clean_company_name(self):
        
            # Custom validation method for the company_name field. runs after is_valid()
            # This method clears the company name and returns the Company object if the company already exists; otherwise, it returns None.
            # The clean_field_name() methods are where you validate and process the raw data entered into a single field in the form and return the result.
            # All the validated and processed values ​​from these methods are eventually collected in a safe dictionary called self.cleaned_data["field_name"].
        
        company_name = self.cleaned_data['company_name']  # cleanED_data its return value of clean_company_name()
        
        # Case insensitive search
        existing_company = Company.objects.filter(name__iexact=company_name).first()

        if existing_company:
            # If the company already exists, that Company object is returned
            # so the save method can use it.
            return existing_company
        else:
            # If the company does not exist, the sanitized name is returned.
            # The save method creates a new company.
            return company_name

    @transaction.atomic              # commit=True ---> create and save /// commit=False ---> create
    def save(self, commit=True):     # if is_valid() true 
        
            #Saves the User, Company (new or existing), and Employee objects.
        
        user = super().save(commit=False) # Creates the User object but does not save it yet. save user infos
                                          # The super() function allows us to access the methods of the superclass (UserCreationForm) from which we inherit.          
        company_data = self.cleaned_data['company_name']
        
        # Look at the value coming from the clean_company_name method
        # If the Company object came, it is an existing company.
        if isinstance(company_data, Company):    # is company_data is Company object or not.
            company = company_data # Mevcut Company objesini kullanıyoruz
        else:
            # If a string comes up, it is a new company and must be created.
            company = Company.objects.create(name=company_data)

        # Creates the Employee object and connects it to the User (existing or new) and Company.
        employee = Employee(user=user, company=company)

        if commit:
            user.save() # Saves the user object to the database
            employee.save() # Saves the employee object to the database
        return user
"""

