"""
Job matching service to match user profiles with job offers.
"""
import logging
from typing import List, Dict, Tuple
from .models import UserProfile, JobOffer
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)


class JobMatchingService:
    """Service for matching users with job offers"""
    
    def calculate_match_score(self, user_profile: UserProfile, job: JobOffer) -> float:
        """
        Calculate how well a job matches a user's profile
        
        Args:
            user_profile: User profile with skills and preferences
            job: Job offer to match against
            
        Returns:
            Match score between 0 and 100
        """
        score = 0.0
        weights = {
            'skills': 0.5,      # 50% weight
            'title': 0.2,       # 20% weight
            'location': 0.15,   # 15% weight
            'cv_match': 0.15    # 15% weight
        }
        
        # 1. Skills matching
        if user_profile.skills and job.required_skills:
            user_skills_lower = [s.lower() for s in user_profile.skills]
            job_skills_lower = [s.lower() for s in job.required_skills]
            
            matched_skills = set(user_skills_lower) & set(job_skills_lower)
            skill_score = (len(matched_skills) / len(job_skills_lower)) * 100 if job_skills_lower else 0
            score += skill_score * weights['skills']
        
        # 2. Job title matching
        if user_profile.preferred_job_titles:
            title_scores = []
            for preferred_title in user_profile.preferred_job_titles:
                # Use fuzzy matching for job titles
                title_similarity = fuzz.partial_ratio(
                    preferred_title.lower(),
                    job.title.lower()
                )
                title_scores.append(title_similarity)
            
            if title_scores:
                avg_title_score = sum(title_scores) / len(title_scores)
                score += avg_title_score * weights['title']
        
        # 3. Location matching
        if user_profile.preferred_locations and job.location:
            location_match = False
            for preferred_loc in user_profile.preferred_locations:
                if preferred_loc.lower() in job.location.lower() or job.location.lower() in preferred_loc.lower():
                    location_match = True
                    break
            
            # Remote jobs always match location preference
            if 'remote' in job.location.lower():
                location_match = True
            
            if location_match:
                score += 100 * weights['location']
        
        # 4. CV text matching (if available)
        if user_profile.cv_text and job.description:
            # Simple keyword matching from CV to job description
            cv_words = set(user_profile.cv_text.lower().split())
            job_words = set(job.description.lower().split())
            
            common_words = cv_words & job_words
            # Filter out very short words
            meaningful_common = [w for w in common_words if len(w) > 3]
            
            if job_words:
                cv_match_score = min((len(meaningful_common) / len(job_words)) * 200, 100)
                score += cv_match_score * weights['cv_match']
        
        return min(score, 100.0)
    
    def find_matching_jobs(
        self, 
        user_profile: UserProfile, 
        jobs: List[JobOffer], 
        min_score: float = 30.0
    ) -> List[Tuple[JobOffer, float]]:
        """
        Find jobs that match a user's profile
        
        Args:
            user_profile: User profile to match against
            jobs: List of job offers to search through
            min_score: Minimum match score threshold
            
        Returns:
            List of (JobOffer, score) tuples sorted by score (highest first)
        """
        matches = []
        
        for job in jobs:
            score = self.calculate_match_score(user_profile, job)
            
            if score >= min_score:
                matches.append((job, score))
                logger.debug(f"Job '{job.title}' matched with score {score:.2f} for user {user_profile.email}")
        
        # Sort by score (highest first)
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches


# Singleton instance
job_matcher = JobMatchingService()
