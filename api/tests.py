from django.test import TestCase
from .models import UserProfile, JobOffer, JobNotification
from .job_matcher import job_matcher
from .job_scraper import job_scraper
from datetime import datetime


class UserProfileModelTest(TestCase):
    """Test cases for UserProfile model"""
    
    def setUp(self):
        self.user_profile = UserProfile.objects.create(
            email="test@example.com",
            name="Test User",
            skills=["python", "django", "javascript"],
            preferred_job_titles=["Software Engineer", "Python Developer"],
            preferred_locations=["Remote", "New York"],
            is_active=True
        )
    
    def test_user_profile_creation(self):
        """Test that user profile is created correctly"""
        self.assertEqual(self.user_profile.email, "test@example.com")
        self.assertEqual(self.user_profile.name, "Test User")
        self.assertEqual(len(self.user_profile.skills), 3)
        self.assertTrue(self.user_profile.is_active)
    
    def test_user_profile_str(self):
        """Test string representation"""
        expected = "test@example.com - Test User"
        self.assertEqual(str(self.user_profile), expected)


class JobOfferModelTest(TestCase):
    """Test cases for JobOffer model"""
    
    def setUp(self):
        self.job = JobOffer.objects.create(
            title="Python Developer",
            company="Tech Corp",
            description="Looking for a Python developer with Django experience",
            location="Remote",
            url="https://example.com/job/123",
            source="remotive",
            required_skills=["python", "django", "rest api"],
            job_type="full-time",
            external_id="test_job_123"
        )
    
    def test_job_creation(self):
        """Test that job offer is created correctly"""
        self.assertEqual(self.job.title, "Python Developer")
        self.assertEqual(self.job.company, "Tech Corp")
        self.assertEqual(len(self.job.required_skills), 3)
    
    def test_job_str(self):
        """Test string representation"""
        expected = "Python Developer at Tech Corp"
        self.assertEqual(str(self.job), expected)
    
    def test_external_id_unique(self):
        """Test that external_id must be unique"""
        from django.db import IntegrityError
        
        with self.assertRaises(IntegrityError):
            JobOffer.objects.create(
                title="Another Job",
                company="Another Corp",
                description="Another description",
                location="Remote",
                url="https://example.com/job/456",
                source="remotive",
                external_id="test_job_123"  # Same as above
            )


class JobMatchingServiceTest(TestCase):
    """Test cases for job matching functionality"""
    
    def setUp(self):
        self.user_profile = UserProfile.objects.create(
            email="developer@example.com",
            name="Jane Developer",
            skills=["python", "django", "javascript", "react"],
            preferred_job_titles=["Software Engineer", "Full Stack Developer"],
            preferred_locations=["Remote"],
            cv_text="Experienced software engineer with 5 years of Python and Django development"
        )
        
        self.job1 = JobOffer.objects.create(
            title="Senior Python Developer",
            company="Tech Company",
            description="We need a Python developer with Django experience",
            location="Remote",
            url="https://example.com/job1",
            source="test",
            required_skills=["python", "django"],
            external_id="match_test_1"
        )
        
        self.job2 = JobOffer.objects.create(
            title="Java Backend Developer",
            company="Java Corp",
            description="Looking for Java Spring developers",
            location="New York",
            url="https://example.com/job2",
            source="test",
            required_skills=["java", "spring"],
            external_id="match_test_2"
        )
    
    def test_calculate_match_score(self):
        """Test that match score is calculated correctly"""
        score1 = job_matcher.calculate_match_score(self.user_profile, self.job1)
        score2 = job_matcher.calculate_match_score(self.user_profile, self.job2)
        
        # Job1 should have higher score as it matches user's skills
        self.assertGreater(score1, score2)
        self.assertGreater(score1, 0)
        self.assertLessEqual(score1, 100)
    
    def test_find_matching_jobs(self):
        """Test finding matching jobs"""
        all_jobs = [self.job1, self.job2]
        matches = job_matcher.find_matching_jobs(
            self.user_profile, 
            all_jobs, 
            min_score=30.0
        )
        
        # Should find at least the Python job
        self.assertGreater(len(matches), 0)
        # Results should be sorted by score
        if len(matches) > 1:
            self.assertGreaterEqual(matches[0][1], matches[1][1])


class JobScraperTest(TestCase):
    """Test cases for job scraper (basic structure tests, not actual API calls)"""
    
    def test_extract_skills(self):
        """Test skill extraction from job description"""
        description = "We need a developer with Python, Django, and React experience. Knowledge of Docker is a plus."
        skills = job_scraper._extract_skills(description)
        
        self.assertIn("python", skills)
        self.assertIn("django", skills)
        self.assertIn("react", skills)
        self.assertIn("docker", skills)
    
    def test_parse_date(self):
        """Test date parsing"""
        # ISO format
        date_str = "2024-01-15T10:30:00Z"
        parsed = job_scraper._parse_date(date_str)
        self.assertIsInstance(parsed, datetime)
        
        # None case
        parsed_none = job_scraper._parse_date(None)
        self.assertIsNone(parsed_none)


class JobNotificationModelTest(TestCase):
    """Test cases for JobNotification model"""
    
    def setUp(self):
        self.user = UserProfile.objects.create(
            email="notify@example.com",
            name="Notify User",
            skills=["python"],
            is_active=True
        )
        
        self.job = JobOffer.objects.create(
            title="Python Job",
            company="Company",
            description="Description",
            location="Remote",
            url="https://example.com/job",
            source="test",
            external_id="notify_test_1"
        )
    
    def test_notification_creation(self):
        """Test creating a notification"""
        notification = JobNotification.objects.create(
            user_profile=self.user,
            job_offer=self.job,
            match_score=85.5
        )
        
        self.assertEqual(notification.match_score, 85.5)
        self.assertFalse(notification.is_read)
        self.assertIsNotNone(notification.sent_at)
    
    def test_unique_together_constraint(self):
        """Test that same user-job combination can't be notified twice"""
        from django.db import IntegrityError
        
        JobNotification.objects.create(
            user_profile=self.user,
            job_offer=self.job,
            match_score=85.5
        )
        
        with self.assertRaises(IntegrityError):
            JobNotification.objects.create(
                user_profile=self.user,
                job_offer=self.job,
                match_score=90.0
            )
