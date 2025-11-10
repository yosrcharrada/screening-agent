"""
Tests for job fetcher service.
"""
from django.test import TestCase
from unittest.mock import patch, Mock
from jobs.services.fetcher import RemotiveFetcher, RemoteOKFetcher, fetch_all_sources
from jobs.models import JobPosting


class RemotiveFetcherTest(TestCase):
    """Test Remotive job fetcher."""
    
    @patch('jobs.services.fetcher.requests.get')
    def test_fetch_creates_new_jobs(self, mock_get):
        """Test that fetcher creates new jobs from API response."""
        # Mock API response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'jobs': [
                {
                    'id': '12345',
                    'title': 'Python Developer',
                    'company_name': 'Tech Corp',
                    'candidate_required_location': 'Worldwide',
                    'url': 'https://example.com/job/12345',
                    'description': 'We are looking for a Python developer...',
                    'publication_date': '2024-01-15T10:30:00Z',
                },
                {
                    'id': '12346',
                    'title': 'Django Engineer',
                    'company_name': 'Web Inc',
                    'candidate_required_location': 'Remote',
                    'url': 'https://example.com/job/12346',
                    'description': 'Django position...',
                    'publication_date': '2024-01-16T10:30:00Z',
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Run fetcher
        fetcher = RemotiveFetcher()
        count = fetcher.fetch()
        
        # Assertions
        self.assertEqual(count, 2)
        self.assertEqual(JobPosting.objects.count(), 2)
        
        job1 = JobPosting.objects.get(external_id='12345')
        self.assertEqual(job1.source, 'remotive')
        self.assertEqual(job1.title, 'Python Developer')
        self.assertEqual(job1.company, 'Tech Corp')
        self.assertTrue(job1.remote)
    
    @patch('jobs.services.fetcher.requests.get')
    def test_fetch_skips_duplicates(self, mock_get):
        """Test that fetcher doesn't create duplicate jobs."""
        # Create existing job
        JobPosting.objects.create(
            source='remotive',
            external_id='12345',
            title='Existing Job',
            company='Company',
            location='Remote',
            url='https://example.com/job/12345',
            description='Description'
        )
        
        # Mock API response with same job
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'jobs': [
                {
                    'id': '12345',
                    'title': 'Python Developer',
                    'company_name': 'Tech Corp',
                    'candidate_required_location': 'Worldwide',
                    'url': 'https://example.com/job/12345',
                    'description': 'Description',
                }
            ]
        }
        mock_get.return_value = mock_response
        
        # Run fetcher
        fetcher = RemotiveFetcher()
        count = fetcher.fetch()
        
        # Should skip duplicate
        self.assertEqual(count, 0)
        self.assertEqual(JobPosting.objects.count(), 1)


class RemoteOKFetcherTest(TestCase):
    """Test RemoteOK job fetcher."""
    
    @patch('jobs.services.fetcher.requests.get')
    def test_fetch_creates_jobs(self, mock_get):
        """Test RemoteOK fetcher creates jobs."""
        # Mock API response (RemoteOK returns array with metadata first)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {'metadata': 'info'},  # First item is metadata
            {
                'id': 'abc123',
                'position': 'Senior Python Developer',
                'company': 'Remote Co',
                'location': 'Anywhere',
                'url': 'https://remoteok.com/job/abc123',
                'description': 'Looking for Python dev...',
                'tags': ['python', 'remote'],
                'date': '2024-01-15T10:30:00Z',
            }
        ]
        mock_get.return_value = mock_response
        
        fetcher = RemoteOKFetcher()
        count = fetcher.fetch()
        
        self.assertEqual(count, 1)
        job = JobPosting.objects.get(external_id='abc123')
        self.assertEqual(job.source, 'remoteok')
        self.assertEqual(job.title, 'Senior Python Developer')
        self.assertTrue(job.remote)


class FetchAllSourcesTest(TestCase):
    """Test fetch_all_sources function."""
    
    @patch('jobs.services.fetcher.RemoteOKFetcher.fetch')
    @patch('jobs.services.fetcher.RemotiveFetcher.fetch')
    def test_fetch_all_sources(self, mock_remotive, mock_remoteok):
        """Test that fetch_all_sources calls all fetchers."""
        mock_remotive.return_value = 5
        mock_remoteok.return_value = 3
        
        results = fetch_all_sources()
        
        self.assertEqual(results['remotive'], 5)
        self.assertEqual(results['remoteok'], 3)
        mock_remotive.assert_called_once()
        mock_remoteok.assert_called_once()
