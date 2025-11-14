# Command Reference Guide

This document lists all available commands you can run in your terminal for the Job Application Tracker.

---

## Web Application

### Start the Web Dashboard
```bash
python3 web_app.py
```
- **What it does**: Starts the Flask web server on `http://localhost:8080`
- **Features**: 
  - User login/registration
  - Gmail OAuth connection
  - Interactive dashboard with charts and statistics
  - View, filter, and update job applications
- **Stop**: Press `Ctrl+C` in the terminal

---

## Scheduler (Background Email Monitoring)

### Start Scheduler (Interactive)
```bash
python3 scheduler.py
```
- **What it does**: Starts the background email monitor that runs continuously
- **Behavior**: 
  - Runs an initial email check immediately
  - Then runs daily at the configured time (default: 9:00 AM)
  - Checks emails from the past 1 day for all users with Gmail connected
- **Stop**: Press `Ctrl+C` in the terminal

### Start Scheduler (Background)
```bash
./start_scheduler.sh
```
- **What it does**: Starts the scheduler in the background (detached from terminal)
- **Logs**: View with `tail -f scheduler.log`
- **Stop**: Run `./stop_scheduler.sh`

### Stop Scheduler
```bash
./stop_scheduler.sh
```
- **What it does**: Stops the background scheduler process

### View Scheduler Logs
```bash
tail -f scheduler.log
```
- **What it does**: Shows real-time scheduler output
- **Stop**: Press `Ctrl+C`

---

## CLI Commands (main.py)

All CLI commands require Python 3. The general format is:
```bash
python3 main.py <command> [options]
```

### List All Users
```bash
python3 main.py users
```
- **What it does**: Shows all registered users and their Gmail connection status
- **Output**: Email addresses and whether Gmail is connected

### Scan Emails for a User
```bash
python3 main.py scan --email user@example.com
```
- **What it does**: Scans and processes job application emails for a specific user
- **Options**:
  - `--email` (required): User's email address
  - `--days` (optional): Number of days to scan back (default: 90)
- **Examples**:
  ```bash
  # Scan last 90 days (default)
  python3 main.py scan --email user@example.com
  
  # Scan last 30 days
  python3 main.py scan --email user@example.com --days 30
  
  # Scan last 10 days
  python3 main.py scan --email user@example.com --days 10
  ```

### List Applications
```bash
python3 main.py list --email user@example.com
```
- **What it does**: Lists job applications for a user
- **Options**:
  - `--email` (required): User's email address
  - `--limit` (optional): Number of applications to show (default: 10)
- **Examples**:
  ```bash
  # Show 10 most recent (default)
  python3 main.py list --email user@example.com
  
  # Show 20 most recent
  python3 main.py list --email user@example.com --limit 20
  
  # Show all applications
  python3 main.py list --email user@example.com --limit 1000
  ```

### Search Applications
```bash
python3 main.py search --email user@example.com [filters]
```
- **What it does**: Searches applications by company, status, or platform
- **Options**:
  - `--email` (required): User's email address
  - `--company` (optional): Filter by company name
  - `--status` (optional): Filter by status (applied, interview, rejected, offer, withdrawn)
  - `--platform` (optional): Filter by platform (workday, greenhouse, lever, etc.)
- **Examples**:
  ```bash
  # Search by company
  python3 main.py search --email user@example.com --company "Google"
  
  # Search by status
  python3 main.py search --email user@example.com --status "interview"
  
  # Search by platform
  python3 main.py search --email user@example.com --platform "workday"
  
  # Combine filters
  python3 main.py search --email user@example.com --status "rejected" --platform "greenhouse"
  ```

### Update Application Status
```bash
python3 main.py update --email user@example.com --id <application_id> --new-status <status>
```
- **What it does**: Updates the status of a specific job application
- **Options**:
  - `--email` (required): User's email address
  - `--id` (required): Application ID (get from list command)
  - `--new-status` (required): New status (applied, interview, rejected, offer, withdrawn)
- **Examples**:
  ```bash
  python3 main.py update --email user@example.com --id 5 --new-status "interview"
  python3 main.py update --email user@example.com --id 10 --new-status "rejected"
  ```

### View Statistics
```bash
python3 main.py stats --email user@example.com
```
- **What it does**: Shows statistics about a user's job applications
- **Output**: 
  - Total applications
  - Count by status
  - Count by platform
- **Example**:
  ```bash
  python3 main.py stats --email user@example.com
  ```

---

## Utility Scripts

### Clear All Users and Data
```bash
python3 clear_all_users.py
```
- **What it does**: Deletes all users and their job applications from the database
- **Warning**: This is permanent! Use `--yes` flag to skip confirmation
- **Example**:
  ```bash
  python3 clear_all_users.py --yes
  ```

### Clear Gmail Tokens
```bash
python3 clear_gmail_tokens.py
```
- **What it does**: Clears Gmail OAuth tokens from all users (forces reconnection)
- **Use case**: If tokens are corrupted or encrypted with wrong key

### Fix Database Unique Constraint
```bash
python3 fix_unique_constraint.py
```
- **What it does**: Migrates database to fix unique constraint on `gmail_message_id`
- **Use case**: Only needed if you see unique constraint errors
- **Note**: This is a one-time migration script

---

## Common Workflows

### Initial Setup
```bash
# 1. Start web app
python3 web_app.py

# 2. In browser: Register account and connect Gmail
# 3. Start scheduler
./start_scheduler.sh
```

### Manual Email Scan
```bash
# Scan emails for a specific user
python3 main.py scan --email user@example.com --days 10
```

### Check Application Status
```bash
# List recent applications
python3 main.py list --email user@example.com --limit 20

# View statistics
python3 main.py stats --email user@example.com
```

### Update Application
```bash
# First, list to find application ID
python3 main.py list --email user@example.com

# Then update status
python3 main.py update --email user@example.com --id 5 --new-status "interview"
```

### Daily Operations
```bash
# Check scheduler is running
tail -f scheduler.log

# View all users
python3 main.py users

# Check stats for a user
python3 main.py stats --email user@example.com
```

---

## ⚙️ Configuration

### Environment Variables (.env file)
- `GEMINI_API_KEY`: Your Google Gemini API key
- `DATABASE_URL`: Database connection string (default: SQLite)
- `SECRET_KEY`: Flask secret key for sessions
- `ENCRYPTION_KEY`: Key for encrypting Gmail tokens
- `SCHEDULER_DAILY_TIME`: Time for daily scheduler run (default: "09:00")
- `CHECK_INTERVAL_MINUTES`: Legacy scheduler interval (default: 30)

### Change Scheduler Time
Edit `.env` file:
```
SCHEDULER_DAILY_TIME=14:30  # Run at 2:30 PM
```

---

## Troubleshooting

### Scheduler Not Running
```bash
# Check if process is running
ps aux | grep scheduler.py

# Check logs
tail -f scheduler.log

# Restart scheduler
./stop_scheduler.sh
./start_scheduler.sh
```

### Token Decryption Errors
```bash
# Clear tokens and reconnect
python3 clear_gmail_tokens.py

# Then reconnect Gmail in web app
```

### Database Issues
```bash
# Fix unique constraint (if needed)
python3 fix_unique_constraint.py
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python3 web_app.py` | Start web dashboard |
| `python3 scheduler.py` | Start scheduler (interactive) |
| `./start_scheduler.sh` | Start scheduler (background) |
| `./stop_scheduler.sh` | Stop scheduler |
| `python3 main.py users` | List all users |
| `python3 main.py scan --email <email>` | Scan emails |
| `python3 main.py list --email <email>` | List applications |
| `python3 main.py search --email <email>` | Search applications |
| `python3 main.py stats --email <email>` | View statistics |
| `python3 main.py update --email <email> --id <id> --new-status <status>` | Update status |
| `python3 clear_all_users.py --yes` | Clear all data |
| `python3 clear_gmail_tokens.py` | Clear Gmail tokens |

---

## Tips

1. **Web App**: Best for interactive use, viewing dashboard, and connecting Gmail
2. **Scheduler**: Run in background for automatic daily email checks
3. **CLI**: Best for scripting, bulk operations, and automation
4. **Logs**: Always check `scheduler.log` if scheduler isn't working
5. **Database**: Uses Supabase (PostgreSQL) in production, SQLite for local dev

