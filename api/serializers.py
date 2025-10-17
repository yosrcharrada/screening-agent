from rest_framework import serializers
from .models import InterviewSession, SkillMatchResult, QuestionSet, Transcript, ScoreResult

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