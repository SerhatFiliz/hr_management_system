from django.contrib import admin
from .models import Company

# I save the Company model in the Django Admin panel. This way, we can add, edit and delete Company data in the admin panel.
@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    # Specifies which fields will be shown in the list view in the admin panel.
    list_display = ('name', 'description', 'created_at', 'updated_at')
    # Specifies which fields can be searched in the admin panel.
    search_fields = ('name', 'description')
    # Specifies which fields can be filtered in the list view in the admin panel.
    list_filter = ('created_at',)

