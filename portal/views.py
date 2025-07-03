from django.views.generic import TemplateView
"""
        - This is a shortcut for views that have a very simple job:
                render a specific template.
        - It saves us from writing a full function just to call the
                `render()` function. We simply tell it which template to use.
        - It handles all the background work of loading the template and
                returning an HTTP response.
"""
from django.contrib.auth.mixins import LoginRequiredMixin # This mixin ensures that only logged-in users can access the view.

class DashboardView(LoginRequiredMixin, TemplateView):
    """
    Displays the main dashboard for a logged-in user.
    Inherits from LoginRequiredMixin to protect the page.
    """
    # Specifies the template file to be rendered for this view.
    template_name = 'portal/dashboard.html'

    def get_context_data(self, **kwargs):
        """
        Sends additional context data to the template.
        Adds the current user and their company to the template context.
        """
        # Calls the base implementation first to get a context.
        context = super().get_context_data(**kwargs)
        # Adds the logged-in user object to the context.
        context['user'] = self.request.user
        # Adds the user's associated company to the context.
        # It assumes a 'userprofile' related object exists for the user.
        context['company'] = self.request.user.employee.company
        return context