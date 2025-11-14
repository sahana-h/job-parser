"""Background scheduler for automatic email monitoring."""

import time
import schedule
import json
from datetime import datetime
from database import DatabaseManager
from gmail_client import GmailClient
from email_parser import EmailParser
from email_classifier import RecruitingEmailClassifier
from token_manager import decrypt_token
from config import CHECK_INTERVAL_MINUTES

class EmailMonitor:
    """Background email monitor that runs continuously for all users."""
    
    def __init__(self):
        self.is_running = False
    
    def start_monitoring(self):
        """Start the background monitoring service."""
        print("🤖 Starting AI Email Monitor...")
        print(f"📧 Will check Gmail for all users every {CHECK_INTERVAL_MINUTES} minutes")
        print("🔄 Press Ctrl+C to stop monitoring")
        print("-" * 50)
        
        try:
            # Schedule the email checking job
            schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(self.check_emails_for_all_users)
            
            # Run initial check
            self.check_emails_for_all_users()
            
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
    
    def check_emails_for_all_users(self):
        """Check for new job application emails for all users with Gmail connected."""
        try:
            print(f"\n🕐 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Checking emails for all users...")
            
            db = DatabaseManager()
            try:
                # Get all users
                users = db.get_all_users()
                print(f"   👥 Found {len(users)} total users")
                
                users_processed = 0
                total_new = 0
                total_updated = 0
                
                for user in users:
                    if not user.gmail_token:
                        print(f"   ⏭️  Skipping user {user.email} (no Gmail token)")
                        continue
                    
                    try:
                        print(f"\n   👤 Processing emails for user: {user.email}")
                        
                        # Process emails for this user (last 1 day for scheduled checks)
                        new_count, updated_count = self.process_user_emails(user.id, days_back=1)
                        
                        total_new += new_count
                        total_updated += updated_count
                        users_processed += 1
                        
                        print(f"   ✅ User {user.email}: {new_count} new, {updated_count} updated")
                        
                    except Exception as e:
                        print(f"   ❌ Error processing user {user.email}: {e}")
                        continue
                
                print(f"\n   📊 Summary: Processed {users_processed} users, {total_new} new applications, {total_updated} updated")
                
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Error checking emails: {e}")
    
    def process_user_emails(self, user_id, days_back=1):
        """Process emails for a specific user."""
        db = DatabaseManager()
        try:
            user = db.get_user_by_id(user_id)
            
            if not user or not user.gmail_token:
                raise ValueError("User Gmail token not found")
            
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
            
            # Clean up old applications first (keep 90 days)
            db.cleanup_old_applications(user_id, 90)
            
            # Get already processed message IDs to avoid duplicates
            processed_ids = db.get_processed_message_ids(user_id)
            
            # Get recent job emails
            emails = gmail_client.get_recent_job_emails(days_back)
            
            # Filter out already processed emails
            emails = [e for e in emails if e.get('message_id') not in processed_ids]
            
            new_applications = 0
            updated_applications = 0
            
            for email in emails:
                subject = email.get("subject", "No subject")
                
                # Step 1: Use AI to decide if this email is job-related
                try:
                    if not recruiting_classifier.is_job_related(email):
                        continue
                except Exception as e:
                    print(f"      ⚠️ Error during AI classification: {e}")
                    continue
                
                # Step 2: Parse the recruiting email to extract structured info
                job_data = email_parser.parse_job_email(email)
                if not job_data:
                    continue
                
                # Step 3: Store or update in database
                try:
                    result = db.add_job_application(job_data, user_id)
                    if result:
                        if "Updated existing application" in str(result):
                            updated_applications += 1
                        else:
                            new_applications += 1
                except Exception as e:
                    print(f"      ❌ Error adding to database: {e}")
                    continue
            
            return new_applications, updated_applications
            
        finally:
            db.close()
    
    def stop_monitoring(self):
        """Stop the monitoring service."""
        self.is_running = False
        print("✅ Email monitor stopped")

def main():
    """Main entry point for the scheduler."""
    monitor = EmailMonitor()
    monitor.start_monitoring()

if __name__ == "__main__":
    main()
