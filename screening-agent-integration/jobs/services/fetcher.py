"""
Job fetching service for various job boards.
Implements retry logic and proper deduplication.
"""
import requests
import logging
import time
from datetime import datetime
from typing import List, Dict, Optional
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from jobs.models import JobPosting

logger = logging.getLogger(__name__)


class JobFetcher:
    """Base class for job fetchers."""
    
    REQUEST_TIMEOUT = 30  # seconds
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; JobAggregator/1.0)'
        }
    
    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """Make HTTP request with retry logic."""
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=self.REQUEST_TIMEOUT
                )
                response.raise_for_status()
                return response.json()
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt + 1}/{self.MAX_RETRIES} for {url}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (2 ** attempt))  # Exponential backoff
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error on attempt {attempt + 1}/{self.MAX_RETRIES}: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAY * (2 ** attempt))
            except Exception as e:
                logger.error(f"Unexpected error fetching from {url}: {e}")
                break
        
        return None
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None
        
        try:
            # Handle ISO format with Z
            if isinstance(date_str, str) and date_str.endswith('Z'):
                date_str = date_str.replace('Z', '+00:00')
            
            parsed = parse_datetime(date_str)
            if parsed:
                # Make timezone aware if not already
                if timezone.is_naive(parsed):
                    parsed = timezone.make_aware(parsed)
                return parsed
        except Exception as e:
            logger.warning(f"Failed to parse date '{date_str}': {e}")
        
        return None


class RemotiveFetcher(JobFetcher):
    """Fetcher for Remotive API."""
    
    API_URL = "https://remotive.com/api/remote-jobs"
    
    def fetch(self) -> int:
        """Fetch jobs from Remotive and return count of new jobs created."""
        logger.info("Fetching jobs from Remotive...")
        
        data = self._make_request(self.API_URL)
        if not data:
            logger.error("Failed to fetch from Remotive")
            return 0
        
        jobs = data.get('jobs', [])
        created_count = 0
        
        for job_data in jobs:
            try:
                external_id = str(job_data.get('id', ''))
                if not external_id:
                    continue
                
                # Check if already exists
                if JobPosting.objects.filter(source='remotive', external_id=external_id).exists():
                    continue
                
                # Create job posting
                job = JobPosting(
                    source='remotive',
                    external_id=external_id,
                    title=job_data.get('title', ''),
                    company=job_data.get('company_name', ''),
                    location=job_data.get('candidate_required_location', 'Worldwide'),
                    remote=True,  # Remotive is remote-only
                    url=job_data.get('url', ''),
                    description=job_data.get('description', ''),
                    published_at=self._parse_date(job_data.get('publication_date')),
                    raw_data=job_data
                )
                job.save()
                created_count += 1
                
            except Exception as e:
                logger.error(f"Error creating job from Remotive data: {e}")
                continue
        
        logger.info(f"Created {created_count} new jobs from Remotive")
        return created_count


class RemoteOKFetcher(JobFetcher):
    """Fetcher for RemoteOK API."""
    
    API_URL = "https://remoteok.com/api"
    
    def fetch(self) -> int:
        """Fetch jobs from RemoteOK and return count of new jobs created."""
        logger.info("Fetching jobs from RemoteOK...")
        
        data = self._make_request(self.API_URL)
        if not data:
            logger.error("Failed to fetch from RemoteOK")
            return 0
        
        # RemoteOK returns array directly, first item is metadata
        if not isinstance(data, list) or len(data) < 2:
            logger.error("Unexpected RemoteOK response format")
            return 0
        
        jobs = data[1:]  # Skip first metadata item
        created_count = 0
        
        for job_data in jobs:
            try:
                external_id = str(job_data.get('id', ''))
                if not external_id:
                    continue
                
                # Check if already exists
                if JobPosting.objects.filter(source='remoteok', external_id=external_id).exists():
                    continue
                
                # Determine if remote
                tags = job_data.get('tags', [])
                is_remote = any(tag.lower() in ['remote', 'worldwide'] for tag in tags) if tags else True
                
                # Create job posting
                job = JobPosting(
                    source='remoteok',
                    external_id=external_id,
                    title=job_data.get('position', ''),
                    company=job_data.get('company', ''),
                    location=job_data.get('location', 'Worldwide'),
                    remote=is_remote,
                    url=job_data.get('url', f"https://remoteok.com/remote-jobs/{external_id}"),
                    description=job_data.get('description', ''),
                    published_at=self._parse_date(job_data.get('date')),
                    raw_data=job_data
                )
                job.save()
                created_count += 1
                
            except Exception as e:
                logger.error(f"Error creating job from RemoteOK data: {e}")
                continue
        
        logger.info(f"Created {created_count} new jobs from RemoteOK")
        return created_count


def fetch_all_sources() -> Dict[str, int]:
    """Fetch jobs from all configured sources."""
    results = {}
    
    # Fetch from Remotive
    try:
        fetcher = RemotiveFetcher()
        results['remotive'] = fetcher.fetch()
    except Exception as e:
        logger.error(f"Error fetching from Remotive: {e}")
        results['remotive'] = 0
    
    # Fetch from RemoteOK
    try:
        fetcher = RemoteOKFetcher()
        results['remoteok'] = fetcher.fetch()
    except Exception as e:
        logger.error(f"Error fetching from RemoteOK: {e}")
        results['remoteok'] = 0
    
    total = sum(results.values())
    logger.info(f"Fetched total of {total} new jobs from all sources")
    
    return results
