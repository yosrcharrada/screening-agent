"""
Job matching service using embeddings and keyword matching.
"""
import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings

from jobs.models import JobPosting, UserJobPreference, JobDispatchLog

logger = logging.getLogger(__name__)

# Lazy load sentence transformers to avoid loading during migrations
_embedding_model = None


def get_embedding_model():
    """Lazy load sentence transformer model."""
    global _embedding_model
    if _embedding_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Loaded sentence transformer model: all-MiniLM-L6-v2")
        except ImportError:
            logger.error("sentence-transformers not installed. Install with: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    return _embedding_model


User = get_user_model()


class JobMatcher:
    """Matches jobs to users based on embeddings and preferences."""
    
    def __init__(self):
        self.model = None  # Lazy loaded
    
    def _get_model(self):
        """Get or load the embedding model."""
        if self.model is None:
            self.model = get_embedding_model()
        return self.model
    
    def _compute_embedding(self, text: str) -> np.ndarray:
        """Compute embedding for text."""
        model = self._get_model()
        return model.encode(text, convert_to_numpy=True)
    
    def _compute_cosine_similarity(self, emb1: np.ndarray, emb2: np.ndarray) -> float:
        """Compute cosine similarity between two embeddings."""
        dot_product = np.dot(emb1, emb2)
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def _calculate_keyword_boost(self, job: JobPosting, keywords: List[str]) -> float:
        """Calculate keyword overlap boost (0.0 to 0.2)."""
        if not keywords:
            return 0.0
        
        job_text = f"{job.title} {job.description} {job.company}".lower()
        matches = sum(1 for keyword in keywords if keyword in job_text)
        
        # Each keyword match gives 0.05 boost, max 0.2
        return min(matches * 0.05, 0.2)
    
    def _calculate_recency_factor(self, job: JobPosting) -> float:
        """Calculate recency factor (0.0 to 1.0)."""
        age_days = job.age_in_days
        
        if age_days is None:
            return 0.5  # Default for jobs without publish date
        
        # Recent jobs (0-30 days) get higher scores
        # Formula: 1 - min(age_days / 30, 1.0)
        return max(0.0, 1.0 - min(age_days / 30.0, 1.0))
    
    def _check_location_match(self, job: JobPosting, preference: UserJobPreference) -> bool:
        """Check if job location matches user preferences."""
        # If remote only and job is not remote, reject
        if preference.remote_only and not job.remote:
            return False
        
        # If no specific locations, accept
        locations = preference.get_locations_list()
        if not locations:
            return True
        
        # Check if job location matches any preferred location
        job_location = job.location.lower()
        for loc in locations:
            if loc.lower() in job_location or job_location in loc.lower():
                return True
        
        # Remote jobs always match
        if job.remote:
            return True
        
        return False
    
    def match_job_to_user(self, job: JobPosting, user: User, preference: UserJobPreference) -> Optional[float]:
        """
        Calculate match score for a job-user pair.
        
        Returns:
            Match score (0.0 to 1.0) or None if job doesn't meet criteria
        """
        # Check location filter
        if not self._check_location_match(job, preference):
            return None
        
        # Build user text from CV or fallback
        user_text = getattr(user, 'cv_text', None) or f"{user.username} {user.email}"
        if hasattr(user, 'userprofile') and user.userprofile.cv_text:
            user_text = user.userprofile.cv_text
        
        # Fallback if no substantial user text
        if len(user_text.strip()) < 20:
            keywords = preference.get_keywords_list()
            user_text = " ".join(keywords) if keywords else user.username
        
        # Build job text
        job_text = f"{job.title} {job.description[:500]} {job.company}"
        
        # Compute embeddings
        try:
            user_emb = self._compute_embedding(user_text[:1000])  # Limit length
            job_emb = self._compute_embedding(job_text[:1000])
            
            # Calculate cosine similarity
            cosine_sim = self._compute_cosine_similarity(user_emb, job_emb)
        except Exception as e:
            logger.error(f"Error computing embeddings: {e}")
            cosine_sim = 0.5  # Fallback
        
        # Calculate additional factors
        keyword_boost = self._calculate_keyword_boost(job, preference.get_keywords_list())
        recency_factor = self._calculate_recency_factor(job)
        
        # Final score: weighted combination
        # 60% embedding similarity + 30% keyword boost + 10% recency
        final_score = (
            0.6 * cosine_sim +
            0.3 * keyword_boost +
            0.1 * recency_factor
        )
        
        return min(max(final_score, 0.0), 1.0)  # Clamp to [0, 1]
    
    def find_matches_for_user(
        self,
        user: User,
        preference: UserJobPreference,
        limit: int = None
    ) -> List[Tuple[JobPosting, float]]:
        """
        Find matching jobs for a user.
        
        Returns:
            List of (JobPosting, score) tuples, sorted by score descending
        """
        limit = limit or preference.max_jobs_per_email
        
        # Get recent jobs (last 30 days)
        recent_date = timezone.now() - timezone.timedelta(days=30)
        jobs = JobPosting.objects.filter(created_at__gte=recent_date)
        
        # Filter out already dispatched jobs
        dispatched_job_ids = JobDispatchLog.objects.filter(
            user=user
        ).values_list('job_id', flat=True)
        jobs = jobs.exclude(id__in=dispatched_job_ids)
        
        matches = []
        for job in jobs:
            score = self.match_job_to_user(job, user, preference)
            if score is not None and score >= preference.min_score_threshold:
                matches.append((job, score))
        
        # Sort by score descending
        matches.sort(key=lambda x: x[1], reverse=True)
        
        return matches[:limit]


def match_and_notify() -> Dict[str, int]:
    """
    Match jobs to all active users and send email notifications.
    
    Returns:
        Dictionary with statistics: users_processed, jobs_matched, emails_sent
    """
    User = get_user_model()
    matcher = JobMatcher()
    
    stats = {
        'users_processed': 0,
        'jobs_matched': 0,
        'emails_sent': 0,
        'errors': 0
    }
    
    # Get all users with preferences
    users_with_prefs = User.objects.filter(
        job_preference__email_enabled=True
    ).select_related('job_preference')
    
    for user in users_with_prefs:
        try:
            preference = user.job_preference
            
            # Find matching jobs
            matches = matcher.find_matches_for_user(user, preference)
            
            if not matches:
                logger.info(f"No matching jobs for user {user.username}")
                stats['users_processed'] += 1
                continue
            
            # Send email digest
            email_sent = _send_job_digest_email(user, matches)
            
            if email_sent:
                # Log dispatches
                for job, score in matches:
                    JobDispatchLog.objects.create(
                        user=user,
                        job=job,
                        score=score
                    )
                
                stats['jobs_matched'] += len(matches)
                stats['emails_sent'] += 1
                logger.info(f"Sent {len(matches)} jobs to {user.username}")
            
            stats['users_processed'] += 1
            
        except Exception as e:
            logger.error(f"Error processing user {user.username}: {e}")
            stats['errors'] += 1
    
    return stats


def _send_job_digest_email(user: User, matches: List[Tuple[JobPosting, float]]) -> bool:
    """Send email digest with matched jobs."""
    try:
        # Build email content
        subject = f"🎯 {len(matches)} New Job Match{'es' if len(matches) > 1 else ''} for You"
        
        # Plain text body
        body_lines = [
            f"Hi {user.username}!",
            "",
            f"We found {len(matches)} job{'s' if len(matches) > 1 else ''} that match your preferences:",
            "",
        ]
        
        for idx, (job, score) in enumerate(matches, 1):
            body_lines.extend([
                f"{idx}. {job.title}",
                f"   Company: {job.company}",
                f"   Location: {job.location}",
                f"   Match Score: {score*100:.0f}%",
                f"   URL: {job.url}",
                "",
            ])
        
        body_lines.extend([
            "---",
            "Update your preferences or unsubscribe at any time.",
        ])
        
        body = "\n".join(body_lines)
        
        # Get from email from settings
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@example.com')
        
        # Send email
        send_mail(
            subject=subject,
            message=body,
            from_email=from_email,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {user.email}: {e}")
        return False
