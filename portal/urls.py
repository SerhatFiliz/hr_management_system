from django.urls import path
from . import views

# Import all the views we have created
from .views import (
    DashboardView,
    JobPostingCreateView,
    JobPostingUpdateView,
    JobPostingDeleteView,
    CandidateCreateView,
    CandidateUpdateView,
    CandidateDeleteView,
    JobPostingDetailView,
    ApplicationCreateView,
    ApplicationUpdateView,
    generate_job_title_view,
    BulkCVUploadView
)

urlpatterns = [
    # Path for the main user dashboard.
    path('dashboard/', DashboardView.as_view(), name='dashboard'),

    # Path for creating a new job posting.
    path('jobs/new/', JobPostingCreateView.as_view(), name='job-create'),

    # Path for updating an existing job posting.
    # <int:pk> is a path converter that captures an integer from the URL.
    # Django passes this integer as a keyword argument named 'pk' (primary key)
    # to the view, so the view knows which specific object to update.
    # Example URL: /portal/jobs/5/edit/
    path('jobs/<int:pk>/edit/', JobPostingUpdateView.as_view(), name='job-update'),

    # Path for deleting an existing job posting.
    # It works the same way as the update URL, using the 'pk' to identify the object.
    # Example URL: /portal/jobs/5/delete/
    path('jobs/<int:pk>/delete/', JobPostingDeleteView.as_view(), name='job-delete'),

    # Path for creating a new candidate.
    # The URL will be /portal/candidates/new/
    path('candidates/new/', CandidateCreateView.as_view(), name='candidate-create'),

    # Path for updating an existing candidate profile.
    # Example URL: /portal/candidates/3/edit/
    path('candidates/<int:pk>/edit/', CandidateUpdateView.as_view(), name='candidate-update'),

    # Path for deleting an existing candidate profile.
    # Example URL: /portal/candidates/4/delete/
    path('candidates/<int:pk>/delete/', CandidateDeleteView.as_view(), name='candidate-delete'),

    # Path for viewing a single job posting's details.
    # <int:pk> captures the job's ID from the URL and passes it to the view.
    # Example URL: /portal/jobs/7/
    path('jobs/<int:pk>/', JobPostingDetailView.as_view(), name='job-detail'),

    # Path for adding a candidate to a specific job posting.
    # The URL needs the job posting's pk to know which job the application is for.
    # Example URL: /portal/jobs/7/apply/
    path('jobs/<int:pk>/apply/', ApplicationCreateView.as_view(), name='application-create'),

    # Path for updating the status of a specific application.
    # The URL needs the application's pk to identify which one to update.
    # Example URL: /portal/application/12/update/
    path('application/<int:pk>/update/', ApplicationUpdateView.as_view(), name='application-update'),

    # Path for generating a job title using an external API.
    # This URL will be used to send a request to the API to generate a job title.
    path('api/generate-title/', generate_job_title_view, name='api-generate-title'),

    # This line creates a new URL endpoint for our bulk upload feature.
    # 'candidates/bulk-upload/' is the URL path.
    # 'views.BulkCVUploadView.as_view()' tells Django to use the class-based view we are about to create.
    # 'name='candidate-bulk-upload'' gives this URL a unique name so we can refer to it in our templates.
    path('candidates/bulk-upload/', BulkCVUploadView.as_view(), name='candidate-bulk-upload'),

     # --- NEW API URLs ---
    # This endpoint will receive a single CV file, parse it using our task's logic,
    # and return the extracted data as JSON.
    path('api/parse-cv/', views.parse_cv_api_view, name='api-parse-cv'),
    
    # This endpoint will receive a list of user-approved/edited candidate data
    # and save them to the database in bulk.
    path('api/save-candidates/', views.save_candidates_api_view, name='api-save-candidates'),

    # This path is for our new autofill feature.
    path('api/parse-cv-autofill/', views.parse_cv_for_autofill_api, name='api-parse-cv-autofill'),
]
