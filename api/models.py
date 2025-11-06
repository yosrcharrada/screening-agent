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


class UserProfile(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255, blank=True)
    skills = models.JSONField(default=list)  # List of skills user has
    preferred_job_titles = models.JSONField(default=list)  # Job titles user is interested in
    preferred_locations = models.JSONField(default=list)  # Preferred job locations
    cv_text = models.TextField(blank=True)  # Store CV text for matching
    is_active = models.BooleanField(default=True)  # Enable/disable notifications
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.email} - {self.name}"


class JobOffer(models.Model):
    title = models.CharField(max_length=500)
    company = models.CharField(max_length=255, blank=True)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True)
    url = models.URLField(max_length=1000)
    source = models.CharField(max_length=100)  # e.g., 'adzuna', 'indeed', 'github'
    required_skills = models.JSONField(default=list)
    salary_range = models.CharField(max_length=255, blank=True)
    job_type = models.CharField(max_length=100, blank=True)  # e.g., 'full-time', 'part-time'
    posted_date = models.DateTimeField(null=True, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)
    external_id = models.CharField(max_length=255, unique=True)  # To avoid duplicates

    def __str__(self):
        return f"{self.title} at {self.company}"

    class Meta:
        ordering = ['-posted_date', '-fetched_at']


class JobNotification(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    job_offer = models.ForeignKey(JobOffer, on_delete=models.CASCADE)
    match_score = models.FloatField(default=0.0)  # How well the job matches user profile
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user_profile.email} - {self.job_offer.title}"

    class Meta:
        ordering = ['-sent_at']
        unique_together = ['user_profile', 'job_offer']  # Avoid duplicate notifications