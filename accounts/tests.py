from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Company
from portal.models import Employee # The Employee model is in the 'portal' app.

class AccountsRegistrationTestCase(TestCase):
    """
    Test suite for the user registration functionality in the 'accounts' app.
    """
    def setUp(self):
        """
        This method runs before each test to set up a clean environment.
        It prepares a test client and necessary URL lookups.
        """
        self.client = Client()
        self.register_url = reverse('register')
        # As per project requirements, a successful registration should redirect to the dashboard.
        self.dashboard_url = reverse('dashboard')

    def test_successful_registration_with_new_company(self):
        """
        Tests if a user can register successfully with a brand new company name.
        It checks if a User, a Company, and an Employee profile are all created correctly.
        """
        # This data simulates a new user filling out the registration form.
        form_data = {
            'username': 'newuser',
            'company_name': 'New Unique Company',
            'password1': 'a-very-strong-password-123',
            'password2': 'a-very-strong-password-123'
        }

        # We get the state of the database *before* performing the action.
        initial_user_count = User.objects.count()
        initial_company_count = Company.objects.count()
        initial_employee_count = Employee.objects.count()

        # We simulate posting the form data to the registration URL.
        response = self.client.post(self.register_url, form_data)

        # --- Assertions ---

        # 1. Check that the registration was successful and resulted in a redirect.
        # If this fails, it likely means the form was invalid for some reason.
        form_errors = response.context.get('form').errors if response.context else {}
        self.assertEqual(response.status_code, 302, 
                         f"Should redirect after successful registration. "
                         f"Instead, got status 200 with form errors: {form_errors}")
        
        # 2. Check that the user is redirected to the correct page (the dashboard).
        self.assertRedirects(response, self.dashboard_url, msg_prefix="Should redirect to the dashboard.")

        # 3. Check that exactly one new object was created in each of the three tables.
        self.assertEqual(User.objects.count(), initial_user_count + 1, "A new User should be created.")
        self.assertEqual(Company.objects.count(), initial_company_count + 1, "A new Company should be created.")
        self.assertEqual(Employee.objects.count(), initial_employee_count + 1, "A new Employee profile should be created.")

        # 4. Retrieve the newly created objects to check their properties.
        new_user = User.objects.get(username='newuser')
        new_company = Company.objects.get(name='New Unique Company')
        new_employee = Employee.objects.get(user=new_user)

        # 5. Check that the new employee is correctly linked to the new user and new company.
        self.assertEqual(new_employee.company, new_company, "Employee should be linked to the new company.")

    def test_successful_registration_with_existing_company(self):
        """
        Tests if a user can register successfully by providing an existing company name.
        It should link the new user to the existing company, not create a new one.
        """
        # First, create an existing company in the database for the test scenario.
        existing_company = Company.objects.create(name="Existing Corp")

        # This data simulates a new user joining an already existing company.
        form_data = {
            'username': 'anotheruser',
            'company_name': 'Existing Corp', # Using the name of the existing company
            'password1': 'a-very-strong-password-123',
            'password2': 'a-very-strong-password-123'
        }

        # Get the company count *before* the action. It should not change.
        initial_company_count = Company.objects.count() # Should be 1

        # Simulate posting the form data.
        response = self.client.post(self.register_url, form_data)

        # --- Assertions ---

        # 1. Check for successful redirection.
        form_errors = response.context.get('form').errors if response.context else {}
        self.assertEqual(response.status_code, 302,
                         f"Should redirect. Instead, got 200 with form errors: {form_errors}")

        # 2. CRITICAL: Check that NO new company was created.
        self.assertEqual(Company.objects.count(), initial_company_count, "No new company should be created.")

        # 3. Check that the new user's employee profile is linked to the *existing* company.
        new_user = User.objects.get(username='anotheruser')
        new_employee = Employee.objects.get(user=new_user)
        self.assertEqual(new_employee.company, existing_company, "Employee should be linked to the existing company.")
