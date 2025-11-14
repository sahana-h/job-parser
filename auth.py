"""User authentication utilities."""

import bcrypt
from database import DatabaseManager, User

class UserAuth:
    """User authentication wrapper for Flask-Login."""
    
    def __init__(self, id, email):
        self.id = id
        self.email = email
    
    def is_authenticated(self):
        return True
    
    def is_active(self):
        return True
    
    def is_anonymous(self):
        return False
    
    def get_id(self):
        return str(self.id)

def create_user_account(email, password):
    """Create a new user account."""
    db = DatabaseManager()
    try:
        # Check if user already exists
        if db.get_user_by_email(email):
            return None, "Email already registered."
        
        # Hash password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user = db.create_user(email, hashed_password)
        if user:
            return UserAuth(user.id, user.email), None
        return None, "Failed to create user account."
    except Exception as e:
        return None, str(e)
    finally:
        db.close()

def authenticate_user(email, password):
    """Authenticate a user with email and password."""
    db = DatabaseManager()
    try:
        user = db.get_user_by_email(email)
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
            return UserAuth(user.id, user.email), None
        return None, "Invalid email or password."
    except Exception as e:
        return None, str(e)
    finally:
        db.close()

