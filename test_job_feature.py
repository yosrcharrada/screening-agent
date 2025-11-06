#!/usr/bin/env python
"""
Standalone test script for job notification feature.
This tests the core functionality without Django dependencies.
"""

import sys
import os

# Add the project to path - use relative path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

import django
django.setup()

# Simple test without Django
def test_job_scraper():
    """Test job scraper module"""
    print("Testing Job Scraper...")
    from api.job_scraper import job_scraper
    
    # Test skill extraction
    description = "We need Python, Django, and React developers"
    skills = job_scraper._extract_skills(description)
    assert "python" in skills, "Python should be extracted"
    assert "django" in skills, "Django should be extracted"
    assert "react" in skills, "React should be extracted"
    print("✓ Skill extraction works")
    
    # Test date parsing
    from datetime import datetime
    date_str = "2024-01-15T10:30:00Z"
    parsed = job_scraper._parse_date(date_str)
    assert isinstance(parsed, datetime), "Date should be parsed"
    print("✓ Date parsing works")
    
    print("✓ Job Scraper tests passed\n")


def test_job_matcher():
    """Test job matcher logic"""
    print("Testing Job Matcher...")
    from api.job_matcher import job_matcher
    
    # Create mock objects
    class MockUser:
        skills = ["python", "django"]
        preferred_job_titles = ["Python Developer"]
        preferred_locations = ["Remote"]
        cv_text = "I have 5 years of Python and Django experience"
    
    class MockJob:
        id = 1
        title = "Python Developer"
        location = "Remote"
        description = "Looking for Python and Django developer"
        required_skills = ["python", "django"]
    
    user = MockUser()
    job = MockJob()
    
    score = job_matcher.calculate_match_score(user, job)
    assert score > 0, "Match score should be positive"
    assert score <= 100, "Match score should be <= 100"
    print(f"✓ Match score calculated: {score:.2f}%")
    
    print("✓ Job Matcher tests passed\n")


def test_email_service():
    """Test email service structure"""
    print("Testing Email Service...")
    from api.email_service import email_service
    
    # Just verify the service initializes
    assert email_service is not None
    assert hasattr(email_service, 'send_job_notification')
    assert hasattr(email_service, 'send_test_email')
    print("✓ Email service initialized correctly")
    
    print("✓ Email Service tests passed\n")


def main():
    print("="*60)
    print("Job Notification Feature - Standalone Tests")
    print("="*60)
    print()
    
    try:
        test_job_scraper()
        test_job_matcher()
        test_email_service()
        
        print("="*60)
        print("✅ All tests passed!")
        print("="*60)
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
