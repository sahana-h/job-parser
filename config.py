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

# Job Platform Email Patterns
JOB_PLATFORM_PATTERNS = [
    "workday",
    "greenhouse",
    "lever",
    "bamboohr",
    "smartrecruiters",
    "icims",
    "jobvite",
    "successfactors",
    "taleo",
    "zenefits",
    "applicantstack",
    "recruitee",
    "personio",
    "bamboohr",
    "adp",
    "paycom",
    "ultipro"
]

# Email Subject Patterns for Job Applications
JOB_EMAIL_SUBJECT_PATTERNS = [
    "application received",
    "thank you for your application",
    "application confirmation",
    "your application has been received",
    "application submitted",
    "job application received",
    "application status update",
    "next steps",
    "interview invitation",
    "application update"
]

