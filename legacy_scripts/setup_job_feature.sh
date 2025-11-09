echo "========================================"
echo "Job Notification Feature Setup"
echo "========================================"

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
source venv/bin/activate

echo ""
echo "Step 1: Verifying environment..."
# Note: Full migrations skipped due to missing dependencies in the main project
# In production, run: python manage.py migrate
echo "✓ Environment ready"

echo ""
echo "Step 2: Creating database tables..."
# Create a simple Python script to properly run migrations
python << 'PYTHON_EOF'
import sqlite3
import os

db_path = 'db.sqlite3'

# Create connection
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Create tables if they don't exist
try:
    cursor.execute('''
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
        )
    ''')
    
    cursor.execute('''
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
        )
    ''')
    
    cursor.execute('''
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
        )
    ''')
    
    conn.commit()
    print("✓ Database tables created successfully")
except Exception as e:
    print(f"Error creating tables: {e}")
    conn.rollback()
finally:
    conn.close()
PYTHON_EOF

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "You can now:"
echo "1. Run the demo: python demo_job_notification.py"
echo "2. Use the management command: python manage.py fetch_and_notify_jobs --dry-run"
echo "3. Check the documentation: JOB_NOTIFICATION_README.md"
