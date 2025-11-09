"""
Models for job matching and notifications.
"""
import hashlib
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone


User = get_user_model()


class JobPosting(models.Model):
    """Stores job postings fetched from various sources."""
    
    # Source and identification
    source = models.CharField(max_length=50, db_index=True)  # 'remotive', 'remoteok', etc.
    external_id = models.CharField(max_length=255)  # ID from the source API
    hash = models.CharField(max_length=64, unique=True, db_index=True)  # SHA-256 hash for deduplication
    
    # Job details
    title = models.CharField(max_length=500)
    company = models.CharField(max_length=255, blank=True)
    location = models.CharField(max_length=255, blank=True)
    remote = models.BooleanField(default=False)
    url = models.URLField(max_length=1000)
    description = models.TextField()
    
    # Additional metadata
    published_at = models.DateTimeField(null=True, blank=True)
    raw_data = models.JSONField(default=dict, blank=True)  # Store original API response
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        ordering = ['-published_at', '-created_at']
        unique_together = [['source', 'external_id']]
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['remote']),
        ]
    
    def __str__(self):
        return f"{self.title} at {self.company} ({self.source})"
    
    def save(self, *args, **kwargs):
        """Generate hash on save if not provided."""
        if not self.hash:
            self.hash = self.generate_hash()
        super().save(*args, **kwargs)
    
    def generate_hash(self):
        """Generate unique hash from source, external_id, and title."""
        content = f"{self.source}:{self.external_id}:{self.title}".encode('utf-8')
        return hashlib.sha256(content).hexdigest()
    
    @property
    def age_in_days(self):
        """Calculate age of the posting in days."""
        if self.published_at:
            delta = timezone.now() - self.published_at
            return delta.days
        return None


class UserJobPreference(models.Model):
    """Stores job preferences for each user."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='job_preference')
    
    # Search criteria
    desired_locations = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated locations, e.g., 'New York,Remote,San Francisco'"
    )
    remote_only = models.BooleanField(default=False)
    keywords = models.CharField(
        max_length=500,
        blank=True,
        help_text="Comma-separated keywords, e.g., 'python,django,react'"
    )
    
    # Matching threshold
    min_score_threshold = models.FloatField(
        default=0.6,
        help_text="Minimum matching score (0.0 - 1.0) to receive notifications"
    )
    
    # Notification settings
    email_enabled = models.BooleanField(default=True)
    max_jobs_per_email = models.IntegerField(default=10)
    
    # System fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Job Preference'
        verbose_name_plural = 'User Job Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
    
    def get_keywords_list(self):
        """Return keywords as a list."""
        if not self.keywords:
            return []
        return [k.strip().lower() for k in self.keywords.split(',') if k.strip()]
    
    def get_locations_list(self):
        """Return desired locations as a list."""
        if not self.desired_locations:
            return []
        return [loc.strip() for loc in self.desired_locations.split(',') if loc.strip()]


class JobDispatchLog(models.Model):
    """Tracks which jobs have been sent to which users."""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_dispatches')
    job = models.ForeignKey(JobPosting, on_delete=models.CASCADE, related_name='dispatches')
    score = models.FloatField(help_text="Matching score for this job-user pair")
    sent_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['user', 'job']]
        ordering = ['-sent_at']
        indexes = [
            models.Index(fields=['user', '-sent_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.job.title} ({self.score:.2f})"
