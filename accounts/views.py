from django.shortcuts import render, redirect # render: to display HTML template, redirect: to redirect the user
from django.contrib.auth import login # To automatically log in the user
from .forms import UserRegistrationForm # We import our own registration form
from django.contrib import messages # To show message to user

def register_hr_employee(request):
    """
        HR Employee shows the registration page and manages the registration process.
    """
    if request.method == 'POST': # (1) If the HTTP request is POST (i.e. the form is submitted)
        form = UserRegistrationForm(request.POST) # (2) The form is filled with data submitted by the user (request.POST)
        if form.is_valid(): # (3) Check whether the form is valid or not.
            user = form.save() # (4) By calling the form's save method, the User, Company and Employee objects are saved.
                               # The save method returns the saved User object.

            login(request, user) # (5) After registration, the user is automatically logged in.

            messages.success(request, 'Registration successful and you are now logged in!') # Added success message

            # (6) After successful registration, the user is directed to the dashboard page.
            # Since there is no dashboard page yet, it is directed to the admin panel for now.
            # This will be changed when the dashboard URL is created in the future
            return redirect('dashboard') # Redirect to admin panel home page

        else:
            # (7) If the form is not valid (if there is a validation error)
            # We resend the form with errors (with form.errors) to the template.
            # The errors object is automatically found in the form.
            # Thus, the user sees the error messages next to the form.
            pass # The render function will already submit the form containing errors.

    else: # (8) If the HTTP request is GET (i.e. the user is viewing the page for the first time)
        form = UserRegistrationForm() # (9) We create a blank, clean registration form.

    # (10) Render (create) the HTML template and the form is sent to the template.
    # 'accounts/register.html': Path to the template to use.
    # {'form': form}: Python object (form object) sent to the template with the name 'form'.
    return render(request, 'accounts/register.html', {'form': form})