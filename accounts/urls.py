from django.urls import path
from .views import register_hr_employee
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', register_hr_employee, name='register'),

    # Defines the URL path for user login.
    # It uses Django's built-in LoginView to handle the authentication logic.
    # - 'template_name': Specifies the path to the custom HTML template for the login form.
    # - 'name': A unique name used to reference this URL path in templates or views.
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),

    # Defines the URL path for user logout.
    # It uses Django's built-in LogoutView to handle terminating the user's session.
    # - 'next_page': Specifies the name of the URL to redirect to after a successful logout.
    # - 'name': A unique name for this URL path.
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
]