"""Database operations for job application tracker."""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import IntegrityError
from datetime import datetime
from config import DATABASE_URL
import os

# Support for PostgreSQL connection pooling
def get_database_url():
    """Get database URL (pool settings are passed to create_engine, not in URL)."""
    return DATABASE_URL

Base = declarative_base()

class User(Base):
    """SQLAlchemy model for users."""
    
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    gmail_token = Column(Text)  # Encrypted OAuth token for Gmail API
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to job applications
    applications = relationship("JobApplication", back_populates="user")

class JobApplication(Base):
    """SQLAlchemy model for job applications."""
    
    __tablename__ = 'job_applications'
    __table_args__ = (
        UniqueConstraint('user_id', 'gmail_message_id', name='uq_user_message'),
    )
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    company_name = Column(String(255), nullable=False)
    job_title = Column(String(255), nullable=False)
    platform = Column(String(100), nullable=True)  # workday, greenhouse, etc.
    status = Column(String(100), default="applied")  # applied, interview, rejected, etc.
    date_applied = Column(DateTime, nullable=False)
    email_subject = Column(String(500))
    email_body = Column(Text)
    email_date = Column(DateTime, nullable=False)
    gmail_message_id = Column(String(255), nullable=False)  # Unique per user (composite constraint)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship to user
    user = relationship("User", back_populates="applications")

class DatabaseManager:
    """Manages database operations."""
    
    def __init__(self):
        db_url = get_database_url()
        
        # Configure connection pooling for PostgreSQL
        # Pool settings must be passed to create_engine, not in the URL string
        engine_kwargs = {'echo': False}
        if db_url.startswith('postgresql://') or db_url.startswith('postgresql+psycopg2://'):
            engine_kwargs.update({
                'pool_size': 5,
                'max_overflow': 10,
                'pool_pre_ping': True  # Verify connections before using
            })
        
        self.engine = create_engine(db_url, **engine_kwargs)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def add_job_application(self, job_data, user_id):
        """Add a new job application to the database or update existing one."""
        try:
            # First check by message ID and user (exact duplicate)
            existing_by_message = self.session.query(JobApplication).filter(
                JobApplication.gmail_message_id == job_data['gmail_message_id'],
                JobApplication.user_id == user_id
            ).first()
            
            if existing_by_message:
                print(f"Email already processed: {job_data['gmail_message_id']}")
                return existing_by_message
            
            # Check for similar application (same company + similar job title)
            company_name = (job_data.get('company_name') or '').lower().strip()
            job_title = (job_data.get('job_title') or '').lower().strip()
            
            # Skip if no company name
            if not company_name:
                print(f"⚠️ Skipping application with no company name")
                return None
            
            existing_by_content = self.session.query(JobApplication).filter(
                JobApplication.company_name.ilike(f"%{company_name}%"),
                JobApplication.user_id == user_id
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
            company_name = job_data.get('company_name')
            if not company_name:
                print(f"⚠️ Skipping application with no company name")
                return None
                
            job_app = JobApplication(
                user_id=user_id,
                company_name=company_name,
                job_title=job_data.get('job_title') or 'Unknown Position',
                platform=job_data.get('platform') or 'Unknown Platform',
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
            
        except IntegrityError as e:
            # Handle unique constraint violation (duplicate message_id)
            self.session.rollback()
            if 'gmail_message_id' in str(e) or 'uq_user_message' in str(e):
                # Try to get the existing application
                existing = self.session.query(JobApplication).filter(
                    JobApplication.gmail_message_id == job_data['gmail_message_id'],
                    JobApplication.user_id == user_id
                ).first()
                if existing:
                    print(f"Email already processed (caught by constraint): {job_data['gmail_message_id']}")
                    return existing
            print(f"Integrity error adding job application: {e}")
            return None
        except Exception as e:
            self.session.rollback()
            print(f"Error adding job application: {e}")
            return None
    
    def get_all_applications(self, user_id, days_back=None):
        """Get job applications for a specific user, optionally filtered by days back."""
        query = self.session.query(JobApplication).filter(JobApplication.user_id == user_id)
        
        if days_back:
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            query = query.filter(JobApplication.created_at >= cutoff_date)
        
        return query.order_by(JobApplication.date_applied.desc()).all()
    
    def cleanup_old_applications(self, user_id, days_back=90):
        """Remove applications older than specified days (default 90 days) for a specific user."""
        try:
            from datetime import datetime, timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            old_applications = self.session.query(JobApplication).filter(
                JobApplication.user_id == user_id,
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
    
    def get_application_by_id(self, app_id, user_id):
        """Get a specific job application by ID for a specific user."""
        return self.session.query(JobApplication).filter(
            JobApplication.id == app_id,
            JobApplication.user_id == user_id
        ).first()
    
    def delete_application(self, app_id, user_id):
        """Delete a job application."""
        try:
            app = self.session.query(JobApplication).filter(
                JobApplication.id == app_id,
                JobApplication.user_id == user_id
            ).first()
            
            if app:
                self.session.delete(app)
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            print(f"Error deleting application: {e}")
            return False
    
    def update_application_status(self, app_id, user_id, new_status):
        """Update the status of a job application."""
        try:
            app = self.session.query(JobApplication).filter(
                JobApplication.id == app_id,
                JobApplication.user_id == user_id
            ).first()
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
    
    def search_applications(self, user_id, company=None, status=None, platform=None):
        """Search job applications by criteria for a specific user."""
        query = self.session.query(JobApplication).filter(JobApplication.user_id == user_id)
        
        if company:
            query = query.filter(JobApplication.company_name.ilike(f"%{company}%"))
        if status:
            query = query.filter(JobApplication.status.ilike(f"%{status}%"))
        if platform:
            query = query.filter(JobApplication.platform.ilike(f"%{platform}%"))
        
        return query.order_by(JobApplication.date_applied.desc()).all()
    
    # User management methods
    def create_user(self, email, password_hash):
        """Create a new user."""
        try:
            user = User(email=email, password_hash=password_hash)
            self.session.add(user)
            self.session.commit()
            return user
        except Exception as e:
            self.session.rollback()
            print(f"Error creating user: {e}")
            return None
    
    def get_user_by_email(self, email):
        """Get a user by email."""
        return self.session.query(User).filter_by(email=email).first()
    
    def get_user_by_id(self, user_id):
        """Get a user by ID."""
        return self.session.query(User).filter_by(id=user_id).first()
    
    def update_user_gmail_token(self, user_id, token):
        """Update a user's Gmail OAuth token."""
        try:
            user = self.session.query(User).filter_by(id=user_id).first()
            if user:
                user.gmail_token = token
                user.updated_at = datetime.utcnow()
                self.session.commit()
                return True
            return False
        except Exception as e:
            self.session.rollback()
            print(f"Error updating user Gmail token: {e}")
            return False
    
    def get_all_users(self):
        """Get all users (for scheduler)."""
        return self.session.query(User).all()
    
    def get_processed_message_ids(self, user_id):
        """Get all processed Gmail message IDs for a user."""
        applications = self.session.query(JobApplication).filter(
            JobApplication.user_id == user_id
        ).all()
        return {app.gmail_message_id for app in applications if app.gmail_message_id}
    
    def close(self):
        """Close the database session."""
        self.session.close()
