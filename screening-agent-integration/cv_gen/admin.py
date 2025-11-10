from django.contrib import admin
from .models import (
    CVDocument,
    WorkExperience,
    Education,
    Skill,
    KnowledgeBase
)

@admin.register(CVDocument)
class CVDocumentAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'professional_headline', 'profession', 'created_at')
    list_filter = ('profession', 'created_at')
    search_fields = ('full_name', 'email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(WorkExperience)
class WorkExperienceAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'company_name', 'start_date', 'is_current')
    list_filter = ('is_current', 'start_date')
    search_fields = ('job_title', 'company_name')

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('degree', 'institution', 'end_date')
    search_fields = ('degree', 'institution')

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('skill_name', 'cv_document', 'category', 'proficiency_level')
    list_filter = ('category', 'proficiency_level', 'cv_document')
    search_fields = ('skill_name',)

@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'profession', 'cv_section')
    list_filter = ('profession', 'cv_section', 'category')
    search_fields = ('title', 'content')