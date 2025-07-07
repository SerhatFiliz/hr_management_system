# portal/urls.py

from django.urls import path
# Import all the views we have created
from .views import (
    DashboardView,
    JobPostingCreateView,
    JobPostingUpdateView,
    JobPostingDeleteView,
    CandidateCreateView
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
]
