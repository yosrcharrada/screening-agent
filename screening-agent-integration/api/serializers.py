from rest_framework import serializers
from .models import InterviewSession, SkillMatchResult, QuestionSet, Transcript, ScoreResult, UserProfile, JobOffer, JobNotification

class InterviewSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = InterviewSession
        fields = '__all__'

class SkillMatchResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = SkillMatchResult
        fields = '__all__'

class QuestionSetSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionSet
        fields = '__all__'

class TranscriptSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transcript
        fields = '__all__'

class ScoreResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = ScoreResult
        fields = '__all__'


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class JobOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobOffer
        fields = '__all__'
        read_only_fields = ['fetched_at']


class JobNotificationSerializer(serializers.ModelSerializer):
    job_offer = JobOfferSerializer(read_only=True)
    
    class Meta:
        model = JobNotification
        fields = '__all__'
        read_only_fields = ['sent_at']