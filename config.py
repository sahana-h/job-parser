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
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///job_applications.db")

# Email Processing Configuration
CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
MAX_EMAILS_PER_CHECK = int(os.getenv("MAX_EMAILS_PER_CHECK", "50"))
