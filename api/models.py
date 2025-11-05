from django.db import models

class InterviewSession(models.Model):
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
    questions = models.JSONField(default=list)

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