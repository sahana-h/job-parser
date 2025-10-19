"""Check for duplicate applications in the database."""

from database import DatabaseManager, JobApplication
from gmail_client import GmailClient
from email_parser import EmailParser

def check_duplicates():
    """Check what's causing the duplicate detection."""
    print("🔍 CHECKING DUPLICATE DETECTION:")
    print("=" * 80)
    
    db = DatabaseManager()
    gmail = GmailClient()
    parser = EmailParser()
    
    # Get recent emails
    emails = gmail.get_recent_job_emails(7)
    
    print(f"Found {len(emails)} emails to check")
    print("-" * 80)
    
    for i, email in enumerate(emails[:5], 1):
        print(f"\n📧 Email {i}:")
        print(f"Subject: {email.get('subject')}")
        print(f"Message ID: {email.get('message_id')}")
        
        # Check if this message ID exists in database
        existing = db.session.query(JobApplication).filter_by(
            gmail_message_id=email.get('message_id')
        ).first()
        
        if existing:
            print(f"✅ FOUND in database - ID: {existing.id}, Company: {existing.company_name}")
        else:
            print(f"❌ NOT in database - would be added")
            
            # Try to parse it
            job_data = parser.parse_job_email(email)
            if job_data:
                print(f"   Parsed data: {job_data['company_name']} - {job_data.get('job_title', 'No title')}")
            else:
                print(f"   Failed to parse")
        
        print("-" * 40)
    
    # Show all message IDs in database
    print(f"\n📊 All Message IDs in Database:")
    applications = db.get_all_applications()
    for app in applications:
        print(f"   ID {app.id}: {app.gmail_message_id} - {app.company_name}")
    
    db.close()

if __name__ == "__main__":
    check_duplicates()
