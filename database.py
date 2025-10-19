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
        """Add a new job application to the database."""
        try:
            # Check if application already exists
            existing = self.session.query(JobApplication).filter_by(
                gmail_message_id=job_data['gmail_message_id']
            ).first()
            
            if existing:
                print(f"Job application already exists for message ID: {job_data['gmail_message_id']}")
                return existing
            
            job_app = JobApplication(
                company_name=job_data['company_name'],
                job_title=job_data['job_title'],
                platform=job_data['platform'],
                status=job_data.get('status', 'applied'),
                date_applied=job_data['date_applied'],
                email_subject=job_data.get('email_subject'),
                email_body=job_data.get('email_body'),
                email_date=job_data['email_date'],
                gmail_message_id=job_data['gmail_message_id']
            )
            
            self.session.add(job_app)
            self.session.commit()
            print(f"Added job application: {job_data['company_name']} - {job_data['job_title']}")
            return job_app
            
        except Exception as e:
            self.session.rollback()
            print(f"Error adding job application: {e}")
            return None
    
    def get_all_applications(self):
        """Get all job applications."""
        return self.session.query(JobApplication).order_by(JobApplication.date_applied.desc()).all()
    
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
