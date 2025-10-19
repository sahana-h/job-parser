"""Show all data in the database with detailed information."""

from database import DatabaseManager
from gmail_client import GmailClient
import json

def show_complete_database():
    """Show all data in the database with full details."""
    db = DatabaseManager()
    
    print("🔍 COMPLETE DATABASE CONTENTS:")
    print("=" * 100)
    
    applications = db.get_all_applications()
    
    if not applications:
        print("❌ No applications in database.")
        return
    
    print(f"📊 Total applications in database: {len(applications)}")
    print("-" * 100)
    
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
        print(f"   Email Body (first 200 chars): {app.email_body[:200] if app.email_body else 'No body'}...")
        print("-" * 100)

def test_email_search():
    """Test what emails are being found by the search."""
    print("\n🔍 TESTING EMAIL SEARCH:")
    print("=" * 100)
    
    gmail = GmailClient()
    
    # Test different time ranges
    for days in [1, 7, 30, 90]:
        print(f"\n📅 Searching last {days} days:")
        emails = gmail.get_recent_job_emails(days)
        print(f"   Found {len(emails)} emails")
        
        if emails:
            for i, email in enumerate(emails[:3], 1):  # Show first 3
                print(f"   {i}. Subject: {email.get('subject', 'No subject')[:50]}...")
                print(f"      From: {email.get('from', 'No from')[:50]}...")
                print(f"      Date: {email.get('date', 'No date')}")
                print(f"      Message ID: {email.get('message_id', 'No ID')[:20]}...")
        
        if days == 7:  # Stop at 7 days to avoid too much output
            break

if __name__ == "__main__":
    show_complete_database()
    test_email_search()
