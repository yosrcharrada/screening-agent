"""
Admin configuration for jobs app.
"""
from django.contrib import admin
from .models import JobPosting, UserJobPreference, JobDispatchLog


@admin.register(JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'source', 'remote', 'location', 'published_at', 'created_at']
    list_filter = ['source', 'remote', 'created_at', 'published_at']
    search_fields = ['title', 'company', 'location', 'description']
    readonly_fields = ['hash', 'created_at', 'external_id']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Job Information', {
            'fields': ('title', 'company', 'location', 'remote', 'url', 'description')
        }),
        ('Source', {
            'fields': ('source', 'external_id', 'hash')
        }),
        ('Dates', {
            'fields': ('published_at', 'created_at')
        }),
        ('Raw Data', {
            'fields': ('raw_data',),
            'classes': ('collapse',)
        }),
    )


@admin.register(UserJobPreference)
class UserJobPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'remote_only', 'email_enabled', 'min_score_threshold', 'updated_at']
    list_filter = ['remote_only', 'email_enabled', 'updated_at']
    search_fields = ['user__username', 'user__email', 'keywords', 'desired_locations']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Search Criteria', {
            'fields': ('desired_locations', 'remote_only', 'keywords', 'min_score_threshold')
        }),
        ('Notification Settings', {
            'fields': ('email_enabled', 'max_jobs_per_email')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(JobDispatchLog)
class JobDispatchLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'job_title', 'job_company', 'score', 'sent_at']
    list_filter = ['sent_at']
    search_fields = ['user__username', 'user__email', 'job__title', 'job__company']
    readonly_fields = ['sent_at']
    date_hierarchy = 'sent_at'
    
    def job_title(self, obj):
        return obj.job.title
    job_title.short_description = 'Job Title'
    
    def job_company(self, obj):
        return obj.job.company
    job_company.short_description = 'Company'
    
    fieldsets = (
        ('Dispatch Info', {
            'fields': ('user', 'job', 'score', 'sent_at')
        }),
    )
