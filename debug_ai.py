"""Debug script to see what AI is receiving and responding."""

from email_parser import EmailParser
from gmail_client import GmailClient
import json

def debug_ai_extraction():
    """Debug AI extraction process."""
    print("🤖 Debugging AI Extraction:")
    print("=" * 80)
    
    gmail = GmailClient()
    parser = EmailParser()
    
    # Get a recent email
    emails = gmail.get_recent_job_emails(7)
    
    if not emails:
        print("No emails found.")
        return
    
    # Test with the first email
    email = emails[0]
    print(f"📧 Testing with email:")
    print(f"Subject: {email.get('subject')}")
    print(f"From: {email.get('from')}")
    print(f"Date: {email.get('date')}")
    print(f"Body: {email.get('body', '')[:300]}...")
    print("\n" + "="*80)
    
    # Show what we send to AI
    email_content = parser._prepare_email_content(email)
    print(f"📤 Content sent to AI:")
    print(email_content)
    print("\n" + "="*80)
    
    # Show AI response
    try:
        response = parser.model.generate_content(parser._create_extraction_prompt(email_content))
        print(f"🤖 AI Response:")
        print(response.text)
        print("\n" + "="*80)
        
        # Try to parse the response
        job_data = parser.parse_job_email(email)
        if job_data:
            print(f"✅ Parsed successfully:")
            print(json.dumps(job_data, indent=2, default=str))
        else:
            print("❌ Failed to parse AI response")
            
    except Exception as e:
        print(f"❌ AI Error: {e}")

if __name__ == "__main__":
    debug_ai_extraction()
