from django.urls import path
from . import views 

app_name = 'accounts' 

urlpatterns = [
    # Redirects the request to '/accounts/register/' to the views.register_hr_employee function.
    # This name is used to create URLs in HTML templates or Python code
    path('register/', views.register_hr_employee, name='register_hr_employee'),
]