"""Script to clean up duplicate applications in the database."""

from database import DatabaseManager, JobApplication
from datetime import datetime

def cleanup_duplicates():
    """Remove duplicate applications from the database."""
    db = DatabaseManager()
    
    print("🧹 Cleaning up duplicate applications...")
    
    try:
        # Get all applications
        all_apps = db.session.query(JobApplication).all()
        print(f"Found {len(all_apps)} total applications")
        
        # Group by company name
        company_groups = {}
        for app in all_apps:
            company_key = app.company_name.lower().strip()
            if company_key not in company_groups:
                company_groups[company_key] = []
            company_groups[company_key].append(app)
        
        duplicates_removed = 0
        
        for company, apps in company_groups.items():
            if len(apps) > 1:
                print(f"\n📋 {company.title()}: {len(apps)} applications found")
                
                # Keep the most recent one and remove the rest
                apps.sort(key=lambda x: x.created_at, reverse=True)
                keep_app = apps[0]
                
                print(f"   ✅ Keeping: {keep_app.job_title} (Created: {keep_app.created_at})")
                
                for app in apps[1:]:
                    print(f"   🗑️  Removing: {app.job_title} (Created: {app.created_at})")
                    db.session.delete(app)
                    duplicates_removed += 1
        
        db.session.commit()
        print(f"\n✅ Cleanup complete! Removed {duplicates_removed} duplicate applications")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error during cleanup: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    cleanup_duplicates()
