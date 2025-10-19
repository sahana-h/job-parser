"""Test why emails are failing to parse."""

from gmail_client import GmailClient
from email_parser import EmailParser
import json

def test_failing_emails():
    """Test specific emails that are failing to parse."""
    print("🧪 TESTING FAILING EMAILS:")
    print("=" * 80)
    
    gmail = GmailClient()
    parser = EmailParser()
    
    # Get emails from last 7 days
    emails = gmail.get_recent_job_emails(7)
    
    if not emails:
        print("No emails found.")
        return
    
    # Test the first few emails
    for i, email in enumerate(emails[:5], 1):
        print(f"\n📧 Testing Email {i}:")
        print(f"Subject: {email.get('subject')}")
        print(f"From: {email.get('from')}")
        print(f"Date: {email.get('date')}")
        print(f"Body length: {len(email.get('body', ''))}")
        print(f"Body preview: {email.get('body', '')[:200]}...")
        print("-" * 40)
        
        # Try to parse this email
        try:
            job_data = parser.parse_job_email(email)
            if job_data:
                print(f"✅ SUCCESS: {job_data}")
            else:
                print(f"❌ FAILED: Could not parse job information")
        except Exception as e:
            print(f"❌ ERROR: {e}")
        
        print("=" * 80)

if __name__ == "__main__":
    test_failing_emails()
