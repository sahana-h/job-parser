"""Main application for job application tracker."""

import sys
import argparse
from datetime import datetime, timedelta
from gmail_client import GmailClient
from email_parser import EmailParser
from database import DatabaseManager
from email_classifier import RecruitingEmailClassifier

class JobApplicationTracker:
    """Main job application tracker application."""
    
    def __init__(self):
        self.gmail_client = GmailClient()
        self.email_parser = EmailParser()
        self.db_manager = DatabaseManager()
        self.recruiting_classifier = RecruitingEmailClassifier()

    
    def scan_emails(self, days_back=90):
        """Scan Gmail for job application emails."""
        print(f"Scanning Gmail for job application emails from the last {days_back} days...")
        
        try:
            # Clean up old applications first (keep 90 days)
            print("🧹 Cleaning up applications older than 90 days...")
            self.db_manager.cleanup_old_applications(90)
            
            # Get recent job emails
            emails = self.gmail_client.get_recent_job_emails(days_back)
            print(f"Found {len(emails)} potential job emails")
            
            processed_count = 0
            new_applications = 0
            updated_applications = 0
            
            for email in emails:
                subject = email.get("subject", "No subject")
                print(f"\n📧 Processing email: {subject[:60]}")

                # 🧠 Step 1: Use AI to decide if this email is job-related
                try:
                    if not self.recruiting_classifier.is_job_related(email):
                        print(f"🚫 Skipping non-recruiting email: {subject}")
                        continue
                except Exception as e:
                    print(f"⚠️ Error during AI classification: {e}")
                    continue

                # 🤖 Step 2: Parse the recruiting email to extract structured info
                job_data = self.email_parser.parse_job_email(email)
                if not job_data:
                    print("❌ Could not parse job information from email.")
                    continue

                # 💾 Step 3: Store or update in database
                try:
                    result = self.db_manager.add_job_application(job_data)
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
            
        except Exception as e:
            print(f"Error scanning emails: {e}")
    
    def list_applications(self, limit=10):
        """List recent job applications."""
        print(f"\n📋 Recent Job Applications (showing {limit}):")
        print("-" * 80)
        
        applications = self.db_manager.get_all_applications()
        
        if not applications:
            print("No job applications found. Run 'python main.py scan' to process emails.")
            return
        
        for i, app in enumerate(applications[:limit]):
            print(f"{i+1}. {app.company_name}")
            print(f"   Position: {app.job_title}")
            print(f"   Platform: {app.platform}")
            print(f"   Status: {app.status}")
            print(f"   Applied: {app.date_applied.strftime('%Y-%m-%d')}")
            print(f"   Email: {app.email_subject[:50]}..." if app.email_subject else "   Email: No subject")
            print()
    
    def search_applications(self, company=None, status=None, platform=None):
        """Search job applications by criteria."""
        print("\n🔍 Search Results:")
        print("-" * 80)
        
        applications = self.db_manager.search_applications(company, status, platform)
        
        if not applications:
            print("No applications found matching your criteria.")
            return
        
        for app in applications:
            print(f"• {app.company_name} - {app.job_title}")
            print(f"  Platform: {app.platform} | Status: {app.status}")
            print(f"  Applied: {app.date_applied.strftime('%Y-%m-%d')}")
            print()
    
    def update_status(self, app_id, new_status):
        """Update application status."""
        success = self.db_manager.update_application_status(app_id, new_status)
        if success:
            print(f"✅ Updated application status to: {new_status}")
        else:
            print(f"❌ Failed to update application status")
    
    def stats(self):
        """Show application statistics."""
        applications = self.db_manager.get_all_applications()
        
        if not applications:
            print("No job applications found.")
            return
        
        total_apps = len(applications)
        status_counts = {}
        platform_counts = {}
        
        for app in applications:
            # Count by status
            status_counts[app.status] = status_counts.get(app.status, 0) + 1
            
            # Count by platform
            platform_counts[app.platform] = platform_counts.get(app.platform, 0) + 1
        
        print("\n📊 Application Statistics:")
        print("-" * 40)
        print(f"Total Applications: {total_apps}")
        
        print("\nBy Status:")
        for status, count in status_counts.items():
            print(f"  {status.title()}: {count}")
        
        print("\nBy Platform:")
        for platform, count in platform_counts.items():
            print(f"  {platform.title()}: {count}")
    
    def close(self):
        """Close database connection."""
        self.db_manager.close()

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Job Application Tracker")
    parser.add_argument('command', choices=['scan', 'list', 'search', 'update', 'stats'], 
                       help='Command to execute')
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
        tracker = JobApplicationTracker()
        
        if args.command == 'scan':
            tracker.scan_emails(args.days)
        elif args.command == 'list':
            tracker.list_applications(args.limit)
        elif args.command == 'search':
            tracker.search_applications(args.company, args.status, args.platform)
        elif args.command == 'update':
            if not args.id or not args.new_status:
                print("Error: --id and --new-status are required for update command")
                sys.exit(1)
            tracker.update_status(args.id, args.new_status)
        elif args.command == 'stats':
            tracker.stats()
        
        tracker.close()
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
