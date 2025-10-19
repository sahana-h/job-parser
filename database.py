"""Database operations for job application tracker."""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL

Base = declarative_base()

class JobApplication(Base):
    """SQLAlchemy model for job applications."""
    
    __tablename__ = 'job_applications'
    
    id = Column(Integer, primary_key=True)
    company_name = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    platform = Column(String(100), nullable=False)  # workday, greenhouse, etc.
    status = Column(String(100), default="applied")  # applied, interview, rejected, etc.
    date_applied = Column(DateTime, nullable=False)
    email_subject = Column(String(500))
    email_body = Column(Text)
    email_date = Column(DateTime, nullable=False)
    gmail_message_id = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DatabaseManager:
    """Manages database operations."""
    
    def __init__(self):
        self.engine = create_engine(DATABASE_URL, echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def add_job_application(self, job_data):
        """Add a new job application to the database or update existing one."""
        try:
            # First check by message ID (exact duplicate)
            existing_by_message = self.session.query(JobApplication).filter_by(
                gmail_message_id=job_data['gmail_message_id']
            ).first()
            
            if existing_by_message:
                print(f"Email already processed: {job_data['gmail_message_id']}")
                return existing_by_message
            
            # Check for similar application (same company + similar job title)
            company_name = job_data['company_name'].lower().strip()
            job_title = job_data.get('job_title', '').lower().strip()
            
            existing_by_content = self.session.query(JobApplication).filter(
                JobApplication.company_name.ilike(f"%{company_name}%")
            ).all()
            
            # Find the best match based on company name similarity
            best_match = None
            for existing in existing_by_content:
                existing_company = existing.company_name.lower().strip()
                existing_title = existing.job_title.lower().strip()
                
                # Check if company names are very similar
                if (company_name in existing_company or existing_company in company_name or 
                    company_name.split()[0] == existing_company.split()[0]):
                    
                    # If job titles are similar or one is unknown, consider it a match
                    if (job_title == 'unknown position' or existing_title == 'unknown position' or
                        job_title in existing_title or existing_title in job_title or
                        not job_title or not existing_title):
                        best_match = existing
                        break
            
            if best_match:
                # Update existing application with new information
                best_match.status = job_data.get('status', best_match.status)
                best_match.email_subject = job_data.get('email_subject', best_match.email_subject)
                best_match.email_body = job_data.get('email_body', best_match.email_body)
                best_match.email_date = job_data['email_date']
                best_match.updated_at = datetime.utcnow()
                
                # Update job title if we got a better one
                if job_title and job_title != 'unknown position' and best_match.job_title.lower() == 'unknown position':
                    best_match.job_title = job_data.get('job_title', best_match.job_title)
                
                self.session.commit()
                print(f"Updated existing application: {job_data['company_name']} - {job_data.get('job_title', 'Unknown')}")
                return best_match
            
            # Create new application
            job_app = JobApplication(
                company_name=job_data['company_name'],
                job_title=job_data.get('job_title', 'Unknown Position'),
                platform=job_data.get('platform', 'Unknown Platform'),
                status=job_data.get('status', 'applied'),
                date_applied=job_data.get('date_applied') or job_data.get('email_date'),
                email_subject=job_data.get('email_subject'),
                email_body=job_data.get('email_body'),
                email_date=job_data['email_date'],
                gmail_message_id=job_data['gmail_message_id']
            )
            
            self.session.add(job_app)
            self.session.commit()
            print(f"Added new application: {job_data['company_name']} - {job_data.get('job_title', 'Unknown')}")
            return job_app
            
        except Exception as e:
            self.session.rollback()
            print(f"Error adding job application: {e}")
            return None
    
    def get_all_applications(self, days_back=None):
        """Get job applications, optionally filtered by days back."""
        query = self.session.query(JobApplication)
        
        if days_back:
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            query = query.filter(JobApplication.created_at >= cutoff_date)
        
        return query.order_by(JobApplication.date_applied.desc()).all()
    
    def cleanup_old_applications(self, days_back=90):
        """Remove applications older than specified days (default 90 days)."""
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            old_applications = self.session.query(JobApplication).filter(
                JobApplication.created_at < cutoff_date
            ).all()
            
            count = len(old_applications)
            if count > 0:
                for app in old_applications:
                    self.session.delete(app)
                self.session.commit()
                print(f"Cleaned up {count} old applications (older than {days_back} days)")
            
        except Exception as e:
            self.session.rollback()
            print(f"Error cleaning up old applications: {e}")
    
    def get_application_by_id(self, app_id):
        """Get a specific job application by ID."""
        return self.session.query(JobApplication).filter_by(id=app_id).first()
    
    def update_application_status(self, app_id, new_status):
        """Update the status of a job application."""
        try:
            app = self.session.query(JobApplication).filter_by(id=app_id).first()
            if app:
                app.status = new_status
                app.updated_at = datetime.utcnow()
                self.session.commit()
                print(f"Updated application status to: {new_status}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            print(f"Error updating application status: {e}")
            return False
    
    def search_applications(self, company=None, status=None, platform=None):
        """Search job applications by criteria."""
        query = self.session.query(JobApplication)
        
        if company:
            query = query.filter(JobApplication.company_name.ilike(f"%{company}%"))
        if status:
            query = query.filter(JobApplication.status.ilike(f"%{status}%"))
        if platform:
            query = query.filter(JobApplication.platform.ilike(f"%{platform}%"))
        
        return query.order_by(JobApplication.date_applied.desc()).all()
    
    def close(self):
        """Close the database session."""
        self.session.close()
