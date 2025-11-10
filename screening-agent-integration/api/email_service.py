"""
Email notification service for sending job offers to users.
Uses Django's built-in email backend.
"""
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
import logging
from typing import List, Dict
from .models import UserProfile, JobOffer, JobNotification

logger = logging.getLogger(__name__)


class EmailNotificationService:
    """Service for sending email notifications about job offers"""
    
    def __init__(self):
        self.from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@screening-agent.com')
    
    def send_job_notification(self, user_profile: UserProfile, jobs: List[JobOffer], match_scores: Dict[int, float] = None) -> bool:
        """
        Send email notification with matching job offers
        
        Args:
            user_profile: User profile to send notification to
            jobs: List of job offers to include
            match_scores: Optional dictionary mapping job IDs to match scores
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not jobs:
            logger.info(f"No jobs to send to {user_profile.email}")
            return False
        
        try:
            subject = f"🎯 {len(jobs)} New Job{'s' if len(jobs) > 1 else ''} Matching Your Profile"
            
            # Prepare job data for email
            job_data = []
            for job in jobs:
                match_score = match_scores.get(job.id, 0) if match_scores else 0
                job_data.append({
                    'job': job,
                    'match_score': match_score
                })
            
            # Create plain text message
            plain_message = self._create_plain_text_email(user_profile, job_data)
            
            # Create HTML message (if you want to add HTML templates later)
            html_message = self._create_html_email(user_profile, job_data)
            
            # Send email
            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=self.from_email,
                to=[user_profile.email]
            )
            
            if html_message:
                email.attach_alternative(html_message, "text/html")
            
            email.send()
            
            logger.info(f"Successfully sent job notification to {user_profile.email} with {len(jobs)} jobs")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {user_profile.email}: {e}")
            return False
    
    def _create_plain_text_email(self, user_profile: UserProfile, job_data: List[Dict]) -> str:
        """Create plain text email content"""
        message_lines = [
            f"Hi {user_profile.name or 'there'}!",
            "",
            f"We found {len(job_data)} new job offer{'s' if len(job_data) > 1 else ''} matching your profile:",
            "",
        ]
        
        for idx, data in enumerate(job_data, 1):
            job = data['job']
            match_score = data['match_score']
            
            message_lines.extend([
                f"{'='*60}",
                f"{idx}. {job.title}",
                f"   Company: {job.company}",
                f"   Location: {job.location}",
                f"   Match Score: {match_score:.0f}%",
            ])
            
            if job.required_skills:
                skills_str = ", ".join(job.required_skills[:5])
                message_lines.append(f"   Skills: {skills_str}")
            
            message_lines.extend([
                f"   Link: {job.url}",
                "",
            ])
        
        message_lines.extend([
            "",
            "Good luck with your applications!",
            "",
            "---",
            "To stop receiving these notifications, please update your profile settings.",
        ])
        
        return "\n".join(message_lines)
    
    def _create_html_email(self, user_profile: UserProfile, job_data: List[Dict]) -> str:
        """Create HTML email content"""
        html_lines = [
            "<html>",
            "<body style='font-family: Arial, sans-serif; line-height: 1.6;'>",
            f"<h2>Hi {user_profile.name or 'there'}!</h2>",
            f"<p>We found <strong>{len(job_data)}</strong> new job offer{'s' if len(job_data) > 1 else ''} matching your profile:</p>",
        ]
        
        for idx, data in enumerate(job_data, 1):
            job = data['job']
            match_score = data['match_score']
            
            html_lines.extend([
                "<div style='border: 1px solid #ddd; padding: 15px; margin: 15px 0; border-radius: 5px;'>",
                f"<h3 style='margin-top: 0;'>{idx}. {job.title}</h3>",
                f"<p><strong>Company:</strong> {job.company}</p>",
                f"<p><strong>Location:</strong> {job.location}</p>",
                f"<p><strong>Match Score:</strong> <span style='color: #28a745;'>{match_score:.0f}%</span></p>",
            ])
            
            if job.required_skills:
                skills_html = ", ".join([f"<span style='background: #e9ecef; padding: 2px 8px; border-radius: 3px; margin-right: 5px;'>{skill}</span>" for skill in job.required_skills[:5]])
                html_lines.append(f"<p><strong>Skills:</strong> {skills_html}</p>")
            
            if job.description:
                desc_preview = job.description[:200] + "..." if len(job.description) > 200 else job.description
                html_lines.append(f"<p>{desc_preview}</p>")
            
            html_lines.extend([
                f"<p><a href='{job.url}' style='background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;'>View Job</a></p>",
                "</div>",
            ])
        
        html_lines.extend([
            "<hr>",
            "<p><small>To stop receiving these notifications, please update your profile settings.</small></p>",
            "</body>",
            "</html>",
        ])
        
        return "\n".join(html_lines)
    
    def send_test_email(self, email: str) -> bool:
        """Send a test email to verify email configuration"""
        try:
            subject = "Test Email from Screening Agent"
            message = "This is a test email. Your email configuration is working correctly!"
            
            send_mail(
                subject=subject,
                message=message,
                from_email=self.from_email,
                recipient_list=[email],
                fail_silently=False,
            )
            
            logger.info(f"Test email sent successfully to {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send test email to {email}: {e}")
            return False


# Singleton instance
email_service = EmailNotificationService()
