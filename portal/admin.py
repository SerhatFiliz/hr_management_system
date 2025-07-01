from django.contrib import admin
from .models import Employee, JobPosting, Candidate, Application

# I save the Employee model to the Django Admin panel
@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'company__name') # Search in related model fields
    list_filter = ('company', 'created_at')

# I save the JobPosting model to the Django Admin panel
@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'is_active', 'created_by', 'created_at', 'updated_at')
    search_fields = ('title', 'description', 'company__name') # Search in related model fields
    list_filter = ('is_active', 'company', 'created_by', 'created_at')
    # Order and grouping of fields on the JobPosting detail page
    fieldsets = (
        (None, {
            'fields': ('company', 'title', 'description', 'is_active', 'auto_title_generated')
        }),
        ('Audit Info', {
            'fields': ('created_by',)
        }),
    )
    raw_id_fields = ('created_by',) # Provides a better widget for Foreign Keys

# I save the Candidate model to the Django Admin panel
@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'company', 'created_by', 'created_at')
    search_fields = ('first_name', 'last_name', 'email', 'company__name') # Search in related model fields
    list_filter = ('company', 'created_by', 'created_at')
    raw_id_fields = ('created_by',) # Provides a better widget for Foreign Keys

# I save the Application model to the Django Admin panel
@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job_posting', 'status', 'application_date')
    search_fields = ('candidate__first_name', 'candidate__last_name', 'job_posting__title')
    list_filter = ('status', 'job_posting__company', 'application_date')
    raw_id_fields = ('candidate', 'job_posting') # Provides a better widget for Foreign Keys