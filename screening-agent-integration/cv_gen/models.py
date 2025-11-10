from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

class KnowledgeBase(models.Model):
    """Enhanced Knowledge Base with RAG classification"""
    
    PROFESSION_CHOICES = [
        ('Accountant', 'Accountant'),
        ('Backend Developer', 'Backend Developer'),
        ('Frontend Developer', 'Frontend Developer'),
        ('Manager', 'Manager'),
        ('DevOps Engineer', 'DevOps Engineer'),
        ('Data Scientist', 'Data Scientist'),
        ('QA Engineer', 'QA Engineer'),
        ('General', 'General'),
    ]
    
    CV_SECTION_CHOICES = [
        ('summary', 'Professional Summary'),
        ('achievement', 'Achievement/Accomplishment'),
        ('experience', 'Work Experience'),
        ('skill', 'Skill'),
    ]
    
    CONTENT_TYPE_CHOICES = [
        ('bullet', 'Bullet Point'),
        ('paragraph', 'Paragraph'),
        ('job_description', 'Job Description'),
    ]
    
    # Core content
    title = models.CharField(max_length=500, db_index=True)
    content = models.TextField()
    category = models.CharField(max_length=100, default='achievement')
    
    # RAG Classification
    profession = models.CharField(
        max_length=50,
        choices=PROFESSION_CHOICES,
        default='General',
        db_index=True
    )
    cv_section = models.CharField(
        max_length=50,
        choices=CV_SECTION_CHOICES,
        default='achievement',
        db_index=True
    )
    content_type = models.CharField(
        max_length=50,
        choices=CONTENT_TYPE_CHOICES,
        default='bullet'
    )
    
    # Metadata
    role_type = models.CharField(max_length=100, blank=True)
    industry = models.CharField(max_length=100, blank=True, db_index=True)
    source_document = models.CharField(max_length=500, blank=True)
    word_count = models.IntegerField(default=0)
    
    # Embeddings - JSON format for compatibility
    embedding_vector = models.TextField(
        blank=True,
        help_text="JSON array of embedding vector"
    )
    
    # Quality metrics
    confidence_score = models.FloatField(
        default=1.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)]
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Knowledge Base"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['profession', 'cv_section']),
            models.Index(fields=['cv_section', 'category']),
        ]
    
    def __str__(self):
        return f"{self.title[:50]} ({self.profession})"


class CVDocument(models.Model):
    """User's CV Document"""
    
    PROFESSION_CHOICES = [
        ('Accountant', 'Accountant'),
        ('Backend Developer', 'Backend Developer'),
        ('Frontend Developer', 'Frontend Developer'),
        ('Manager', 'Manager'),
        ('DevOps Engineer', 'DevOps Engineer'),
        ('Data Scientist', 'Data Scientist'),
        ('QA Engineer', 'QA Engineer'),
        ('Other', 'Other'),
    ]
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cv_documents'
    )
    
    # Personal Info
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=200, blank=True)
    
    # Professional Info
    professional_headline = models.CharField(max_length=200, blank=True)
    profession = models.CharField(max_length=100, choices=PROFESSION_CHOICES, default='Other')
    professional_summary = models.TextField(blank=True)
    
    # Generated Content
    generated_summary = models.TextField(blank=True, default='')
    generated_cv_content = models.JSONField(default=dict, blank=True)
    
    # ========== ADD THESE FIELDS ==========
    is_generated = models.BooleanField(default=False)
    # =====================================
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "CV Documents"
    
    def __str__(self):
        return f"{self.full_name} - {self.profession}"


class Skill(models.Model):
    """Skills for CV"""
    
    PROFICIENCY_CHOICES = [
        ('Beginner', 'Beginner'),
        ('Intermediate', 'Intermediate'),
        ('Advanced', 'Advanced'),
        ('Expert', 'Expert'),
    ]
    
    cv_document = models.ForeignKey(CVDocument, on_delete=models.CASCADE, related_name='skills')
    skill_name = models.CharField(max_length=200)
    proficiency_level = models.CharField(
        max_length=50,
        choices=PROFICIENCY_CHOICES,
        default='Intermediate'
    )
    category = models.CharField(max_length=100, blank=True)
    years_of_experience = models.FloatField(blank=True, null=True)
    generated_description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Skills"
        ordering = ['skill_name']
    
    def __str__(self):
        return f"{self.skill_name} ({self.proficiency_level})"


class WorkExperience(models.Model):
    """Work Experience for CV"""
    
    cv_document = models.ForeignKey(CVDocument, on_delete=models.CASCADE, related_name='work_experiences')
    job_title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(blank=True, null=True)
    is_current = models.BooleanField(default=False)
    
    job_description = models.TextField()
    achievements = models.TextField(blank=True)
    technologies = models.CharField(max_length=500, blank=True)
    
    generated_bullets = models.TextField(blank=True)
    generated_description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Work Experiences"
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.job_title} at {self.company_name}"


class Education(models.Model):
    """Education for CV"""
    
    cv_document = models.ForeignKey(CVDocument, on_delete=models.CASCADE, related_name='education')
    institution = models.CharField(max_length=300)
    field_of_study = models.CharField(max_length=200)
    degree = models.CharField(max_length=100, blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    gpa = models.FloatField(blank=True, null=True)
    honors = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    generated_description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Education"
        ordering = ['-end_date']
    
    def __str__(self):
        return f"{self.degree} in {self.field_of_study}"


class RAGCache(models.Model):
    """Cache for RAG query results"""
    
    query_hash = models.CharField(max_length=64, unique=True, db_index=True)
    query_text = models.TextField()
    profession = models.CharField(max_length=100, blank=True)
    cv_section = models.CharField(max_length=100, blank=True)
    cached_results = models.JSONField(default=dict)
    hit_count = models.IntegerField(default=0)
    
    accessed_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "RAG Cache"
        ordering = ['-accessed_at']
    
    def __str__(self):
        return f"Cache: {self.query_text[:50]}"


class CVGenerationFeedback(models.Model):
    """User feedback on generated CV content"""
    
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    
    cv_document = models.ForeignKey(CVDocument, on_delete=models.CASCADE, related_name='feedback')
    section_type = models.CharField(max_length=100)
    generated_content = models.TextField()
    rating = models.IntegerField(choices=RATING_CHOICES)
    feedback_text = models.TextField(blank=True)
    was_helpful = models.BooleanField(default=True)
    suggested_improvement = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "CV Generation Feedback"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feedback: {self.section_type} - Rating {self.rating}/5"