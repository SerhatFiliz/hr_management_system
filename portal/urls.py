from django.urls import path
# Import all the views we have created
from .views import (
    DashboardView,
    JobPostingCreateView,
    JobPostingUpdateView,
    JobPostingDeleteView,
    CandidateCreateView,
    CandidateUpdateView,
    JobPostingDetailView,
    ApplicationCreateView,
    ApplicationUpdateView,
    generate_job_title_view,
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
]
