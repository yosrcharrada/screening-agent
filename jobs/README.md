# Jobs App - Automated Job Matching & Notifications

This Django app provides automated job fetching, intelligent matching, and email notifications to help users find relevant job opportunities.

## Features

- **Multi-Source Job Fetching**: Automatically fetches jobs from Remotive and RemoteOK APIs
- **Intelligent Matching**: Uses sentence-transformer embeddings for semantic matching
- **Customizable Preferences**: Users can set location, remote preferences, keywords, and score thresholds
- **Email Notifications**: Sends digest emails with top matches
- **Deduplication**: Prevents duplicate jobs and notifications
- **REST API**: Full API for managing preferences
- **Admin Interface**: Django admin for managing jobs and preferences

## Architecture

### Models

1. **JobPosting**: Stores job listings from various sources
   - Deduplication via unique hash and source+external_id
   - Tracks publication dates and source metadata
   
2. **UserJobPreference**: User-specific job search preferences
   - Keywords, locations, remote-only flag
   - Matching threshold and email settings
   
3. **JobDispatchLog**: Tracks which jobs have been sent to which users
   - Prevents duplicate notifications
   - Records match scores

### Services

1. **Fetcher** (`services/fetcher.py`):
   - Fetches jobs from Remotive and RemoteOK
   - Implements retry logic with exponential backoff
   - Handles idempotent job creation

2. **Matcher** (`services/matcher.py`):
   - Computes embeddings using sentence-transformers
   - Calculates match scores with weighted factors:
     - 60% semantic similarity (embeddings)
     - 30% keyword overlap
     - 10% recency
   - Filters by location and remote preferences
   - Sends email digests

## Setup

### 1. Add to INSTALLED_APPS

Edit `core/settings.py`:

```python
INSTALLED_APPS = [
    # ... other apps
    'jobs',
]
```

### 2. Include URLs

Edit `core/urls.py`:

```python
urlpatterns = [
    # ... other patterns
    path('api/jobs/', include('jobs.urls')),
]
```

### 3. Run Migrations

```bash
python manage.py makemigrations jobs
python manage.py migrate jobs
```

### 4. Configure Environment Variables

Optional settings in `core/settings.py` or `.env`:

```python
# Job fetching configuration
JOB_SOURCES = ['remotive', 'remoteok']  # Sources to fetch from
JOB_MAX_PER_USER = 10                   # Max jobs per email digest
JOB_MIN_SCORE_DEFAULT = 0.6             # Default minimum match score
JOB_EMAIL_ENABLED = True                # Enable/disable email sending
```

### 5. Install Dependencies

sentence-transformers is required for embeddings:

```bash
pip install sentence-transformers
```

## Usage

### Running the Management Command

Fetch jobs and send notifications:

```bash
# Full run (fetch + match + notify)
python manage.py fetch_and_match_jobs

# Dry run (fetch only, no emails)
python manage.py fetch_and_match_jobs --dry-run
```

### Scheduling

#### Linux/Mac (cron)

```bash
crontab -e
```

Add line to run daily at 9 AM:

```
0 9 * * * cd /path/to/screening-agent && /path/to/venv/bin/python manage.py fetch_and_match_jobs >> /var/log/jobs.log 2>&1
```

#### Windows (Task Scheduler)

Create `run_jobs.bat`:

```batch
cd C:\path\to\screening-agent
call venv\Scripts\activate.bat
python manage.py fetch_and_match_jobs
```

Schedule this batch file to run daily.

## API Endpoints

All endpoints require authentication.

### Get Preferences

```
GET /api/jobs/preferences/
```

Returns or creates job preferences for the authenticated user.

**Response:**
```json
{
  "preference": {
    "desired_locations": "Remote,New York",
    "remote_only": false,
    "keywords": "python,django",
    "min_score_threshold": 0.6,
    "email_enabled": true,
    "max_jobs_per_email": 10
  },
  "created": false
}
```

### Update Preferences

```
PATCH /api/jobs/preferences/update/
```

Update user preferences (partial updates supported).

**Request Body:**
```json
{
  "keywords": "react,typescript",
  "remote_only": true,
  "min_score_threshold": 0.7
}
```

### Trigger Manual Fetch (Development Only)

```
POST /api/jobs/trigger/
```

Manually trigger job fetching and matching. Only available in DEBUG mode.

**Response:**
```json
{
  "success": true,
  "fetched": {
    "total": 25,
    "by_source": {
      "remotive": 15,
      "remoteok": 10
    }
  },
  "matched": {
    "users_processed": 3,
    "jobs_matched": 12,
    "emails_sent": 3
  }
}
```

## Matching Strategy

Jobs are matched to users using a multi-factor approach:

### 1. Embedding Similarity (60% weight)

- User profile created from CV text or keywords
- Job profile from title + description
- Cosine similarity computed using sentence-transformers

### 2. Keyword Overlap (30% weight)

- Each matching keyword adds 0.05 boost
- Maximum boost: 0.2 (4 keywords)

### 3. Recency Factor (10% weight)

- Recent jobs (0-30 days) get higher scores
- Formula: `1 - min(age_in_days / 30, 1.0)`

### Final Score

```
score = 0.6 * cosine_similarity + 0.3 * keyword_boost + 0.1 * recency_factor
```

Jobs are sent if `score >= user.min_score_threshold`.

## Testing

### Run All Tests

```bash
python manage.py test jobs
```

### Run Specific Test Files

```bash
python manage.py test jobs.tests.test_fetcher
python manage.py test jobs.tests.test_matcher
python manage.py test jobs.tests.test_api
```

### Coverage

Tests cover:
- Job fetching with mocked API responses
- Deduplication logic
- Matching algorithm components
- API authentication and validation
- Email sending (with mocked backend)

## Admin Interface

Access at `/admin/`:

1. **Job Postings**: View and manage fetched jobs
   - Filter by source, remote status, dates
   - Search by title, company, location
   
2. **User Job Preferences**: View and edit user preferences
   - Filter by settings
   - Search by username or email
   
3. **Job Dispatch Logs**: Track sent notifications
   - View match scores
   - Filter by date and user

## Troubleshooting

### No jobs fetched

- Check internet connectivity
- Verify API endpoints are accessible
- Check logs for rate limiting or API errors

### Emails not sending

- Verify EMAIL_* settings in Django settings
- Check that users have `email_enabled=True` in preferences
- Test with console backend: `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`

### Low match scores

- Ensure users have CV text or keywords set
- Lower `min_score_threshold` in preferences
- Check that job descriptions contain relevant keywords

### Duplicate notifications

- JobDispatchLog should prevent duplicates
- Verify unique_together constraint is working
- Check for database migration issues

## Configuration

### Default Settings

Add to `core/settings.py`:

```python
# Jobs app configuration
JOB_SOURCES = os.environ.get('JOB_SOURCES', 'remotive,remoteok').split(',')
JOB_MAX_PER_USER = int(os.environ.get('JOB_MAX_PER_USER', 10))
JOB_MIN_SCORE_DEFAULT = float(os.environ.get('JOB_MIN_SCORE_DEFAULT', 0.6))
JOB_EMAIL_ENABLED = os.environ.get('JOB_EMAIL_ENABLED', 'True').lower() == 'true'
```

### Email Settings

Ensure email is configured:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@example.com')
```

## Development

### Adding New Job Sources

1. Create a new fetcher class in `services/fetcher.py`:

```python
class NewSourceFetcher(JobFetcher):
    API_URL = "https://api.newsource.com/jobs"
    
    def fetch(self) -> int:
        # Implementation
        pass
```

2. Add to `fetch_all_sources()`:

```python
fetcher = NewSourceFetcher()
results['newsource'] = fetcher.fetch()
```

### Customizing Match Algorithm

Edit `services/matcher.py` and adjust weights in `match_job_to_user()`:

```python
final_score = (
    0.5 * cosine_sim +       # Reduce embedding weight
    0.4 * keyword_boost +    # Increase keyword weight
    0.1 * recency_factor
)
```

## Performance Considerations

- **Embeddings**: Model loaded lazily, cached in memory
- **Batch Processing**: Jobs fetched in batches
- **Database**: Indexed fields for fast lookups
- **Email**: Sent in batches to avoid rate limits

## Security

- API endpoints require authentication
- Manual trigger endpoint restricted to DEBUG mode
- User data isolated per user
- No sensitive data in logs

## Future Enhancements

- Cache embeddings for large CV texts
- Add HTML email templates
- Support for more job sources
- Advanced filtering (salary, company size, etc.)
- User feedback on match quality
- A/B testing different match algorithms
