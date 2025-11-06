# Job Offer Notification Feature

This feature allows the screening agent to automatically fetch job offers from free sources and send email notifications to users when jobs match their profile.

## Features

- **User Profile Management**: Store user preferences including skills, preferred job titles, and locations
- **Automatic Job Fetching**: Fetch jobs from multiple free sources (Remotive API, GitHub)
- **Intelligent Matching**: Score jobs based on how well they match user profiles
- **Email Notifications**: Automatically send email notifications with matching jobs
- **API Endpoints**: RESTful API for managing profiles and viewing notifications

## Setup

### 1. Install Dependencies

The required packages are already in `requirements.txt`, but here are the key ones for this feature:
- Django
- djangorestframework
- django-cors-headers
- requests
- beautifulsoup4
- rapidfuzz

```bash
pip install Django djangorestframework django-cors-headers requests beautifulsoup4 rapidfuzz django-environ
```

### 2. Run Migrations

```bash
python manage.py migrate
```

### 3. Configure Email Settings

The feature supports two email backends:

#### Option A: Console Backend (for development/testing)
This is the default. Emails will be printed to the console.

No configuration needed - it's already set in `core/settings.py`.

#### Option B: SMTP Backend (for production)

For Gmail SMTP, create a `.env` file in the project root:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

**Note**: For Gmail, you need to:
1. Enable 2-factor authentication
2. Generate an "App Password" (Google Account Settings > Security > App Passwords)
3. Use the app password in `EMAIL_HOST_PASSWORD`

For other SMTP providers, adjust the settings accordingly.

## Usage

### 1. Create User Profiles

#### Via API:

```bash
curl -X POST http://localhost:8000/api/user-profiles/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "developer@example.com",
    "name": "John Doe",
    "skills": ["python", "django", "javascript", "react"],
    "preferred_job_titles": ["Software Engineer", "Python Developer"],
    "preferred_locations": ["Remote", "New York"],
    "is_active": true
  }'
```

#### Via Django Admin:

1. Run the development server: `python manage.py runserver`
2. Go to http://localhost:8000/admin/
3. Navigate to User Profiles and add profiles manually

### 2. Fetch and Notify Jobs

Run the management command to fetch jobs and send notifications:

```bash
# Regular run
python manage.py fetch_and_notify_jobs

# Dry run (preview without sending emails)
python manage.py fetch_and_notify_jobs --dry-run

# Customize parameters
python manage.py fetch_and_notify_jobs --limit 100 --min-score 50
```

**Command Options:**
- `--dry-run`: Preview matches without sending emails
- `--limit N`: Maximum number of jobs to fetch (default: 50)
- `--min-score N`: Minimum match score to notify (default: 40.0)

### 3. Schedule Automatic Job Fetching

You can schedule the command to run periodically using:

#### Option A: Cron (Linux/Mac)

```bash
# Edit crontab
crontab -e

# Add this line to run every day at 9 AM
0 9 * * * cd /path/to/screening-agent && /path/to/venv/bin/python manage.py fetch_and_notify_jobs
```

#### Option B: Windows Task Scheduler

Create a batch file `fetch_jobs.bat`:
```batch
cd C:\path\to\screening-agent
call venv\Scripts\activate.bat
python manage.py fetch_and_notify_jobs
```

Then schedule it using Task Scheduler.

## API Endpoints

### User Profile Management

**Create Profile:**
```
POST /api/user-profiles/
```

**Get Profile:**
```
GET /api/user-profiles/<email>/
```

**Update Profile:**
```
PUT /api/user-profiles/<email>/
```

**Delete Profile:**
```
DELETE /api/user-profiles/<email>/
```

### Job Search and Notifications

**Manual Job Search:**
```
POST /api/jobs/search/
Body: {"keywords": ["python", "django"], "location": "Remote", "limit": 20}
```

**Get Recent Jobs:**
```
GET /api/jobs/recent/?limit=50
```

**Get User Notifications:**
```
GET /api/user-profiles/<email>/notifications/
```

**Trigger Manual Job Matching:**
```
POST /api/user-profiles/<email>/trigger-matching/
Body: {"min_score": 40.0, "send_email": true}
```

**Mark Notification as Read:**
```
POST /api/notifications/<notification_id>/mark-read/
```

**Send Test Email:**
```
POST /api/email/test/
Body: {"email": "test@example.com"}
```

## Job Sources

The scraper fetches jobs from the following free sources:

### 1. Remotive (Primary)
- API: https://remotive.com/api/remote-jobs
- No API key required
- Specializes in remote jobs
- High quality listings

### 2. GitHub (Secondary)
- Searches GitHub repositories for hiring/jobs content
- Uses public GitHub API
- No API key required for basic usage

## Matching Algorithm

Jobs are scored based on:
- **Skills Match (50% weight)**: Overlap between user skills and job requirements
- **Job Title Match (20% weight)**: Fuzzy matching of preferred job titles
- **Location Match (15% weight)**: Match with preferred locations (Remote always matches)
- **CV Text Match (15% weight)**: Keyword overlap between CV and job description

Score ranges from 0-100, with configurable minimum threshold for notifications.

## Testing

Run the test suite:

```bash
python manage.py test api.tests
```

Test individual components:

```bash
# Test job scraper
python manage.py test api.tests.JobScraperTest

# Test job matching
python manage.py test api.tests.JobMatchingServiceTest

# Test models
python manage.py test api.tests.UserProfileModelTest
```

## Troubleshooting

### "No module named 'whisper'" or similar errors
The main application has many dependencies. If you're only testing the job notification feature, you can skip installing all dependencies. The feature works independently.

### Emails not sending
- Check your email configuration in `.env` or `core/settings.py`
- For Gmail, ensure you're using an App Password, not your regular password
- Test with the console backend first: `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`

### No jobs found
- The job scraper depends on external APIs which may have rate limits
- Try running with `--dry-run` first to see what would be fetched
- Check your internet connection

### Duplicate job notifications
The system tracks which jobs have been sent to each user and won't send duplicates. If you want to re-send, you need to delete the JobNotification records from the database.

## Future Enhancements

Potential improvements:
- Add more job sources (Indeed, LinkedIn, etc.)
- Implement authentication/authorization for API endpoints
- Add web interface for user profile management
- Support for job alerts via SMS/push notifications
- Machine learning for improved matching
- Save job search history and analytics

## Support

For issues or questions about this feature, please open an issue on the GitHub repository.
