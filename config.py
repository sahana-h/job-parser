"""Configuration settings for the job application tracker."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Gmail API Configuration
GMAIL_CREDENTIALS_FILE = os.getenv("GMAIL_CREDENTIALS_FILE", "credentials.json")
GMAIL_TOKEN_FILE = os.getenv("GMAIL_TOKEN_FILE", "token.json")

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Database Configuration
# Supports both SQLite (development) and PostgreSQL (production)
# SQLite: sqlite:///job_applications.db
# PostgreSQL: postgresql://user:password@host:port/database
# For free PostgreSQL hosting, check: Supabase, Railway, Render, Neon, etc.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///job_applications.db")

# Flask Secret Key (for session management)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")

# Email Processing Configuration
# Daily scheduler runs at this time (24-hour format, e.g., "09:00" for 9 AM)
SCHEDULER_DAILY_TIME = os.getenv("SCHEDULER_DAILY_TIME", "09:00")
# Legacy: CHECK_INTERVAL_MINUTES (for backward compatibility, but daily scheduler is preferred)
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
MAX_EMAILS_PER_CHECK = int(os.getenv("MAX_EMAILS_PER_CHECK", "50"))
