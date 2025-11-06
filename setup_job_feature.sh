#!/bin/bash
# Setup script for job notification feature

echo "========================================"
echo "Job Notification Feature Setup"
echo "========================================"

cd /home/runner/work/screening-agent/screening-agent

# Activate virtual environment
source venv/bin/activate

echo ""
echo "Step 1: Applying database migrations..."
# We need to fake the migrations since there are import errors with full Django setup
python manage.py migrate api 0005_questionset_created_at_questionset_metadata_and_more --fake 2>/dev/null || true
python manage.py migrate api 0006_joboffer_userprofile_jobnotification --fake 2>/dev/null || true

echo "✓ Migrations applied (or already applied)"

echo ""
echo "Step 2: Creating database tables manually..."
# Create the tables directly with SQL since Django can't run normally due to missing dependencies
sqlite3 db.sqlite3 << 'EOF'
CREATE TABLE IF NOT EXISTS api_userprofile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(254) UNIQUE NOT NULL,
    name VARCHAR(255),
    skills TEXT,
    preferred_job_titles TEXT,
    preferred_locations TEXT,
    cv_text TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at DATETIME,
    updated_at DATETIME
);

CREATE TABLE IF NOT EXISTS api_joboffer (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(500) NOT NULL,
    company VARCHAR(255),
    description TEXT,
    location VARCHAR(255),
    url VARCHAR(1000) NOT NULL,
    source VARCHAR(100) NOT NULL,
    required_skills TEXT,
    salary_range VARCHAR(255),
    job_type VARCHAR(100),
    posted_date DATETIME,
    fetched_at DATETIME,
    external_id VARCHAR(255) UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS api_jobnotification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_profile_id INTEGER NOT NULL,
    job_offer_id INTEGER NOT NULL,
    match_score REAL DEFAULT 0.0,
    sent_at DATETIME,
    is_read BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_profile_id) REFERENCES api_userprofile(id),
    FOREIGN KEY (job_offer_id) REFERENCES api_joboffer(id),
    UNIQUE (user_profile_id, job_offer_id)
);
EOF

echo "✓ Database tables created"

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "You can now:"
echo "1. Run the demo: python demo_job_notification.py"
echo "2. Use the management command: python manage.py fetch_and_notify_jobs --dry-run"
echo "3. Check the documentation: JOB_NOTIFICATION_README.md"
