"""Web application for viewing job applications."""

from flask import Flask, render_template, jsonify, request
from database import DatabaseManager
import json
from datetime import datetime

app = Flask(__name__)

def create_app():
    """Create Flask application."""
    
    @app.route('/')
    def index():
        """Main dashboard page."""
        db = DatabaseManager()
        applications = db.get_all_applications()
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
        
        return render_template('dashboard.html', applications=apps_data)
    
    @app.route('/api/applications')
    def api_applications():
        """API endpoint to get all applications."""
        days_back = request.args.get('days', type=int)
        db = DatabaseManager()
        applications = db.get_all_applications(days_back)
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
    def api_stats():
        """API endpoint to get statistics."""
        days_back = request.args.get('days', type=int)
        db = DatabaseManager()
        applications = db.get_all_applications(days_back)
        
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
    def api_update_status():
        """API endpoint to update application status."""
        data = request.json
        app_id = data.get('id')
        new_status = data.get('status')
        
        if not app_id or not new_status:
            return jsonify({'error': 'Missing id or status'}), 400
        
        db = DatabaseManager()
        success = db.update_application_status(app_id, new_status)
        db.close()
        
        if success:
            return jsonify({'success': True, 'message': 'Status updated successfully'})
        else:
            return jsonify({'error': 'Failed to update status'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    print("🌐 Starting Job Application Tracker Web Dashboard...")
    print("📱 Open your browser and go to: http://localhost:8080")
    app.run(debug=True, host='0.0.0.0', port=8080)
