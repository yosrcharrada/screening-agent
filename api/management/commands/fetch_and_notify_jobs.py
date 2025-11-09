"""
Django management command to fetch job offers and send notifications to users.
Usage: python manage.py fetch_and_notify_jobs
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from api.models import UserProfile, JobOffer, JobNotification
from api.job_scraper import job_scraper
from api.job_matcher import job_matcher
from api.email_service import email_service
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Fetch new job offers and send notifications to matching users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually sending emails',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=50,
            help='Maximum number of jobs to fetch (default: 50)',
        )
        parser.add_argument(
            '--min-score',
            type=float,
            default=40.0,
            help='Minimum match score to send notification (default: 40.0)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        job_limit = options['limit']
        min_score = options['min_score']
        
        self.stdout.write(self.style.SUCCESS('Starting job fetch and notification process...'))
        
        # Get active user profiles
        active_users = UserProfile.objects.filter(is_active=True)
        
        if not active_users.exists():
            self.stdout.write(self.style.WARNING('No active user profiles found.'))
            return
        
        self.stdout.write(f'Found {active_users.count()} active user(s)')
        
        # Collect all unique skills and job titles from users
        all_keywords = set()
        for user in active_users:
            all_keywords.update(user.skills)
            all_keywords.update(user.preferred_job_titles)
        
        self.stdout.write(f'Searching for jobs with keywords: {", ".join(list(all_keywords)[:10])}...')
        
        # Fetch jobs
        try:
            fetched_jobs = job_scraper.fetch_jobs(
                keywords=list(all_keywords),
                limit=job_limit
            )
            
            self.stdout.write(self.style.SUCCESS(f'Fetched {len(fetched_jobs)} job offers'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error fetching jobs: {e}'))
            return
        
        if not fetched_jobs:
            self.stdout.write(self.style.WARNING('No jobs fetched. Exiting.'))
            return
        
        # Save new jobs to database
        new_jobs_count = 0
        for job_data in fetched_jobs:
            try:
                job, created = JobOffer.objects.get_or_create(
                    external_id=job_data['external_id'],
                    defaults={
                        'title': job_data['title'],
                        'company': job_data['company'],
                        'description': job_data['description'],
                        'location': job_data['location'],
                        'url': job_data['url'],
                        'source': job_data['source'],
                        'required_skills': job_data['required_skills'],
                        'job_type': job_data['job_type'],
                        'posted_date': job_data['posted_date'],
                        'salary_range': job_data.get('salary_range', ''),
                    }
                )
                if created:
                    new_jobs_count += 1
                    
            except Exception as e:
                logger.error(f"Error saving job {job_data.get('title')}: {e}")
                continue
        
        self.stdout.write(f'Saved {new_jobs_count} new job(s) to database')
        
        # Get recent jobs (from last 7 days)
        recent_date = timezone.now() - timezone.timedelta(days=7)
        recent_jobs = JobOffer.objects.filter(fetched_at__gte=recent_date)
        
        # Match jobs with users and send notifications
        total_notifications = 0
        
        for user in active_users:
            self.stdout.write(f'\nProcessing user: {user.email}')
            
            # Find matching jobs
            matches = job_matcher.find_matching_jobs(
                user_profile=user,
                jobs=list(recent_jobs),
                min_score=min_score
            )
            
            if not matches:
                self.stdout.write(f'  No matching jobs found for {user.email}')
                continue
            
            self.stdout.write(f'  Found {len(matches)} matching job(s)')
            
            # Filter out jobs already notified
            new_matches = []
            match_scores = {}
            
            for job, score in matches:
                # Check if already notified
                already_notified = JobNotification.objects.filter(
                    user_profile=user,
                    job_offer=job
                ).exists()
                
                if not already_notified:
                    new_matches.append(job)
                    match_scores[job.id] = score
            
            if not new_matches:
                self.stdout.write(f'  All matching jobs already notified for {user.email}')
                continue
            
            self.stdout.write(f'  {len(new_matches)} new job(s) to notify')
            
            # Send email notification
            if not dry_run:
                try:
                    success = email_service.send_job_notification(
                        user_profile=user,
                        jobs=new_matches,
                        match_scores=match_scores
                    )
                    
                    if success:
                        # Create notification records
                        for job in new_matches:
                            JobNotification.objects.create(
                                user_profile=user,
                                job_offer=job,
                                match_score=match_scores.get(job.id, 0)
                            )
                        
                        total_notifications += len(new_matches)
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Email sent to {user.email}'))
                    else:
                        self.stdout.write(self.style.ERROR(f'  ✗ Failed to send email to {user.email}'))
                        
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'  ✗ Error sending email to {user.email}: {e}'))
            else:
                self.stdout.write(f'  [DRY RUN] Would send email with {len(new_matches)} job(s) to {user.email}')
                # Show job details in dry run
                for job in new_matches[:3]:  # Show first 3
                    score = match_scores.get(job.id, 0)
                    self.stdout.write(f'    - {job.title} at {job.company} (Score: {score:.1f}%)')
        
        # Summary
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(self.style.SUCCESS('[DRY RUN] Process completed successfully'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Process completed! Sent {total_notifications} notification(s)'))
