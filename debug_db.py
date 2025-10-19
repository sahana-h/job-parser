"""Debug script to see what's in the database."""

from database import DatabaseManager
from gmail_client import GmailClient
import json

def show_database_contents():
    """Show all data in the database."""
    db = DatabaseManager()
    
    print("🔍 Database Contents:")
    print("=" * 80)
    
    applications = db.get_all_applications()
    
    if not applications:
        print("No applications in database.")
        return
    
    for i, app in enumerate(applications, 1):
        print(f"\n{i}. Application ID: {app.id}")
        print(f"   Company: {app.company_name}")
        print(f"   Job Title: {app.job_title}")
        print(f"   Platform: {app.platform}")
        print(f"   Status: {app.status}")
        print(f"   Date Applied: {app.date_applied}")
        print(f"   Email Date: {app.email_date}")
        print(f"   Email Subject: {app.email_subject}")
        print(f"   Gmail Message ID: {app.gmail_message_id}")
        print(f"   Created: {app.created_at}")
        print(f"   Updated: {app.updated_at}")
        print("-" * 40)

def show_raw_email_example():
    """Show a raw email example to understand the data structure."""
    print("\n🔍 Raw Email Example:")
    print("=" * 80)
    
    gmail = GmailClient()
    
    # Get a recent email
    emails = gmail.get_recent_job_emails(7)
    
    if emails:
        email = emails[0]
        print(f"Subject: {email.get('subject')}")
        print(f"From: {email.get('from')}")
        print(f"Date: {email.get('date')}")
        print(f"Body (first 500 chars): {email.get('body', '')[:500]}...")
        print(f"Message ID: {email.get('message_id')}")

if __name__ == "__main__":
    show_database_contents()
    show_raw_email_example()
