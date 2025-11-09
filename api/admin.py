from django.contrib import admin
from .models import (
    InterviewSession, SkillMatchResult, QuestionSet, Transcript, ScoreResult,
    UserProfile, JobOffer, JobNotification
)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['email', 'name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(JobOffer)
class JobOfferAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'location', 'source', 'posted_date', 'fetched_at']
    list_filter = ['source', 'job_type', 'fetched_at']
    search_fields = ['title', 'company', 'location']
    readonly_fields = ['fetched_at', 'external_id']


@admin.register(JobNotification)
class JobNotificationAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'job_offer', 'match_score', 'sent_at', 'is_read']
    list_filter = ['is_read', 'sent_at']
    search_fields = ['user_profile__email', 'job_offer__title']
    readonly_fields = ['sent_at']


# Register existing models if not already registered
admin.site.register(InterviewSession)
admin.site.register(SkillMatchResult)
admin.site.register(QuestionSet)
admin.site.register(Transcript)
admin.site.register(ScoreResult)
