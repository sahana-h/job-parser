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

# Job Platform Email Patterns# Broad list of common ATS / recruiting platforms
JOB_PLATFORM_PATTERNS = [
    "workday.com",
    "myworkdayjobs.com",
    "greenhouse.io",
    "lever.co",
    "icims.com",
    "smartrecruiters.com",
    "successfactors.com",
    "brassring.com",
    "recruiting",
    "talent",
    "applytracking.com",
    "applicantstack.com",
    "hire.lever.co",
    "jobs.lever.co",
    "breezy.hr",
    "recruitee.com",
    "ashbyhq.com",
    "jobvite.com",
    "adp.com",
    "ultipro.com",
    "careerplug.com",
    "teamtailor.com",
    "paycor.com",
    "oraclecloud.com",
    "dayforcehcm.com",
    "eightfold.ai",
    "comeet.co",
    "jobscore.com",
    "recruitingemail.com",
    "mytalentplatform.com",
]

# Common subject lines that appear in job-related emails
JOB_EMAIL_SUBJECT_PATTERNS = [
    "application received",
    "thank you for applying",
    "your application",
    "submitted your application",
    "interview",
    "candidate update",
    "recruiter",
    "career opportunity",
    "hiring process",
    "next steps",
    "offer",
    "decision on your application",
    "position at",
]
