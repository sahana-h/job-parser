# Job Application Tracker

An AI-powered tool that automatically monitors your Gmail inbox for job application confirmation emails and tracks your application status.

## Features

- 🔍 **Automatic Email Scanning**: Monitors Gmail for job application emails from platforms like Workday, Greenhouse, Lever, etc.
- 🤖 **AI-Powered Extraction**: Uses Google Gemini 1.5 Flash to extract structured job application data
- 💾 **Local Database**: Stores all application data in SQLite for privacy and offline access
- 📊 **Application Tracking**: View, search, and update your job application status
- 🔒 **Privacy-First**: All data stored locally, no external services required

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Gmail API:
   - Go to "APIs & Services" > "Library"
   - Search for "Gmail API" and enable it
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the JSON file and save it as `credentials.json` in the project directory

### 3. Gemini API Setup

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create a new API key
3. Copy the API key for the next step

### 4. Environment Configuration

Create a `.env` file in the project directory:

```bash
# Gmail API Configuration
GMAIL_CREDENTIALS_FILE=credentials.json

# Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Database Configuration
DATABASE_URL=sqlite:///job_applications.db

# Email Processing Configuration
CHECK_INTERVAL_MINUTES=30
MAX_EMAILS_PER_CHECK=50
```

## Usage

### Scan for Job Applications

Scan your Gmail inbox for job application emails:

```bash
# Scan last 7 days (default)
python main.py scan

# Scan last 30 days
python main.py scan --days 30
```

### List Applications

View your job applications:

```bash
# List recent applications
python main.py list

# List more applications
python main.py list --limit 20
```

### Search Applications

Search for specific applications:

```bash
# Search by company
python main.py search --company "Google"

# Search by status
python main.py search --status "interview"

# Search by platform
python main.py search --platform "workday"
```

### Update Application Status

Update the status of an application:

```bash
python main.py update --id 1 --new-status "interview"
```

### View Statistics

See statistics about your applications:

```bash
python main.py stats
```

## Supported Job Platforms

The tool automatically detects emails from these platforms:

- Workday
- Greenhouse
- Lever
- BambooHR
- SmartRecruiters
- iCIMS
- Jobvite
- SuccessFactors
- Taleo
- Zenefits
- ApplicantStack
- Recruitee
- Personio
- ADP
- Paycom
- UltiPro

## Database Schema

The application stores the following information for each job application:

- Company name
- Job title
- Platform used (Workday, Greenhouse, etc.)
- Application status
- Date applied
- Email subject and body
- Gmail message ID (for deduplication)

## Privacy & Security

- All data is stored locally in SQLite
- No data is sent to external services except for AI processing
- Gmail access is read-only
- API keys are stored in environment variables

## Troubleshooting

### Gmail Authentication Issues

If you encounter authentication issues:

1. Make sure `credentials.json` is in the project directory
2. Delete `token.json` and re-authenticate
3. Ensure Gmail API is enabled in Google Cloud Console

### Gemini API Issues

If you encounter Gemini API issues:

1. Verify your API key in the `.env` file
2. Check your API quota in Google AI Studio
3. Ensure the API key has the correct permissions

### Database Issues

If you encounter database issues:

1. Check file permissions in the project directory
2. Ensure SQLite is properly installed
3. Try deleting the database file to start fresh

## Contributing

Feel free to submit issues and enhancement requests!

## License

MIT License - feel free to use and modify as needed.
