"""
Job scraper module for fetching job offers from free sources.
Uses public APIs and web scraping where allowed.
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import logging
import re
import time
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class JobScraper:
    """Scraper for fetching job offers from various free sources"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def fetch_jobs(self, keywords: List[str], location: str = "", limit: int = 50) -> List[Dict]:
        """
        Fetch jobs from multiple sources
        
        Args:
            keywords: List of job keywords/skills to search for
            location: Location to search in
            limit: Maximum number of jobs to fetch
            
        Returns:
            List of job dictionaries
        """
        all_jobs = []
        
        # Try Remotive API with retry logic
        try:
            remotive_jobs = self._fetch_from_remotive(keywords, limit=limit//2)
            all_jobs.extend(remotive_jobs)
            logger.info(f"Fetched {len(remotive_jobs)} jobs from Remotive")
        except Exception as e:
            logger.error(f"Error fetching from Remotive: {e}")
        
        # Note: GitHub source is experimental and may have low accuracy
        # GitHub Jobs API is deprecated, so we search repositories instead
        # This may return false positives and should be used as supplementary source
        try:
            github_jobs = self._fetch_from_github_jobs(keywords, location, limit=limit//2)
            all_jobs.extend(github_jobs)
            logger.info(f"Fetched {len(github_jobs)} jobs from GitHub")
        except Exception as e:
            logger.error(f"Error fetching from GitHub: {e}")
        
        return all_jobs[:limit]
    
    def _fetch_from_remotive(self, keywords: List[str], limit: int = 25) -> List[Dict]:
        """
        Fetch jobs from Remotive API (free, no API key required)
        API: https://remotive.com/api/remote-jobs
        
        Implements retry logic with exponential backoff for reliability.
        """
        jobs = []
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                url = "https://remotive.com/api/remote-jobs"
                response = requests.get(url, headers=self.headers, timeout=15)
                response.raise_for_status()  # Raise exception for bad status codes
                
                data = response.json()
                
                for job_data in data.get('jobs', [])[:limit]:
                    # Filter by keywords if provided
                    if keywords:
                        job_text = f"{job_data.get('title', '')} {job_data.get('description', '')}".lower()
                        if not any(keyword.lower() in job_text for keyword in keywords):
                            continue
                    
                    job = {
                        'title': job_data.get('title', ''),
                        'company': job_data.get('company_name', ''),
                        'description': job_data.get('description', '')[:1000],  # Limit description length
                        'location': job_data.get('candidate_required_location', 'Remote'),
                        'url': job_data.get('url', ''),
                        'source': 'remotive',
                        'required_skills': self._extract_skills(job_data.get('description', '')),
                        'job_type': job_data.get('job_type', 'full-time'),
                        'posted_date': self._parse_date(job_data.get('publication_date')),
                        'external_id': f"remotive_{job_data.get('id', '')}",
                        'salary_range': job_data.get('salary', ''),
                    }
                    jobs.append(job)
                
                # Success - break out of retry loop
                break
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout fetching from Remotive (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))  # Exponential backoff
                else:
                    logger.error("Max retries reached for Remotive API")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error fetching from Remotive (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    logger.error("Max retries reached for Remotive API")
                    
            except Exception as e:
                logger.error(f"Unexpected error in _fetch_from_remotive: {e}")
                break  # Don't retry on unexpected errors
        
        return jobs
    
    def _fetch_from_github_jobs(self, keywords: List[str], location: str = "", limit: int = 25) -> List[Dict]:
        """
        Fetch jobs from GitHub (using repository search)
        
        IMPORTANT: GitHub Jobs API is deprecated. This method searches GitHub repositories
        for job postings, which may have low accuracy and reliability. Results may include
        false positives or outdated information. Use as supplementary source only.
        
        Expected success rate: ~20-30% of results may be actual job postings.
        Recommended: Use Remotive API as primary source.
        """
        jobs = []
        max_retries = 2
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                # Search GitHub repositories with "hiring" or "jobs" topics
                query = " ".join(keywords) if keywords else "developer"
                url = f"https://api.github.com/search/repositories"
                params = {
                    'q': f'{query} hiring jobs in:readme',
                    'sort': 'updated',
                    'per_page': min(limit, 30)
                }
                
                response = requests.get(url, headers=self.headers, params=params, timeout=15)
                response.raise_for_status()
                
                data = response.json()
                
                for repo in data.get('items', []):
                    # Try to extract job info from README
                    readme_url = f"https://api.github.com/repos/{repo['full_name']}/readme"
                    readme_response = requests.get(
                        readme_url, 
                        headers={'Accept': 'application/vnd.github.v3.raw'}, 
                        timeout=10
                    )
                    
                    if readme_response.status_code == 200:
                        readme_text = readme_response.text[:2000]  # Limit text
                        
                        # Basic extraction (can be improved)
                        if 'hiring' in readme_text.lower() or 'job' in readme_text.lower():
                            job = {
                                'title': f"Position at {repo['owner']['login']}",
                                'company': repo['owner']['login'],
                                'description': readme_text[:500],
                                'location': location or 'Remote',
                                'url': repo['html_url'],
                                'source': 'github',
                                'required_skills': self._extract_skills(readme_text),
                                'job_type': 'full-time',
                                'posted_date': self._parse_date(repo.get('updated_at')),
                                'external_id': f"github_{repo['id']}",
                                'salary_range': '',
                            }
                            jobs.append(job)
                            
                            if len(jobs) >= limit:
                                break
                
                # Success - break retry loop
                break
                
            except requests.exceptions.Timeout:
                logger.warning(f"Timeout fetching from GitHub (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request error fetching from GitHub (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    
            except Exception as e:
                logger.error(f"Unexpected error in _fetch_from_github_jobs: {e}")
                break
        
        return jobs
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract potential skills from job description"""
        if not text:
            return []
        
        # Common tech skills to look for
        common_skills = [
            'python', 'java', 'javascript', 'typescript', 'react', 'angular', 'vue',
            'node.js', 'django', 'flask', 'spring', 'sql', 'nosql', 'mongodb',
            'postgresql', 'mysql', 'aws', 'azure', 'gcp', 'docker', 'kubernetes',
            'git', 'ci/cd', 'agile', 'scrum', 'machine learning', 'ai', 'data science',
            'html', 'css', 'rest api', 'graphql', 'microservices', 'tensorflow',
            'pytorch', 'pandas', 'numpy', 'scikit-learn', 'nlp', 'computer vision'
        ]
        
        text_lower = text.lower()
        found_skills = []
        
        for skill in common_skills:
            if skill.lower() in text_lower:
                found_skills.append(skill)
        
        return list(set(found_skills))  # Remove duplicates
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        
        try:
            # Try ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except:
            try:
                # Try common formats
                for fmt in ['%Y-%m-%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S']:
                    try:
                        return datetime.strptime(date_str, fmt)
                    except:
                        continue
            except:
                pass
        
        return None


# Singleton instance
job_scraper = JobScraper()
