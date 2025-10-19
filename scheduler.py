"""Background scheduler for automatic email monitoring."""

import time
import schedule
from datetime import datetime
from main import JobApplicationTracker
from config import CHECK_INTERVAL_MINUTES

class EmailMonitor:
    """Background email monitor that runs continuously."""
    
    def __init__(self):
        self.tracker = None
        self.is_running = False
    
    def start_monitoring(self):
        """Start the background monitoring service."""
        print("🤖 Starting AI Email Monitor...")
        print(f"📧 Will check Gmail every {CHECK_INTERVAL_MINUTES} minutes")
        print("🔄 Press Ctrl+C to stop monitoring")
        print("-" * 50)
        
        try:
            # Initialize the tracker
            self.tracker = JobApplicationTracker()
            
            # Schedule the email checking job
            schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(self.check_emails)
            
            # Run initial check
            self.check_emails()
            
            self.is_running = True
            
            # Keep running
            while self.is_running:
                schedule.run_pending()
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping email monitor...")
            self.stop_monitoring()
        except Exception as e:
            print(f"❌ Error in email monitor: {e}")
            self.stop_monitoring()
    
    def check_emails(self):
        """Check for new job application emails."""
        try:
            print(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Checking for new emails...")
            
            # Clean up old applications first
            print("   🧹 Cleaning up applications older than 30 days...")
            self.tracker.db_manager.cleanup_old_applications()
            
            # Scan for emails from the last day
            emails = self.tracker.gmail_client.get_recent_job_emails(1)
            
            if emails:
                print(f"   📧 Found {len(emails)} new potential job emails")
                
                new_applications = 0
                updated_applications = 0
                
                for email in emails:
                    print(f"   Processing: {email.get('subject', 'No subject')[:50]}...")
                    
                    # Parse email with AI
                    job_data = self.tracker.email_parser.parse_job_email(email)
                    
                    if job_data:
                        # Add to database
                        try:
                            result = self.tracker.db_manager.add_job_application(job_data)
                            if result:
                                # Check if this was a new application or an update
                                if "Updated existing application" in str(result):
                                    updated_applications += 1
                                else:
                                    new_applications += 1
                                
                                job_title = job_data.get('job_title', 'Unknown Position')
                                print(f"   ✅ Processed: {job_data['company_name']} - {job_title}")
                            else:
                                print(f"   ℹ️  Already exists: {job_data['company_name']}")
                        except Exception as e:
                            print(f"   ❌ Error adding to database: {e}")
                    else:
                        print(f"   ❌ Could not parse job information")
                
                print(f"   📊 New: {new_applications}, Updated: {updated_applications}")
            else:
                print("   📭 No new job application emails found")
                
        except Exception as e:
            print(f"❌ Error checking emails: {e}")
    
    def stop_monitoring(self):
        """Stop the monitoring service."""
        self.is_running = False
        if self.tracker:
            self.tracker.close()
        print("✅ Email monitor stopped")

def main():
    """Main entry point for the scheduler."""
    monitor = EmailMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
