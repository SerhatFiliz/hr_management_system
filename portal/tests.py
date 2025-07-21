from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
# We need SimpleUploadedFile to create a dummy file for testing uploads.
from django.core.files.uploadedfile import SimpleUploadedFile
# We need ContentFile to save file content directly to a model field in tests.
from django.core.files.base import ContentFile
from accounts.models import Company
from .models import Employee, JobPosting, Candidate, Application
from unittest.mock import patch, MagicMock # The library for "mocking" external services.
from .tasks import process_single_cv # We import our Celery task to test it directly.
import base64 # Needed to encode fake file content for the task.

# All test classes must inherit from django.test.TestCase.
# This provides a rich set of tools and sets up a clean test database for each run.
class PortalViewsTestCase(TestCase):
    """
    Test suite for the views in the 'portal' application.
    A test suite is a collection of tests that are run together.
    """
    
    # The setUp method is a special method that runs *before* every single test
    # function in this class. Its purpose is to create a clean and predictable
    # environment for each test to run in isolation.
    def setUp(self):
        """
        This method runs before each test function to set up a clean environment.
        """
        # self.client is an instance of Django's test Client. It acts like a "dummy"
        # web browser that we can use to make requests to our site's URLs.
        self.client = Client()
        
        # --- Create data for Company A ---
        # We create test objects in the database that our tests will interact with.
        self.company_a = Company.objects.create(name="Company A")
        self.user_a = User.objects.create_user(username='user_a', password='password123')
        self.employee_a = Employee.objects.create(user=self.user_a, company=self.company_a)
        
        # --- Create data for Company B ---
        # We create a second, separate company and user to test security rules.
        self.company_b = Company.objects.create(name="Company B")
        self.user_b = User.objects.create_user(username='user_b', password='password123')
        self.employee_b = Employee.objects.create(user=self.user_b, company=self.company_b)

        # --- Create a job posting that belongs to Company B ---
        # This object will be used to test if a user from Company A can access it.
        self.job_posting_b = JobPosting.objects.create(
            title="Developer at Company B",
            description="A job at Company B",
            company=self.company_b,
            created_by=self.employee_b
        )
        
        # --- Create dummy PDF file content ---
        # We define the binary content of a minimal, valid PDF file once to reuse it.
        self.dummy_pdf_content = b"%PDF-1.5\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n3 0 obj\n<< /Type /Page /MediaBox [0 0 612 792] >>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000010 00000 n \n0000000059 00000 n \n0000000112 00000 n \ntrailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n159\n%%EOF"
        
        # --- Create a dummy file object for upload simulations ---
        # SimpleUploadedFile simulates a file being uploaded through a form.
        self.dummy_resume_file = SimpleUploadedFile(
            "resume.pdf", 
            self.dummy_pdf_content, 
            "application/pdf"
        )
        
        # Define the URLs we will be testing. Using reverse() is best practice because
        # it finds the URL by its name from urls.py. If we change the URL path later,
        # our tests won't break.
        self.dashboard_url = reverse('dashboard')
        self.login_url = reverse('login')
        # This URL needs a keyword argument 'pk' to be built correctly.
        self.job_update_url_b = reverse('job-update', kwargs={'pk': self.job_posting_b.pk})

#-------------------------------------------------------------------------------------------------------------------------------

    # Test method names MUST start with 'test_'. Django's test runner
    # looks for methods with this prefix to know which ones to run.
    def test_dashboard_view_unauthenticated_user(self):
        """
        Test that an unauthenticated (not logged in) user is redirected
        from the dashboard to the login page.
        """
        # We use the test client to make a GET request to our dashboard URL.
        response = self.client.get(self.dashboard_url)
        
        # --- Assertions ---
        # Assertions are checks that must be true for the test to pass.
        
        # assertEqual(first, second, msg): Checks if the first and second values are equal.
        # Parameters:
        #   - response.status_code: The HTTP status code returned by the server.
        #   - 302: The expected status code for a redirect.
        #   - msg: The message to display if the assertion fails.
        self.assertEqual(response.status_code, 302, "Response should be a redirect.")
        
        # assertRedirects(response, expected_url, msg_prefix): A more powerful check.
        # It verifies both the status code (302) and the redirect location.
        # Parameters:
        #   - response: The response object from the client request.
        #   - expected_url: The full URL we expect the user to be redirected to.
        #   - msg_prefix: A prefix for the failure message.
        expected_redirect_url = f"{self.login_url}?next={self.dashboard_url}"
        self.assertRedirects(response, expected_redirect_url, msg_prefix="Should redirect to the login page.")

#-------------------------------------------------------------------------------------------------------------------------------

    def test_dashboard_view_authenticated_user(self):
        """
        Test that an authenticated (logged in) user can successfully
        access the dashboard page.
        """
        # The client.login() method simulates a user logging in.
        self.client.login(username='user_a', password='password123')
        
        # Now that we are logged in, we make the request again.
        response = self.client.get(self.dashboard_url)
        
        # --- Assertions ---
        # We expect a 200 OK status code, meaning the page was loaded successfully.
        self.assertEqual(response.status_code, 200, "Authenticated user should access the dashboard.")
        
        # assertTemplateUsed(response, template_name, msg_prefix): Checks if Django
        # used the specified template to render the response.
        # Parameters:
        #   - response: The response object.
        #   - 'portal/dashboard.html': The exact path of the template we expect to be used.
        self.assertTemplateUsed(response, 'portal/dashboard.html', "The correct template should be used.")
        
        # assertContains(response, text, msg_prefix): Checks if the given text
        # appears in the content of the response (the final rendered HTML).
        # Parameters:
        #   - response: The response object.
        #   - "Company A": The specific text we are looking for.
        self.assertContains(response, "Company A", msg_prefix="The company name should be displayed.")

#-------------------------------------------------------------------------------------------------------------------------------

    def test_user_cannot_edit_other_company_job_posting(self):
        """
        SECURITY TEST: Ensures a user from Company A cannot access the edit page
        for a job posting that belongs to Company B.
        """
        # Log in as the user from Company A.
        self.client.login(username='user_a', password='password123')
        
        # Attempt to access the edit URL for Company B's job posting.
        response = self.client.get(self.job_update_url_b)
        
        # --- Assertion ---
        # We expect a 404 Not Found error. This is because our 'get_queryset'
        # method filters the results, so from User A's perspective,
        # Company B's job posting "does not exist". This is the correct behavior.
        self.assertEqual(response.status_code, 404, "Should return 404 Not Found for unauthorized access.")

#-------------------------------------------------------------------------------------------------------------------------------

    def test_job_posting_creation(self):
        """
        Tests the successful creation of a new job posting via a POST request.
        """
        # Log in as a user.
        self.client.login(username='user_a', password='password123')
        
        # This is the data that simulates what a user would enter into the form.
        post_data = {
            'title': 'New Job at Company A',
            'description': 'A brand new role.',
            'is_active': True
        }
        
        # We check the state of the database *before* the action.
        initial_job_count = JobPosting.objects.count()
        
        # The client.post() method simulates submitting a form with the given data.
        response = self.client.post(reverse('job-create'), post_data)
        
        # --- Assertions ---
        self.assertEqual(response.status_code, 302, "Should redirect after successful creation.")
        self.assertRedirects(response, self.dashboard_url, msg_prefix="Should redirect to the dashboard.")
        
        # We check the state of the database *after* the action to see if it changed correctly.
        self.assertEqual(JobPosting.objects.count(), initial_job_count + 1, "A new job posting should be created.")
        
        # We retrieve the newly created object to check its properties.
        new_job = JobPosting.objects.latest('created_at')
        self.assertEqual(new_job.company, self.company_a, "The new job should belong to Company A.")
        self.assertEqual(new_job.created_by, self.employee_a, "The creator should be Employee A.")

#-------------------------------------------------------------------------------------------------------------------------------

    def test_candidate_creation(self):
        """
        Tests the successful creation of a new candidate, now including a file upload.
        """
        self.client.login(username='user_a', password='password123')
        
        # Add the dummy resume file object to our post data.
        post_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@example.com',
            'resume': self.dummy_resume_file
        }
        
        initial_candidate_count = Candidate.objects.count()
        # When posting files, the client needs to encode the data as 'multipart'.
        response = self.client.post(reverse('candidate-create'), post_data, format='multipart')
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, self.dashboard_url)
        self.assertEqual(Candidate.objects.count(), initial_candidate_count + 1)
        
        new_candidate = Candidate.objects.latest('created_at')
        self.assertEqual(new_candidate.company, self.company_a)
        
        # assertTrue(value, msg): Checks if the given value evaluates to True.
        # It's a more robust test for file existence than checking the exact filename.
        # Parameters:
        #   - new_candidate.resume.name: The path saved in the database for the file.
        self.assertTrue(new_candidate.resume.name, "A resume file path should be saved to the candidate.")

#-------------------------------------------------------------------------------------------------------------------------------

    def test_application_creation(self):
        """
        Tests that a user from Company B can successfully create an application
        for a job posting in their own company.
        """
        self.client.login(username='user_b', password='password123')
        
        # Create a candidate that also belongs to Company B.
        candidate_b = Candidate.objects.create(
            first_name="Jane", 
            last_name="Smith", 
            email="jane.smith@example.com",
            company=self.company_b,
            created_by=self.employee_b
        )
        
        # We must manually save the file content
        # to the field when creating an object directly in a test (not via a form).
        # ContentFile creates a file-like object from a string or bytes.
        candidate_b.resume.save("resume.pdf", ContentFile(self.dummy_pdf_content))
        
        post_data = {'candidate': candidate_b.pk}
        application_create_url = reverse('application-create', kwargs={'pk': self.job_posting_b.pk})
        
        initial_application_count = Application.objects.count()
        response = self.client.post(application_create_url, post_data)

        expected_redirect_url = reverse('job-detail', kwargs={'pk': self.job_posting_b.pk})

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, expected_redirect_url)
        self.assertEqual(Application.objects.count(), initial_application_count + 1)
        
        new_application = Application.objects.latest('application_date')
        self.assertEqual(new_application.candidate, candidate_b)
        self.assertEqual(new_application.job_posting, self.job_posting_b)

#-------------------------------------------------------------------------------------------------------------------------------

def test_candidate_creation_fails_with_invalid_file_type(self):
    """
    Tests that the form validation fails if a user tries to upload
    a non-PDF file for the resume, thanks to our FileExtensionValidator.
    """
    # Log in as a user to be able to access the form page.
    self.client.login(username='user_a', password='password123')

    # Create a dummy text file instead of a PDF to simulate an invalid upload.
    dummy_text_file = SimpleUploadedFile(
        "resume.txt",           # The filename.
        b"This is not a PDF.", # The file content as bytes.
        "text/plain"            # The content type.
    )

    # Prepare the form data with the invalid file.
    post_data = {
        'first_name': 'Invalid',
        'last_name': 'File',
        'email': 'invalid.file@example.com',
        'resume': dummy_text_file
    }

    # Check the number of candidates before the action.
    initial_candidate_count = Candidate.objects.count()
    # Simulate posting the form with the invalid file.
    response = self.client.post(reverse('candidate-create'), post_data, format='multipart')

    # --- Assertions ---

    # 1. Check that NO new candidate was created in the database.
    self.assertEqual(Candidate.objects.count(), initial_candidate_count, "No candidate should be created with an invalid file type.")

    # 2. Check that the server responded with 200 OK. This means it did NOT redirect.
    # Instead, it re-rendered the form page to show the validation error to the user.
    self.assertEqual(response.status_code, 200, "Should re-render the form page on validation error.")

    # 3. Check that the specific validation error message from our validator
    # is present in the HTML content of the response.
    self.assertContains(response, "Allowed extensions are: pdf", msg_prefix="The PDF validation error message should be displayed.")
    
#-----------------------------------------------------------------------------------------
# We use a TestCase to group related tests together.
class CVUploadTests(TestCase):

    def setUp(self):
        """
        This method runs before every single test in this class.
        It's used to set up a clean, predictable environment for each test.
        """
        # We create a test client to simulate browser requests.
        self.client = Client()
        
        # We create the necessary objects for our tests.
        self.company = Company.objects.create(name="Test Corp")
        self.user = User.objects.create_user(username='testuser', password='password123')
        # We must create an Employee profile for our test user.
        self.employee = Employee.objects.create(user=self.user, company=self.company)
        
        # We log in our test user.
        self.client.login(username='testuser', password='password123')

    # --- Test for the View ---
    
    @patch('portal.views.process_single_cv.delay') # We "mock" the Celery task's delay method.
    def test_bulk_cv_upload_post_triggers_task(self, mock_delay):
        """
        Tests if submitting the form with files correctly triggers the Celery task for each file.
        """
        print("Running test: test_bulk_cv_upload_post_triggers_task")
        url = reverse('candidate-bulk-upload')
        
        # We create two fake PDF files in memory to simulate a bulk upload.
        fake_cv1 = SimpleUploadedFile("test_cv1.pdf", b"file_content1", content_type="application/pdf")
        fake_cv2 = SimpleUploadedFile("test_cv2.pdf", b"file_content2", content_type="application/pdf")
        
        # We simulate a POST request, sending the fake files.
        self.client.post(url, {'cv_files': [fake_cv1, fake_cv2]})
        
        # This is the key assertion: We check that our mocked '.delay()' method was called twice,
        # once for each file. This proves our view is correctly handling multiple files.
        self.assertEqual(mock_delay.call_count, 2)

    # --- Tests for the Celery Task ---

    @patch('portal.tasks.genai.GenerativeModel') # We "mock" the entire Gemini Model class.
    def test_process_single_cv_creates_candidate_on_ai_success(self, MockGenerativeModel):
        """
        Tests if the Celery task correctly creates a Candidate when the AI provides a valid response.
        This tests our "Plan A".
        """
        print("Running test: test_process_single_cv_creates_candidate_on_ai_success")
        
        # --- Mocking the AI Response ---
        # We create a fake response that looks exactly like a real one from the Gemini API.
        mock_response = MagicMock()
        mock_response.text = '```json\n{"first_name": "Jane", "last_name": "AI", "email": "jane.ai@test.com"}\n```'
        
        # We tell our mocked model's 'generate_content' method to return our fake response.
        MockGenerativeModel.return_value.generate_content.return_value = mock_response
        
        fake_file_content_b64 = base64.b64encode(b"fake pdf content").decode('utf-8')

        # --- We now also mock the PDF reader ---
        # This prevents the "EOF marker not found" error by bypassing the actual PDF reading.
        with patch('portal.tasks.PyPDF2.PdfReader') as mock_pdf_reader:
            # We configure the mock to behave as if it read a PDF with some text.
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "This is some fake CV text."
            mock_pdf_reader.return_value.pages = [mock_page]

            # We run the Celery task directly as a normal function inside the patch context.
            process_single_cv(fake_file_content_b64, "fake_cv.pdf", self.company.id, self.user.id)
        
        # --- Assertions ---
        # We check if a new Candidate was actually created in the database with the AI's data.
        self.assertTrue(Candidate.objects.filter(email="jane.ai@test.com").exists())
        candidate = Candidate.objects.get(email="jane.ai@test.com")
        self.assertEqual(candidate.first_name, "Jane")
        self.assertEqual(candidate.last_name, "AI")

    @patch('portal.tasks.genai.GenerativeModel')
    def test_process_single_cv_uses_regex_on_ai_failure(self, MockGenerativeModel):
        """
        Tests if the Celery task falls back to RegEx and still creates a Candidate
        when the AI call fails. This tests our "Plan B".
        """
        print("Running test: test_process_single_cv_uses_regex_on_ai_failure")
        
        # --- Mocking an AI FAILURE ---
        # We configure the mocked 'generate_content' method to raise an exception,
        # simulating a network error or the API being down.
        MockGenerativeModel.return_value.generate_content.side_effect = Exception("Simulating API failure")

        # We create fake file content that contains information our RegEx can find.
        fake_pdf_text = "This is a test CV for John Regex. Contact him at john.regex@test.com."
        fake_file_content_b64 = base64.b64encode(fake_pdf_text.encode('utf-8')).decode('utf-8')
        
        # We need to also mock the PDF reader to return our fake text.
        with patch('portal.tasks.PyPDF2.PdfReader') as mock_pdf_reader:
            # Create a mock page object with an extract_text method.
            mock_page = MagicMock()
            mock_page.extract_text.return_value = fake_pdf_text
            # Make the mock reader return a list containing our mock page.
            mock_pdf_reader.return_value.pages = [mock_page]

            # Run the task. This will trigger the exception inside the 'try' block.
            process_single_cv(fake_file_content_b64, "fake_cv.pdf", self.company.id, self.user.id)
        
        # --- Assertions ---
        # We check that a Candidate was STILL created, this time with the data found by our RegEx fallback.
        self.assertTrue(Candidate.objects.filter(email="john.regex@test.com").exists())
        candidate = Candidate.objects.get(email="john.regex@test.com")
        self.assertEqual(candidate.first_name, "John")
        self.assertEqual(candidate.last_name, "Regex")
