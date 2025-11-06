# Testing Guide for Job Notification Feature

This guide explains how to test the job notification feature step by step.

## Quick Test (5 minutes)

The fastest way to verify the feature works:

### 1. Run Setup Script
```bash
cd /path/to/screening-agent
./setup_job_feature.sh
```

This creates the database tables needed for the feature.

### 2. Run Verification Script
```bash
python verify_job_feature.py
```

**What it does:**
- Creates a test user profile
- Creates mock job offers
- Tests the matching algorithm
- Tests notification creation
- Verifies email service is configured

**Expected output:**
```
✅ ALL TESTS PASSED!

Feature verification summary:
  ✓ User profiles: Working
  ✓ Job storage: Working
  ✓ Job matching: Working (scored 2 matches)
  ✓ Notifications: Working (2 created)
  ✓ Email generation: Working
```

---

## Interactive Demo (10 minutes)

For a more detailed walkthrough:

```bash
python demo_job_notification.py
```

**What it does:**
1. Creates a demo user profile
2. Attempts to fetch real jobs from Remotive API
3. Matches jobs against the profile
4. Generates email notifications (printed to console)
5. Shows notification history

**Note:** Job fetching requires internet access. In sandboxed environments, this may not work, but the rest of the workflow will still demonstrate.

---

## Manual Testing via Django Admin (15 minutes)

### Step 1: Start Django Server
```bash
# If you have all dependencies installed:
python manage.py runserver

# If missing dependencies, you may need to install them first:
pip install -r requirements.txt
```

### Step 2: Access Admin Interface
1. Open browser: http://localhost:8000/admin/
2. Login with admin credentials (create superuser if needed):
   ```bash
   python manage.py createsuperuser
   ```

### Step 3: Create User Profile
1. Click "User Profiles" → "Add User Profile"
2. Fill in:
   - Email: your-email@example.com
   - Name: Your Name
   - Skills: `["python", "django", "react"]` (JSON format)
   - Preferred job titles: `["Software Engineer", "Python Developer"]`
   - Preferred locations: `["Remote"]`
   - Is active: ✓ (checked)
3. Save

### Step 4: Run Job Fetch Command
```bash
# Dry run to see what would happen without sending emails:
python manage.py fetch_and_notify_jobs --dry-run

# Actual run (sends emails to console by default):
python manage.py fetch_and_notify_jobs
```

### Step 5: Check Results in Admin
1. Go back to admin interface
2. Check "Job offers" - should see fetched jobs
3. Check "Job notifications" - should see notifications created for your profile

---

## Testing with Real Email (Production Testing)

### Step 1: Configure Email Settings

Create a `.env` file in the project root:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**For Gmail:**
1. Go to Google Account Settings > Security
2. Enable 2-Factor Authentication
3. Generate an "App Password"
4. Use the app password in EMAIL_HOST_PASSWORD

### Step 2: Update settings.py (if not using .env)

Edit `core/settings.py`:
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'
```

### Step 3: Send Test Email
```bash
# Via Python:
python -c "
import os, sys, django
sys.path.insert(0, '.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from api.email_service import email_service
email_service.send_test_email('your-email@example.com')
"
```

Or use the API:
```bash
curl -X POST http://localhost:8000/api/email/test/ \
  -H "Content-Type: application/json" \
  -d '{"email": "your-email@example.com"}'
```

### Step 4: Run Full Workflow
```bash
python manage.py fetch_and_notify_jobs
```

Check your email inbox for notifications!

---

## Testing via API (Development Testing)

### Step 1: Start Django Server
```bash
python manage.py runserver
```

### Step 2: Create User Profile via API
```bash
curl -X POST http://localhost:8000/api/user-profiles/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User",
    "skills": ["python", "django", "javascript"],
    "preferred_job_titles": ["Software Engineer"],
    "preferred_locations": ["Remote"],
    "is_active": true
  }'
```

### Step 3: Manually Search Jobs
```bash
curl -X POST http://localhost:8000/api/jobs/search/ \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["python", "django"],
    "location": "Remote",
    "limit": 20
  }'
```

### Step 4: Trigger Manual Matching
```bash
curl -X POST http://localhost:8000/api/user-profiles/test@example.com/trigger-matching/ \
  -H "Content-Type: application/json" \
  -d '{
    "min_score": 40.0,
    "send_email": false
  }'
```

This returns matching jobs without sending email.

### Step 5: Get User Notifications
```bash
curl http://localhost:8000/api/user-profiles/test@example.com/notifications/
```

---

## Troubleshooting

### "No module named 'whisper'" or similar errors
The main application has many dependencies. The job notification feature works independently. If you get import errors:
- Use the verification script instead: `python verify_job_feature.py`
- Or install only the required packages: `pip install Django djangorestframework django-cors-headers requests beautifulsoup4 rapidfuzz django-environ`

### No jobs fetched
- Check internet connectivity
- Remotive API may be rate-limited
- Try with `--limit 10` for fewer jobs
- Network restrictions in some environments may block external APIs

### Emails not sending
- Check email configuration in `core/settings.py`
- Verify SMTP credentials
- Test with console backend first: `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`
- For Gmail, ensure you're using an App Password, not regular password

### Database errors
- Run `./setup_job_feature.sh` to create tables
- Or manually run: `python manage.py migrate`

---

## Expected Results Summary

**Verification Script:** ✅ All tests passed message

**Demo Script:** Shows job fetching, matching, and email generation

**Admin Interface:** 
- User profiles visible and editable
- Job offers stored after fetch
- Job notifications recorded

**Email:** 
- Console: Email printed to terminal
- SMTP: Email received in inbox with job details and match scores

**API Testing:**
- Profile creation: Returns created profile JSON
- Job search: Returns list of jobs
- Trigger matching: Returns matching jobs with scores
- Get notifications: Returns notification history

---

## Performance Testing

To test with larger datasets:

```bash
# Fetch more jobs
python manage.py fetch_and_notify_jobs --limit 100

# Create multiple user profiles
# Then run fetch to see multiple users getting notifications
python manage.py fetch_and_notify_jobs
```

---

## Scheduling (Production)

Once tested, schedule automatic execution:

### Linux/Mac (cron):
```bash
crontab -e
# Add line to run daily at 9 AM:
0 9 * * * cd /path/to/screening-agent && /path/to/venv/bin/python manage.py fetch_and_notify_jobs
```

### Windows (Task Scheduler):
Create `fetch_jobs.bat`:
```batch
cd C:\path\to\screening-agent
call venv\Scripts\activate.bat
python manage.py fetch_and_notify_jobs
```

Then create a scheduled task to run this batch file.

---

## Success Criteria

The feature is working correctly if:
- ✅ User profiles can be created and stored
- ✅ Jobs are fetched from Remotive API
- ✅ Matching algorithm scores jobs (0-100 scale)
- ✅ High-scoring jobs (>40%) are identified
- ✅ Emails are generated with job details
- ✅ Notifications are recorded in database
- ✅ Duplicate notifications are prevented

---

For more details, see:
- `JOB_NOTIFICATION_README.md` - Complete setup guide
- `IMPLEMENTATION_SUMMARY.md` - Technical details
