from django.db import models
from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    cv_text = models.TextField(blank=True, null=True)
    registration_method = models.CharField(
        max_length=10, 
        choices=[('manual', 'Manual'), ('cv', 'CV Upload')],
        default='manual'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email
    
class InterviewSession(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, null=True)  # This line must exist
    cv_text = models.TextField()
    jd_text = models.TextField()
    created_at = models.DateTimeField(null=True, blank=True)  # Remove auto_now_add temporarily
    analysis_data = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"Session {self.id}"

class SkillMatchResult(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE)
    matched_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    evidence = models.JSONField(default=list)
    cv_skill_count = models.IntegerField(default=0)
    jd_skill_count = models.IntegerField(default=0)
    match_percentage = models.FloatField(default=0.0)
    created_at = models.DateTimeField(null=True, blank=True)  # Remove auto_now_add temporarily

    def __str__(self):
        return f"Skills for Session {self.session.id}"

class QuestionSet(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE)
    questions = models.JSONField()  # Stores the list of questions
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Add metadata field for XAI data
    metadata = models.JSONField(default=dict, blank=True, null=True)  # ADD THIS LINE
    
    def __str__(self):
        return f"QuestionSet for Session {self.session.id} - {self.created_at}"


class Transcript(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE)
    text = models.TextField()
    filler_words = models.IntegerField(default=0)
    wpm = models.FloatField(default=0.0)
    created_at = models.DateTimeField(null=True, blank=True)  # Remove auto_now_add temporarily

class ScoreResult(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE)
    content_score = models.FloatField()
    delivery_score = models.FloatField()
    communication_score = models.FloatField()
    overall_score = models.FloatField()
    feature_contributions = models.JSONField(default=dict)
    evidence_quotes = models.JSONField(default=list)
    created_at = models.DateTimeField(null=True, blank=True)  # Remove auto_now_add temporarily