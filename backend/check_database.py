#!/usr/bin/env python3
"""
Database connection and table creation check script
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import SessionLocal, Session, Score, Evidence, Report, engine
from sqlalchemy import inspect, text

def check_database():
    print("🔍 Checking database setup...")
    
    # Check if database file exists
    db_file = "interview_platform.db"
    if os.path.exists(db_file):
        print(f"✅ Database file '{db_file}' exists")
    else:
        print(f"❌ Database file '{db_file}' not found")
        return False
    
    # Test database connection - FIXED for SQLAlchemy 2.0
    try:
        db = SessionLocal()
        # Use text() for raw SQL in SQLAlchemy 2.0
        result = db.execute(text("SELECT 1")).scalar()
        if result == 1:
            print("✅ Database connection successful")
        else:
            print("❌ Database connection test failed")
            return False
        db.close()
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False
    
    # Check if tables exist
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        expected_tables = {"sessions", "scores", "evidence", "reports"}
        
        print(f"📊 Found tables: {tables}")
        
        for table in expected_tables:
            if table in tables:
                print(f"✅ Table '{table}' exists")
            else:
                print(f"❌ Table '{table}' missing")
                
        return all(table in tables for table in expected_tables)
        
    except Exception as e:
        print(f"❌ Error checking tables: {e}")
        return False

def test_crud_operations():
    print("\n🧪 Testing CRUD operations...")
    
    try:
        db = SessionLocal()
        
        # Create a test session
        test_session = Session(
            session_id="test_session_123",
            status="active"
        )
        db.add(test_session)
        db.commit()
        db.refresh(test_session)
        print("✅ Create operation successful")
        
        # Read the session
        session_from_db = db.query(Session).filter(Session.session_id == "test_session_123").first()
        if session_from_db:
            print("✅ Read operation successful")
        else:
            print("❌ Read operation failed")
            return False
        
        # Update the session
        session_from_db.status = "completed"
        db.commit()
        print("✅ Update operation successful")
        
        # Delete the session
        db.delete(session_from_db)
        db.commit()
        print("✅ Delete operation successful")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ CRUD operations failed: {e}")
        db.rollback()
        return False

if __name__ == "__main__":
    print("🚀 Starting database verification...\n")
    
    db_check = check_database()
    crud_check = test_crud_operations()
    
    print("\n" + "="*50)
    if db_check and crud_check:
        print("🎉 ALL DATABASE CHECKS PASSED!")
        sys.exit(0)
    else:
        print("💥 SOME DATABASE CHECKS FAILED!")
        sys.exit(1)