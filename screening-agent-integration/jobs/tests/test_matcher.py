"""
Tests for job matcher service.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from unittest.mock import patch, Mock
import numpy as np

from jobs.models import JobPosting, UserJobPreference, JobDispatchLog
from jobs.services.matcher import JobMatcher, match_and_notify

User = get_user_model()


class JobMatcherTest(TestCase):
    """Test job matching logic."""
    
    def setUp(self):
        """Set up test data."""
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create preference
        self.preference = UserJobPreference.objects.create(
            user=self.user,
            keywords='python,django',
            remote_only=False,
            min_score_threshold=0.5
        )
        
        # Create jobs
        self.job1 = JobPosting.objects.create(
            source='remotive',
            external_id='job1',
            title='Senior Python Developer',
            company='Tech Corp',
            location='Remote',
            remote=True,
            url='https://example.com/job1',
            description='Looking for an experienced Python and Django developer',
            published_at=timezone.now()
        )
        
        self.job2 = JobPosting.objects.create(
            source='remotive',
            external_id='job2',
            title='Java Backend Engineer',
            company='Java Inc',
            location='New York',
            remote=False,
            url='https://example.com/job2',
            description='Java Spring Boot developer needed',
            published_at=timezone.now()
        )
    
    def test_location_match_remote_only(self):
        """Test location matching with remote_only preference."""
        self.preference.remote_only = True
        self.preference.save()
        
        matcher = JobMatcher()
        
        # Remote job should match
        match1 = matcher._check_location_match(self.job1, self.preference)
        self.assertTrue(match1)
        
        # Non-remote job should not match
        match2 = matcher._check_location_match(self.job2, self.preference)
        self.assertFalse(match2)
    
    def test_keyword_boost_calculation(self):
        """Test keyword boost calculation."""
        matcher = JobMatcher()
        keywords = ['python', 'django']
        
        boost = matcher._calculate_keyword_boost(self.job1, keywords)
        
        # Both keywords should be found, giving 0.10 boost
        self.assertGreater(boost, 0)
        self.assertLessEqual(boost, 0.2)
    
    def test_recency_factor(self):
        """Test recency factor calculation."""
        matcher = JobMatcher()
        
        # Recent job should have high recency factor
        factor = matcher._calculate_recency_factor(self.job1)
        self.assertGreater(factor, 0.9)
    
    @patch('jobs.services.matcher.get_embedding_model')
    def test_match_job_to_user(self, mock_get_model):
        """Test complete job-to-user matching."""
        # Mock embedding model
        mock_model = Mock()
        mock_model.encode.return_value = np.random.rand(384)  # Random embedding
        mock_get_model.return_value = mock_model
        
        matcher = JobMatcher()
        matcher.model = mock_model
        
        # Add CV text to user
        self.user.cv_text = "I am a Python and Django developer with 5 years of experience"
        self.user.save()
        
        score = matcher.match_job_to_user(self.job1, self.user, self.preference)
        
        # Should return a valid score
        self.assertIsNotNone(score)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)
    
    @patch('jobs.services.matcher.get_embedding_model')
    def test_find_matches_for_user(self, mock_get_model):
        """Test finding multiple matches for a user."""
        # Mock embedding model
        mock_model = Mock()
        mock_model.encode.return_value = np.random.rand(384)
        mock_get_model.return_value = mock_model
        
        matcher = JobMatcher()
        matcher.model = mock_model
        
        self.user.cv_text = "Python Django developer"
        self.user.save()
        
        matches = matcher.find_matches_for_user(self.user, self.preference, limit=10)
        
        # Should return list of tuples
        self.assertIsInstance(matches, list)
        
        # Matches should be sorted by score
        if len(matches) > 1:
            for i in range(len(matches) - 1):
                self.assertGreaterEqual(matches[i][1], matches[i+1][1])
    
    @patch('jobs.services.matcher.get_embedding_model')
    def test_already_dispatched_jobs_excluded(self, mock_get_model):
        """Test that already dispatched jobs are excluded."""
        # Mock embedding model
        mock_model = Mock()
        mock_model.encode.return_value = np.random.rand(384)
        mock_get_model.return_value = mock_model
        
        # Create dispatch log for job1
        JobDispatchLog.objects.create(
            user=self.user,
            job=self.job1,
            score=0.8
        )
        
        matcher = JobMatcher()
        matcher.model = mock_model
        
        self.user.cv_text = "Python developer"
        self.user.save()
        
        matches = matcher.find_matches_for_user(self.user, self.preference)
        
        # job1 should be excluded
        job_ids = [job.id for job, score in matches]
        self.assertNotIn(self.job1.id, job_ids)


class MatchAndNotifyTest(TestCase):
    """Test match_and_notify function."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        UserJobPreference.objects.create(
            user=self.user,
            email_enabled=True,
            keywords='python',
            min_score_threshold=0.3
        )
        
        JobPosting.objects.create(
            source='test',
            external_id='test1',
            title='Python Developer',
            company='Test Co',
            location='Remote',
            remote=True,
            url='https://example.com/test1',
            description='Python job',
            published_at=timezone.now()
        )
    
    @patch('jobs.services.matcher.get_embedding_model')
    @patch('jobs.services.matcher._send_job_digest_email')
    def test_match_and_notify_sends_email(self, mock_send_email, mock_get_model):
        """Test that match_and_notify sends emails for matches."""
        # Mock embedding model
        mock_model = Mock()
        mock_model.encode.return_value = np.random.rand(384)
        mock_get_model.return_value = mock_model
        
        # Mock email sending
        mock_send_email.return_value = True
        
        # Add CV to user
        self.user.cv_text = "I am a Python developer"
        self.user.save()
        
        stats = match_and_notify()
        
        # Check stats
        self.assertEqual(stats['users_processed'], 1)
        self.assertGreater(stats['jobs_matched'], 0)
        
        # Check dispatch log created
        self.assertTrue(JobDispatchLog.objects.filter(user=self.user).exists())
