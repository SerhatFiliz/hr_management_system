from django.shortcuts import render, redirect # render: to display HTML template, redirect: to redirect the user
from django.contrib.auth import login # To automatically log in the user
from .forms import UserRegistrationForm # We import our own registration form
from django.contrib import messages # To show message to user

def register_hr_employee(request):
    """
    Shows the registration page and manages the registration process for HR Employees.
    This view handles both GET (displaying the form) and POST (processing form data) requests.
    """
    # If the user is already logged in, redirect them away from the registration page.
    if request.user.is_authenticated:
        return redirect('dashboard')

    # Check if the request method is POST, which means the form has been submitted.
    if request.method == 'POST':
        # Create a form instance and populate it with data from the request.
        form = UserRegistrationForm(request.POST)
        
        # Check if the form data is valid according to the rules defined in UserRegistrationForm.
        if form.is_valid():
            # If the form is valid, save the user object to the database.
            # Our custom form's save() method will also handle creating the company and profile.
            user = form.save() 
            
            # Log the user in automatically after successful registration.
            login(request, user)
            
            # Create a success message to be displayed on the next page.
            messages.success(request, 'Registration successful and you are now logged in!')
            
            # Redirect the user to the dashboard page.
            return redirect('dashboard')
        # else: (If form is not valid)
        # No explicit 'else' block is needed here. If form.is_valid() is false,
        # the function will naturally continue to the final render() call at the bottom,
        # passing the form object which now contains validation errors.
        # The template will then display these errors to the user.

    else: # If the request method is GET (i.e., the user is just visiting the page)
        # Create a blank, empty instance of the registration form.
        form = UserRegistrationForm()

    # Render the registration page template.
    # This line is reached on a GET request or when a POST request has an invalid form.
    # We pass the form object to the template in a context dictionary.
    return render(request, 'accounts/register.html', {'form': form})
