"""Main application for job application tracker (CLI)."""

import sys
import argparse
import json
from gmail_client import GmailClient
from email_parser import EmailParser
from database import DatabaseManager
from email_classifier import RecruitingEmailClassifier
from token_manager import decrypt_token

def scan_user_emails_cli(user_id, days_back=90):
    """Scan and process emails for a specific user (CLI version)."""
    db = DatabaseManager()
    try:
        user = db.get_user_by_id(user_id)
        
        if not user or not user.gmail_token:
            raise ValueError(f"User {user.email if user else 'unknown'} does not have Gmail connected")
        
        # Decrypt and load token
        encrypted_token = user.gmail_token
        decrypted_token = decrypt_token(encrypted_token)
        if not decrypted_token:
            raise ValueError("Failed to decrypt Gmail token")
        
        token_dict = json.loads(decrypted_token.decode('utf-8'))
        
        # Initialize Gmail client with user's token
        gmail_client = GmailClient(user_id=user_id, token_data=token_dict)
        
        # Initialize parser and classifier
        email_parser = EmailParser()
        recruiting_classifier = RecruitingEmailClassifier()
        
        # Clean up old applications first
        db.cleanup_old_applications(user_id, 90)
        
        # Get recent job emails
        emails = gmail_client.get_recent_job_emails(days_back)
        print(f"Found {len(emails)} potential job emails")
        
        processed_count = 0
        new_applications = 0
        updated_applications = 0
        
        for email in emails:
            subject = email.get("subject", "No subject")
            print(f"\n📧 Processing email: {subject[:60]}")
            
            # 🧠 Step 1: Use AI to decide if this email is job-related
            try:
                if not recruiting_classifier.is_job_related(email):
                    print(f"🚫 Skipping non-recruiting email: {subject}")
                    continue
            except Exception as e:
                print(f"⚠️ Error during AI classification: {e}")
                continue
            
            # 🤖 Step 2: Parse the recruiting email to extract structured info
            job_data = email_parser.parse_job_email(email)
            if not job_data:
                print("❌ Could not parse job information from email.")
                continue
            
            # 💾 Step 3: Store or update in database
            try:
                result = db.add_job_application(job_data, user_id)
                if result:
                    if "Updated existing application" in str(result):
                        updated_applications += 1
                    else:
                        new_applications += 1
                    print(f"✅ Added: {job_data.get('company_name', 'Unknown')} - {job_data.get('job_title', 'Unknown')}")
                else:
                    print(f"ℹ️ Already exists: {job_data.get('company_name', 'Unknown')} - {job_data.get('job_title', 'Unknown')}")
            except Exception as e:
                print(f"❌ Error adding to database: {e}")
                continue
            
            processed_count += 1
        
        print(f"\n📊 Summary:")
        print(f"   Processed: {processed_count} emails")
        print(f"   New applications: {new_applications}")
        print(f"   Updated applications: {updated_applications}")
        
        return new_applications, updated_applications
        
    finally:
        db.close()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Job Application Tracker (CLI)")
    parser.add_argument('command', choices=['scan', 'list', 'search', 'update', 'stats', 'users'],
                       help='Command to execute')
    parser.add_argument('--email', type=str,
                       help='User email address (required for list, search, update, stats)')
    parser.add_argument('--days', type=int, default=90,
                       help='Number of days to scan back (default: 90)')
    parser.add_argument('--limit', type=int, default=10,
                       help='Number of applications to list (default: 10)')
    parser.add_argument('--company', type=str,
                       help='Company name to search for')
    parser.add_argument('--status', type=str,
                       help='Status to search for')
    parser.add_argument('--platform', type=str,
                       help='Platform to search for')
    parser.add_argument('--id', type=int,
                       help='Application ID for update command')
    parser.add_argument('--new-status', type=str,
                       help='New status for update command')
    
    args = parser.parse_args()
    
    try:
        db = DatabaseManager()
        
        if args.command == 'users':
            # List all users
            users = db.get_all_users()
            print(f"\n👥 Registered Users ({len(users)}):")
            print("-" * 80)
            for user in users:
                gmail_status = "✓ Connected" if user.gmail_token else "✗ Not connected"
                print(f"  {user.email} - Gmail: {gmail_status}")
            db.close()
            return
        
        if args.command == 'scan':
            if not args.email:
                print("❌ Error: --email required for scan command")
                print("   Example: python main.py scan --email user@example.com")
                db.close()
                sys.exit(1)
            
            user = db.get_user_by_email(args.email)
            if not user:
                print(f"❌ User not found: {args.email}")
                db.close()
                sys.exit(1)
            
            print(f"\n📧 Scanning emails for user: {args.email}")
            print("-" * 80)
            scan_user_emails_cli(user.id, args.days)
        
        elif args.command in ['list', 'search', 'update', 'stats']:
            if not args.email:
                print("❌ Error: --email required for this command")
                print("   Example: python main.py list --email user@example.com")
                db.close()
                sys.exit(1)
            
            user = db.get_user_by_email(args.email)
            if not user:
                print(f"❌ User not found: {args.email}")
                db.close()
                sys.exit(1)
            
            user_id = user.id
            
            if args.command == 'list':
                applications = db.get_all_applications(user_id, days_back=None)
                limit = args.limit
                
                print(f"\n📋 Recent Job Applications for {args.email} (showing {limit}):")
                print("-" * 80)
                
                if not applications:
                    print("No job applications found.")
                    db.close()
                    return
                
                for i, app in enumerate(applications[:limit]):
                    print(f"{i+1}. {app.company_name}")
                    print(f"   Position: {app.job_title}")
                    print(f"   Platform: {app.platform}")
                    print(f"   Status: {app.status}")
                    print(f"   Applied: {app.date_applied.strftime('%Y-%m-%d')}")
                    print(f"   Email: {app.email_subject[:50]}..." if app.email_subject else "   Email: No subject")
                    print()
            
            elif args.command == 'search':
                applications = db.search_applications(user_id, args.company, args.status, args.platform)
                
                print(f"\n🔍 Search Results for {args.email}:")
                print("-" * 80)
                
                if not applications:
                    print("No applications found matching your criteria.")
                    db.close()
                    return
                
                for app in applications:
                    print(f"• {app.company_name} - {app.job_title}")
                    print(f"  Platform: {app.platform} | Status: {app.status}")
                    print(f"  Applied: {app.date_applied.strftime('%Y-%m-%d')}")
                    print()
            
            elif args.command == 'update':
                if not args.id or not args.new_status:
                    print("❌ Error: --id and --new-status are required for update command")
                    db.close()
                    sys.exit(1)
                
                success = db.update_application_status(args.id, user_id, args.new_status)
                if success:
                    print(f"✅ Updated application status to: {args.new_status}")
                else:
                    print(f"❌ Failed to update application status")
            
            elif args.command == 'stats':
                applications = db.get_all_applications(user_id)
                
                print(f"\n📊 Application Statistics for {args.email}:")
                print("-" * 40)
                
                if not applications:
                    print("No job applications found.")
                    db.close()
                    return
                
                total_apps = len(applications)
                status_counts = {}
                platform_counts = {}
                
                for app in applications:
                    status_counts[app.status] = status_counts.get(app.status, 0) + 1
                    platform_counts[app.platform] = platform_counts.get(app.platform, 0) + 1
                
                print(f"Total Applications: {total_apps}")
                
                print("\nBy Status:")
                for status, count in status_counts.items():
                    print(f"  {status.title()}: {count}")
                
                print("\nBy Platform:")
                for platform, count in platform_counts.items():
                    print(f"  {platform.title()}: {count}")
        
        db.close()
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
