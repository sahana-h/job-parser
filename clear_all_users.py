"""Script to delete all users and their associated data from the database."""

from database import DatabaseManager
from config import DATABASE_URL
import sqlite3

def clear_all_users():
    """Delete all users and their job applications using raw SQL to avoid data corruption issues."""
    
    # Use raw SQL to avoid SQLAlchemy trying to parse corrupted date fields
    if DATABASE_URL.startswith('sqlite'):
        # Extract SQLite database path
        if DATABASE_URL.startswith('sqlite:///'):
            db_path = DATABASE_URL.replace('sqlite:///', '')
        else:
            db_path = 'job_applications.db'
        
        print(f"Connecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Count records before deletion
            cursor.execute("SELECT COUNT(*) FROM job_applications")
            app_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            
            print(f"Found {user_count} users and {app_count} job applications")
            
            if app_count > 0:
                print(f"Deleting {app_count} job applications...")
                cursor.execute("DELETE FROM job_applications")
                print(f"✅ Deleted {app_count} job applications")
            
            if user_count > 0:
                print(f"\nDeleting {user_count} users...")
                cursor.execute("DELETE FROM users")
                print(f"✅ Deleted {user_count} users")
            
            conn.commit()
            print(f"\n✅ Successfully cleared database!")
            print("Database is now empty. You can create new test accounts.")
            
        except Exception as e:
            conn.rollback()
            print(f"❌ Error clearing database: {e}")
            raise
        finally:
            conn.close()
    else:
        # For PostgreSQL or other databases, use SQLAlchemy with raw SQL
        db = DatabaseManager()
        try:
            # Use raw SQL execution to avoid ORM parsing issues
            result = db.session.execute("DELETE FROM job_applications")
            app_count = result.rowcount
            
            result = db.session.execute("DELETE FROM users")
            user_count = result.rowcount
            
            db.session.commit()
            print(f"✅ Deleted {user_count} users and {app_count} job applications")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error clearing database: {e}")
            raise
        finally:
            db.close()

if __name__ == '__main__':
    import sys
    
    # Allow skipping confirmation with --yes flag
    if '--yes' in sys.argv or '-y' in sys.argv:
        clear_all_users()
    else:
        print("⚠️  WARNING: This will delete ALL users and their job applications!")
        print("Run with --yes flag to skip confirmation: python3 clear_all_users.py --yes")
        response = input("Are you sure you want to continue? (yes/no): ")
        
        if response.lower() in ['yes', 'y']:
            clear_all_users()
        else:
            print("Cancelled. No changes made.")

