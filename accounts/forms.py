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
        """
            Custom validation method for the company_name field. runs after is_valid()
            This method clears the company name and returns the Company object if the company already exists; otherwise, it returns None.
            The clean_field_name() methods are where you validate and process the raw data entered into a single field in the form and return the result.
            All the validated and processed values ​​from these methods are eventually collected in a safe dictionary called self.cleaned_data["field_name"].
        """
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
        """
            Saves the User, Company (new or existing), and Employee objects.
        """
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