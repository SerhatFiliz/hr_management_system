from django.urls import path
from .views import DashboardView # Import the DashboardView from views.py

urlpatterns = [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]