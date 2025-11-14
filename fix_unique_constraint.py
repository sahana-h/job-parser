"""Migration script to fix the gmail_message_id unique constraint.

This removes the old global unique constraint and adds a composite unique constraint
on (user_id, gmail_message_id) so that message IDs are unique per user.
"""

import sqlite3
import os
from config import DATABASE_URL

def migrate_database():
    """Fix the unique constraint on gmail_message_id."""
    
    # Only works with SQLite for now
    if not DATABASE_URL.startswith('sqlite'):
        print("⚠️  This migration only works with SQLite. For PostgreSQL, run:")
        print("   ALTER TABLE job_applications DROP CONSTRAINT IF EXISTS job_applications_gmail_message_id_key;")
        print("   ALTER TABLE job_applications ADD CONSTRAINT uq_user_message UNIQUE (user_id, gmail_message_id);")
        return
    
    # Extract SQLite database path
    if DATABASE_URL.startswith('sqlite:///'):
        db_path = DATABASE_URL.replace('sqlite:///', '')
    else:
        db_path = 'job_applications.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found: {db_path}")
        return
    
    print(f"Migrating database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if the old unique constraint exists
        cursor.execute("""
            SELECT sql FROM sqlite_master 
            WHERE type='table' AND name='job_applications'
        """)
        table_sql = cursor.fetchone()[0]
        
        if "UNIQUE (gmail_message_id)" in table_sql:
            print("Found old unique constraint on gmail_message_id")
            print("Removing old constraint and adding composite constraint...")
            
            # SQLite doesn't support DROP CONSTRAINT directly, so we need to recreate the table
            # Step 1: Create new table with correct schema
            cursor.execute("""
                CREATE TABLE job_applications_new (
                    id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    company_name VARCHAR(255) NOT NULL,
                    job_title VARCHAR(255) NOT NULL,
                    platform VARCHAR(100),
                    status VARCHAR(100),
                    date_applied DATETIME NOT NULL,
                    email_subject VARCHAR(500),
                    email_body TEXT,
                    email_date DATETIME NOT NULL,
                    gmail_message_id VARCHAR(255) NOT NULL,
                    created_at DATETIME,
                    updated_at DATETIME,
                    PRIMARY KEY (id),
                    FOREIGN KEY(user_id) REFERENCES users (id),
                    UNIQUE (user_id, gmail_message_id)
                )
            """)
            
            # Step 2: Copy data
            cursor.execute("""
                INSERT INTO job_applications_new 
                SELECT * FROM job_applications
            """)
            
            # Step 3: Drop old table
            cursor.execute("DROP TABLE job_applications")
            
            # Step 4: Rename new table
            cursor.execute("ALTER TABLE job_applications_new RENAME TO job_applications")
            
            # Step 5: Recreate indexes if any
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS ix_job_applications_user_id 
                ON job_applications (user_id)
            """)
            
            conn.commit()
            print("✅ Migration complete! Unique constraint is now per-user.")
        else:
            print("✅ Database already has the correct constraint (or no constraint found)")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error during migration: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_database()

