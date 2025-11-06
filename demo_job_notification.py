#!/usr/bin/env python
"""
Example script demonstrating the job notification feature.
This shows how to use the API programmatically.
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/runner/work/screening-agent/screening-agent')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from api.models import UserProfile, JobOffer, JobNotification
from api.job_scraper import job_scraper
from api.job_matcher import job_matcher
from api.email_service import email_service


def example_1_create_user_profile():
    """Example: Create a user profile"""
    print("\n" + "="*60)
    print("Example 1: Creating a User Profile")
    print("="*60)
    
    # Create or get user profile
    user, created = UserProfile.objects.get_or_create(
        email="demo@example.com",
        defaults={
            "name": "Demo User",
            "skills": ["python", "django", "javascript", "react", "docker"],
            "preferred_job_titles": ["Software Engineer", "Full Stack Developer", "Python Developer"],
            "preferred_locations": ["Remote", "New York", "San Francisco"],
            "cv_text": "Experienced software engineer with 5 years in Python and Django development. "
                      "Built multiple web applications using React and RESTful APIs.",
            "is_active": True
        }
    )
    
    if created:
        print(f"✓ Created new user profile: {user.email}")
    else:
        print(f"✓ User profile already exists: {user.email}")
    
    print(f"  Name: {user.name}")
    print(f"  Skills: {', '.join(user.skills)}")
    print(f"  Preferred Titles: {', '.join(user.preferred_job_titles)}")
    print(f"  Active: {user.is_active}")
    
    return user


def example_2_fetch_jobs():
    """Example: Fetch jobs from free sources"""
    print("\n" + "="*60)
    print("Example 2: Fetching Jobs")
    print("="*60)
    
    # Fetch jobs for Python developers
    keywords = ["python", "django", "software engineer"]
    print(f"Searching for jobs with keywords: {', '.join(keywords)}")
    
    try:
        jobs = job_scraper.fetch_jobs(keywords=keywords, limit=10)
        print(f"✓ Fetched {len(jobs)} jobs")
        
        # Save jobs to database
        saved_count = 0
        for job_data in jobs:
            try:
                job, created = JobOffer.objects.get_or_create(
                    external_id=job_data['external_id'],
                    defaults=job_data
                )
                if created:
                    saved_count += 1
            except Exception as e:
                print(f"  Error saving job: {e}")
                continue
        
        print(f"✓ Saved {saved_count} new jobs to database")
        
        # Show sample jobs
        if jobs:
            print("\nSample jobs:")
            for i, job in enumerate(jobs[:3], 1):
                print(f"\n  {i}. {job['title']}")
                print(f"     Company: {job['company']}")
                print(f"     Location: {job['location']}")
                print(f"     Skills: {', '.join(job['required_skills'][:3])}")
        
        return jobs
        
    except Exception as e:
        print(f"✗ Error fetching jobs: {e}")
        return []


def example_3_match_jobs(user):
    """Example: Match jobs with user profile"""
    print("\n" + "="*60)
    print("Example 3: Matching Jobs")
    print("="*60)
    
    # Get recent jobs from database
    recent_jobs = JobOffer.objects.all()[:20]
    
    if not recent_jobs:
        print("No jobs in database. Run example 2 first.")
        return []
    
    print(f"Matching {recent_jobs.count()} jobs against user profile...")
    
    # Find matching jobs
    matches = job_matcher.find_matching_jobs(
        user_profile=user,
        jobs=list(recent_jobs),
        min_score=30.0
    )
    
    print(f"✓ Found {len(matches)} matching jobs (score >= 30)")
    
    # Show top matches
    if matches:
        print("\nTop 5 matches:")
        for i, (job, score) in enumerate(matches[:5], 1):
            print(f"\n  {i}. {job.title} at {job.company}")
            print(f"     Match Score: {score:.1f}%")
            print(f"     Location: {job.location}")
            print(f"     Skills: {', '.join(job.required_skills[:3])}")
    
    return matches


def example_4_send_notification(user, matches):
    """Example: Send email notification"""
    print("\n" + "="*60)
    print("Example 4: Sending Email Notification")
    print("="*60)
    
    if not matches:
        print("No matches to send. Run example 3 first.")
        return
    
    # Get top 5 jobs
    top_jobs = [job for job, score in matches[:5]]
    match_scores = {job.id: score for job, score in matches[:5]}
    
    print(f"Preparing to send notification with {len(top_jobs)} jobs...")
    print(f"Recipient: {user.email}")
    
    # Note: This will use console backend by default (prints to console)
    # To actually send emails, configure SMTP in settings
    try:
        success = email_service.send_job_notification(
            user_profile=user,
            jobs=top_jobs,
            match_scores=match_scores
        )
        
        if success:
            print("✓ Email notification sent successfully!")
            print("  (Check console output above for email content)")
            
            # Create notification records
            for job in top_jobs:
                JobNotification.objects.get_or_create(
                    user_profile=user,
                    job_offer=job,
                    defaults={
                        'match_score': match_scores.get(job.id, 0)
                    }
                )
            print(f"✓ Created {len(top_jobs)} notification records")
        else:
            print("✗ Failed to send email notification")
            
    except Exception as e:
        print(f"✗ Error sending notification: {e}")


def example_5_view_notifications(user):
    """Example: View user notifications"""
    print("\n" + "="*60)
    print("Example 5: Viewing Notifications")
    print("="*60)
    
    notifications = JobNotification.objects.filter(user_profile=user).order_by('-sent_at')
    
    print(f"User {user.email} has {notifications.count()} notification(s)")
    
    if notifications:
        print("\nRecent notifications:")
        for i, notif in enumerate(notifications[:5], 1):
            status = "✓ Read" if notif.is_read else "○ Unread"
            print(f"\n  {i}. [{status}] {notif.job_offer.title}")
            print(f"     Company: {notif.job_offer.company}")
            print(f"     Match Score: {notif.match_score:.1f}%")
            print(f"     Sent: {notif.sent_at.strftime('%Y-%m-%d %H:%M')}")


def main():
    print("\n" + "="*70)
    print(" " * 15 + "JOB NOTIFICATION FEATURE - DEMO")
    print("="*70)
    print("\nThis demo shows how to use the job notification feature.")
    print("Note: Emails will be printed to console (not actually sent).")
    print("      To send real emails, configure SMTP in core/settings.py")
    
    try:
        # Example 1: Create user profile
        user = example_1_create_user_profile()
        
        # Example 2: Fetch jobs
        jobs = example_2_fetch_jobs()
        
        # Example 3: Match jobs
        matches = example_3_match_jobs(user)
        
        # Example 4: Send notification
        if matches:
            example_4_send_notification(user, matches)
        
        # Example 5: View notifications
        example_5_view_notifications(user)
        
        print("\n" + "="*70)
        print("✅ Demo completed successfully!")
        print("="*70)
        print("\nNext steps:")
        print("1. Configure email settings in core/settings.py")
        print("2. Run: python manage.py fetch_and_notify_jobs")
        print("3. Schedule the command to run periodically")
        print("4. Check JOB_NOTIFICATION_README.md for full documentation")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
