from django.db import models


class InterviewSession(models.Model):
    cv_text = models.TextField()
    jd_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Session {self.id}"

class SkillMatchResult(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE)
    matched_skills = models.JSONField(default=list)  # Stores list of skills
    missing_skills = models.JSONField(default=list)  # Stores list of skills

    evidence = models.JSONField(default=list)

class QuestionSet(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE)
    questions = models.JSONField(default=list)  # Stores list of questions with rationale

class Transcript(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE)
    text = models.TextField()
    filler_words = models.IntegerField(default=0)
    wpm = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

class ScoreResult(models.Model):
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE)
    content_score = models.FloatField()
    delivery_score = models.FloatField()
    communication_score = models.FloatField()
    overall_score = models.FloatField()
    feature_contributions = models.JSONField(default=dict)  # For XAI
    evidence_quotes = models.JSONField(default=list)  # For XAI
    created_at = models.DateTimeField(auto_now_add=True)
