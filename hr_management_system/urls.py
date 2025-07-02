from django.contrib import admin
from django.urls import path, include
from django.conf import settings # To access the settings in the settings.py file
from django.conf.urls.static import static # to serve static and media files
from django.views.generic.base import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/accounts/register/', permanent=False), name='index'),
    
    path('admin/', admin.site.urls),

    path('accounts/', include('accounts.urls')),

    path('portal/', include('portal.urls')),
]

# We add this setting to serve media files only in DEBUG mode (development environment). 
# In a production environment these files are usually served by a web server such as Nginx/Apache.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)