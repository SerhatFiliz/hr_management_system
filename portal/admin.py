from django.contrib import admin
# JobPosting, Candidate, Application modellerin varsa onları da buraya ekle
from .models import Employee, JobPosting, Candidate, Application

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'created_at')
    search_fields = ('user__username', 'company__name')
    list_filter = ('company', 'created_at')

@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'is_active', 'created_by')
    list_filter = ('is_active', 'company')
    search_fields = ('title',)

@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'company')
    list_filter = ('company',)
    search_fields = ('first_name', 'last_name', 'email')

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job_posting', 'status', 'application_date')
    list_filter = ('status', 'job_posting__company')