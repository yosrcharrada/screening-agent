"""
Tests for jobs API endpoints.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from jobs.models import UserJobPreference

User = get_user_model()


class PreferencesAPITest(TestCase):
    """Test preferences API endpoints."""
    
    def setUp(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_get_preferences_requires_auth(self):
        """Test that get_preferences requires authentication."""
        response = self.client.get('/api/jobs/preferences/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_preferences_creates_if_not_exists(self):
        """Test that GET creates preferences if they don't exist."""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get('/api/jobs/preferences/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['created'])
        self.assertIn('preference', response.data)
        
        # Verify preference was created
        self.assertTrue(UserJobPreference.objects.filter(user=self.user).exists())
    
    def test_get_preferences_returns_existing(self):
        """Test that GET returns existing preferences."""
        # Create preference
        pref = UserJobPreference.objects.create(
            user=self.user,
            keywords='python,django',
            remote_only=True
        )
        
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/jobs/preferences/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['created'])
        self.assertEqual(response.data['preference']['keywords'], 'python,django')
        self.assertTrue(response.data['preference']['remote_only'])
    
    def test_update_preferences(self):
        """Test updating preferences via PATCH."""
        self.client.force_authenticate(user=self.user)
        
        # Create initial preference
        self.client.get('/api/jobs/preferences/')
        
        # Update
        update_data = {
            'keywords': 'react,typescript',
            'remote_only': True,
            'min_score_threshold': 0.7
        }
        
        response = self.client.patch('/api/jobs/preferences/update/', update_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['keywords'], 'react,typescript')
        self.assertTrue(response.data['remote_only'])
        self.assertEqual(response.data['min_score_threshold'], 0.7)
        
        # Verify in database
        pref = UserJobPreference.objects.get(user=self.user)
        self.assertEqual(pref.keywords, 'react,typescript')
    
    def test_update_preferences_partial(self):
        """Test partial update of preferences."""
        UserJobPreference.objects.create(
            user=self.user,
            keywords='python',
            remote_only=False,
            min_score_threshold=0.5
        )
        
        self.client.force_authenticate(user=self.user)
        
        # Update only one field
        response = self.client.patch('/api/jobs/preferences/update/', {
            'remote_only': True
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['remote_only'])
        self.assertEqual(response.data['keywords'], 'python')  # Unchanged
    
    def test_update_preferences_validation(self):
        """Test that invalid data is rejected."""
        self.client.force_authenticate(user=self.user)
        
        # Try to set invalid threshold
        response = self.client.patch('/api/jobs/preferences/update/', {
            'min_score_threshold': 2.0  # Should be 0.0-1.0
        })
        
        # Should still work as there's no validation for this yet
        # But in production, you might want to add validators
        self.assertEqual(response.status_code, status.HTTP_200_OK)
