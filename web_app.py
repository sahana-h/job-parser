"""Web application for viewing job applications."""

from flask import Flask, render_template, jsonify, request, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from database import DatabaseManager
from auth import authenticate_user, create_user_account, UserAuth
from gmail_client import GmailClient
from token_manager import encrypt_token, decrypt_token
from email_parser import EmailParser
from email_classifier import RecruitingEmailClassifier
from google_auth_oauthlib.flow import Flow
import json
import os
from datetime import datetime
from config import SECRET_KEY

app = Flask(__name__)
app.secret_key = SECRET_KEY

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login."""
    db = DatabaseManager()
    try:
        user = db.get_user_by_id(int(user_id))
        if user:
            return UserAuth(user.id, user.email)
        return None
    finally:
        db.close()

def scan_user_emails(user_id, days_back=10):
    """
    Scan and process emails for a specific user.
    
    Args:
        user_id: User ID to scan emails for
        days_back: Number of days to look back (default: 10 days for new users)
    """
    try:
        db = DatabaseManager()
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
        
        # Clean up old applications first
        db.cleanup_old_applications(user_id, 90)
        
        # Get already processed message IDs to avoid duplicates
        processed_ids = db.get_processed_message_ids(user_id)
        print(f"Already have {len(processed_ids)} processed emails in database")
        
        # Get recent job emails
        emails = gmail_client.get_recent_job_emails(days_back)
        print(f"Found {len(emails)} potential job emails for user {user_id}")
        
        # Filter out already processed emails
        emails = [e for e in emails if e.get('message_id') not in processed_ids]
        print(f"After filtering duplicates: {len(emails)} new emails to process")
        
        new_applications = 0
        updated_applications = 0
        
        for email in emails:
            subject = email.get("subject", "No subject")
            
            # Step 1: Use AI to decide if this email is job-related
            try:
                if not recruiting_classifier.is_job_related(email):
                    continue
            except Exception as e:
                print(f"⚠️ Error during AI classification: {e}")
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
                print(f"❌ Error adding to database: {e}")
                continue
        
        print(f"📊 User {user_id} scan complete: {new_applications} new, {updated_applications} updated")
        db.close()
        return new_applications, updated_applications
        
    except Exception as e:
        print(f"Error scanning emails for user {user_id}: {e}")
        raise

def create_app():
    """Create Flask application."""
    
    @app.route('/')
    @login_required
    def index():
        """Main dashboard page."""
        db = DatabaseManager()
        applications = db.get_all_applications(current_user.id)
        user = db.get_user_by_id(current_user.id)
        gmail_connected = user and user.gmail_token is not None
        db.close()
        
        # Convert datetime objects to strings for JSON serialization
        apps_data = []
        for app in applications:
            apps_data.append({
                'id': app.id,
                'company_name': app.company_name,
                'job_title': app.job_title,
                'platform': app.platform,
                'status': app.status,
                'date_applied': app.date_applied.strftime('%Y-%m-%d') if app.date_applied else 'Unknown',
                'email_subject': app.email_subject,
                'created_at': app.created_at.strftime('%Y-%m-%d %H:%M') if app.created_at else 'Unknown'
            })
        
        return render_template('dashboard.html', applications=apps_data, gmail_connected=gmail_connected)
    
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """Login page."""
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            user, error = authenticate_user(email, password)
            if user:
                login_user(user)
                flash('Logged in successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash(error or 'Invalid credentials', 'error')
        return render_template('login.html')
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """Register page."""
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            
            user, error = create_user_account(email, password)
            if user:
                login_user(user)
                flash('Account created successfully!', 'success')
                return redirect(url_for('index'))
            else:
                flash(error or 'Failed to create account', 'error')
        
        return render_template('register.html')
    
    @app.route('/logout')
    @login_required
    def logout():
        """Logout user."""
        logout_user()
        flash('Successfully logged out!', 'success')
        return redirect(url_for('login'))
    
    @app.route('/api/applications')
    @login_required
    def api_applications():
        """API endpoint to get all applications for the current user."""
        days_back = request.args.get('days', type=int)
        db = DatabaseManager()
        applications = db.get_all_applications(current_user.id, days_back)
        db.close()
        
        apps_data = []
        for app in applications:
            apps_data.append({
                'id': app.id,
                'company_name': app.company_name,
                'job_title': app.job_title,
                'platform': app.platform,
                'status': app.status,
                'date_applied': app.date_applied.strftime('%Y-%m-%d') if app.date_applied else 'Unknown',
                'email_subject': app.email_subject,
                'email_date': app.email_date.strftime('%Y-%m-%d %H:%M') if app.email_date else 'Unknown',
                'created_at': app.created_at.strftime('%Y-%m-%d %H:%M') if app.created_at else 'Unknown'
            })
        
        return jsonify(apps_data)
    
    @app.route('/api/stats')
    @login_required
    def api_stats():
        """API endpoint to get statistics for the current user."""
        days_back = request.args.get('days', type=int)
        db = DatabaseManager()
        applications = db.get_all_applications(current_user.id, days_back)
        
        total_apps = len(applications)
        status_counts = {}
        platform_counts = {}
        
        for app in applications:
            # Count by status
            status_counts[app.status] = status_counts.get(app.status, 0) + 1
            
            # Count by platform
            platform_counts[app.platform] = platform_counts.get(app.platform, 0) + 1
        
        db.close()
        
        return jsonify({
            'total_applications': total_apps,
            'status_counts': status_counts,
            'platform_counts': platform_counts
        })
    
    @app.route('/api/update_status', methods=['POST'])
    @login_required
    def api_update_status():
        """API endpoint to update application status."""
        data = request.json
        app_id = data.get('id')
        new_status = data.get('status')
        
        if not app_id or not new_status:
            return jsonify({'error': 'Missing id or status'}), 400
        
        db = DatabaseManager()
        success = db.update_application_status(app_id, current_user.id, new_status)
        db.close()
        
        if success:
            return jsonify({'success': True, 'message': 'Status updated successfully'})
        else:
            return jsonify({'error': 'Failed to update status'}), 500
    
    @app.route('/api/delete_application', methods=['POST'])
    @login_required
    def api_delete_application():
        """API endpoint to delete one or more applications."""
        data = request.json
        app_ids = data.get('ids') or [data.get('id')]  # Support both single ID and list of IDs
        
        if not app_ids:
            return jsonify({'error': 'Missing application id(s)'}), 400
        
        # Ensure app_ids is a list
        if not isinstance(app_ids, list):
            app_ids = [app_ids]
        
        db = DatabaseManager()
        deleted_count = 0
        failed_count = 0
        
        for app_id in app_ids:
            success = db.delete_application(app_id, current_user.id)
            if success:
                deleted_count += 1
            else:
                failed_count += 1
        
        db.close()
        
        if deleted_count > 0:
            message = f'Successfully deleted {deleted_count} application(s)'
            if failed_count > 0:
                message += f', {failed_count} failed'
            return jsonify({'success': True, 'message': message, 'deleted': deleted_count})
        else:
            return jsonify({'error': 'Failed to delete applications'}), 500
    
    @app.route('/api/add_application', methods=['POST'])
    @login_required
    def api_add_application():
        """API endpoint to manually add an application."""
        data = request.json
        
        company_name = data.get('company_name', '').strip()
        job_title = data.get('job_title', '').strip()
        platform = data.get('platform', 'Unknown Platform').strip()
        status = data.get('status', 'applied').strip()
        date_applied = data.get('date_applied')
        
        if not company_name:
            return jsonify({'error': 'Company name is required'}), 400
        
        # Parse date
        from datetime import datetime
        try:
            if date_applied:
                if isinstance(date_applied, str):
                    date_applied = datetime.strptime(date_applied, '%Y-%m-%d')
            else:
                date_applied = datetime.utcnow()
        except Exception as e:
            return jsonify({'error': f'Invalid date format: {e}'}), 400
        
        # Create job data structure
        job_data = {
            'company_name': company_name,
            'job_title': job_title or 'Unknown Position',
            'platform': platform or 'Unknown Platform',
            'status': status,
            'date_applied': date_applied,
            'email_subject': f'Manual entry: {company_name} - {job_title}',
            'email_body': 'Manually added application',
            'email_date': date_applied,
            'gmail_message_id': f'manual_{current_user.id}_{datetime.utcnow().timestamp()}'  # Unique ID for manual entries
        }
        
        db = DatabaseManager()
        try:
            result = db.add_job_application(job_data, current_user.id)
            
            if result:
                # Extract data before closing the session
                app_data = {
                    'id': result.id,
                    'company_name': result.company_name,
                    'job_title': result.job_title
                }
                db.close()
                
                return jsonify({
                    'success': True,
                    'message': 'Application added successfully',
                    'application': app_data
                })
            else:
                db.close()
                return jsonify({'error': 'Failed to add application'}), 500
        except Exception as e:
            db.close()
            return jsonify({'error': f'Error adding application: {str(e)}'}), 500
    
    @app.route('/connect_gmail')
    @login_required
    def connect_gmail():
        """Start Gmail OAuth flow."""
        try:
            # Build redirect URI
            redirect_uri = url_for('gmail_callback', _external=True)
            
            # Get authorization URL and flow
            auth_url, state, flow = GmailClient.get_authorization_url(redirect_uri)
            
            # Store flow state in session (we'll recreate flow in callback)
            # Store the state to verify in callback
            session['oauth_state'] = state
            session['oauth_redirect_uri'] = redirect_uri
            
            return redirect(auth_url)
        except Exception as e:
            flash(f'Error connecting Gmail: {e}', 'error')
            return redirect(url_for('index'))
    
    @app.route('/disconnect_gmail')
    @login_required
    def disconnect_gmail():
        """Disconnect Gmail by clearing the token."""
        try:
            db = DatabaseManager()
            try:
                user = db.get_user_by_id(current_user.id)
                if user:
                    user.gmail_token = None
                    user.updated_at = datetime.utcnow()
                    db.session.commit()
                    flash('Gmail disconnected successfully. You can reconnect anytime.', 'success')
                else:
                    flash('User not found', 'error')
            finally:
                db.close()
        except Exception as e:
            flash(f'Error disconnecting Gmail: {e}', 'error')
        
        return redirect(url_for('index'))
    
    @app.route('/gmail_callback')
    @login_required
    def gmail_callback():
        """Handle Gmail OAuth callback."""
        try:
            code = request.args.get('code')
            state = request.args.get('state')
            error = request.args.get('error')
            
            if error:
                flash(f'Gmail authorization error: {error}', 'error')
                return redirect(url_for('index'))
            
            if not code:
                flash('Gmail authorization cancelled or failed', 'error')
                return redirect(url_for('index'))
            
            # Verify state matches
            if state != session.get('oauth_state'):
                flash('Invalid OAuth state. Please try again.', 'error')
                return redirect(url_for('index'))
            
            # Recreate flow with same redirect URI
            redirect_uri = session.get('oauth_redirect_uri')
            if not redirect_uri:
                flash('OAuth session expired. Please try again.', 'error')
                return redirect(url_for('index'))
            
            # Recreate flow and exchange code for token
            flow = Flow.from_client_secrets_file(
                os.getenv('GMAIL_CREDENTIALS_FILE', 'credentials.json'),
                scopes=['https://www.googleapis.com/auth/gmail.readonly'],
                redirect_uri=redirect_uri
            )
            
            # Exchange code for token
            token_json = GmailClient.get_token_from_flow(flow, code)
            encrypted_token_bytes = encrypt_token(token_json.encode('utf-8'))
            # Convert bytes to string for PostgreSQL Text column
            # Fernet tokens are base64-encoded, so they decode to valid UTF-8 strings
            try:
                encrypted_token = encrypted_token_bytes.decode('utf-8')
            except UnicodeDecodeError:
                # Fallback: use base64 encoding if UTF-8 fails (shouldn't happen with Fernet)
                import base64
                encrypted_token = base64.b64encode(encrypted_token_bytes).decode('utf-8')
            
            # Save token to database
            db = DatabaseManager()
            try:
                db.update_user_gmail_token(current_user.id, encrypted_token)
            finally:
                db.close()
            
            # Clean up session
            session.pop('oauth_state', None)
            session.pop('oauth_redirect_uri', None)
            
            # Start email scan for the past 10 days (baseline for new users)
            # This will process emails and add them to the database
            try:
                new_count, updated_count = scan_user_emails(current_user.id, days_back=10)
                flash(f'Gmail connected! Found {new_count} new applications and updated {updated_count} existing ones.', 'success')
            except Exception as scan_error:
                flash(f'Gmail connected, but email scan had issues: {scan_error}. You can try scanning manually later.', 'error')
            
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'Error completing Gmail connection: {e}', 'error')
            return redirect(url_for('index'))
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("🌐 Starting Job Application Tracker Web Dashboard...")
    print("📱 Open your browser and go to: http://localhost:8080")
    app.run(debug=True, host='0.0.0.0', port=8080)
