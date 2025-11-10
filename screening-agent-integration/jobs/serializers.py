"""
Serializers for jobs app.
"""
from rest_framework import serializers
from .models import UserJobPreference, JobPosting, JobDispatchLog


class UserJobPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserJobPreference
        fields = [
            'desired_locations',
            'remote_only',
            'keywords',
            'min_score_threshold',
            'email_enabled',
            'max_jobs_per_email',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class JobPostingSerializer(serializers.ModelSerializer):
    age_in_days = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = JobPosting
        fields = [
            'id',
            'source',
            'title',
            'company',
            'location',
            'remote',
            'url',
            'description',
            'published_at',
            'created_at',
            'age_in_days'
        ]
        read_only_fields = ['id', 'created_at']


class JobDispatchLogSerializer(serializers.ModelSerializer):
    job = JobPostingSerializer(read_only=True)
    
    class Meta:
        model = JobDispatchLog
        fields = ['id', 'job', 'score', 'sent_at']
        read_only_fields = ['id', 'sent_at']
