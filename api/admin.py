from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, InterviewSession, SkillMatchResult, QuestionSet, Transcript, ScoreResult

# Register CustomUser with custom admin
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'first_name', 'last_name', 'phone_number', 'registration_method', 'is_staff', 'is_active', 'created_at']
    list_filter = ['is_staff', 'is_active', 'registration_method', 'created_at']
    search_fields = ['email', 'first_name', 'last_name', 'phone_number']
    ordering = ['email']
    
    # Define fieldsets for the edit form
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone_number', 'cv_text', 'registration_method')
        }),
    )
    
    # Define fieldsets for the create form
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'cv_text', 'registration_method')
        }),
    )

# InterviewSession Admin - FIXED
@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_user_email', 'created_at', 'cv_preview', 'jd_preview']
    list_filter = ['created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'cv_text', 'jd_text']
    readonly_fields = ['created_at']
    list_select_related = ['user']
    
    def get_user_email(self, obj):
        return obj.user.email if obj.user else 'No User'
    get_user_email.short_description = 'User Email'
    get_user_email.admin_order_field = 'user__email'
    
    def cv_preview(self, obj):
        return obj.cv_text[:50] + '...' if len(obj.cv_text) > 50 else obj.cv_text
    cv_preview.short_description = 'CV Preview'
    
    def jd_preview(self, obj):
        return obj.jd_text[:50] + '...' if len(obj.jd_text) > 50 else obj.jd_text
    jd_preview.short_description = 'JD Preview'

# SkillMatchResult Admin
@admin.register(SkillMatchResult)
class SkillMatchResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_session_user', 'match_percentage', 'cv_skill_count', 'jd_skill_count', 'created_at']
    list_filter = ['created_at', 'match_percentage']
    search_fields = ['session__user__email', 'session__id']
    readonly_fields = ['created_at']
    list_select_related = ['session__user']
    
    def get_session_user(self, obj):
        return obj.session.user.email if obj.session and obj.session.user else 'No User'
    get_session_user.short_description = 'User'

# QuestionSet Admin
@admin.register(QuestionSet)
class QuestionSetAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_session_user', 'questions_count']
    search_fields = ['session__user__email', 'session__id']
    list_select_related = ['session__user']
    
    def get_session_user(self, obj):
        return obj.session.user.email if obj.session and obj.session.user else 'No User'
    get_session_user.short_description = 'User'
    
    def questions_count(self, obj):
        return len(obj.questions) if obj.questions else 0
    questions_count.short_description = 'Questions Count'

# Transcript Admin
@admin.register(Transcript)
class TranscriptAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_session_user', 'filler_words', 'wpm', 'text_preview', 'created_at']
    list_filter = ['created_at']
    search_fields = ['session__user__email', 'session__id', 'text']
    readonly_fields = ['created_at']
    list_select_related = ['session__user']
    
    def get_session_user(self, obj):
        return obj.session.user.email if obj.session and obj.session.user else 'No User'
    get_session_user.short_description = 'User'
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Text Preview'

# ScoreResult Admin
@admin.register(ScoreResult)
class ScoreResultAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_session_user', 'overall_score', 'content_score', 'delivery_score', 'communication_score', 'created_at']
    list_filter = ['created_at']
    search_fields = ['session__user__email', 'session__id']
    readonly_fields = ['created_at']
    list_select_related = ['session__user']
    
    def get_session_user(self, obj):
        return obj.session.user.email if obj.session and obj.session.user else 'No User'
    get_session_user.short_description = 'User'

# Optional: Customize admin site header and title
admin.site.site_header = 'Interview AI Administration'
admin.site.site_title = 'Interview AI Admin'
admin.site.index_title = 'Welcome to Interview AI Admin Portal'

# Optional: Add some admin actions
def delete_old_sessions(modeladmin, request, queryset):
    """Admin action to delete old sessions"""
    count = queryset.count()
    queryset.delete()
    modeladmin.message_user(request, f"Successfully deleted {count} sessions.")
delete_old_sessions.short_description = "Delete selected sessions"

# Add the action to InterviewSession admin
InterviewSessionAdmin.actions = [delete_old_sessions]