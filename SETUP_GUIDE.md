# Complete Setup Guide for Multi-User Job Application Tracker

## ✅ Step 1: Gmail OAuth Redirect URI Setup

### Quick Steps:
1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Navigate to Credentials**:
   - Click "APIs & Services" → "Credentials"
   - Or go directly: https://console.cloud.google.com/apis/credentials
3. **Edit Your OAuth 2.0 Client ID**:
   - Find your OAuth 2.0 Client ID in the list (might be named "Desktop client 1")
   - **Click on its name** to edit it
4. **Add Redirect URI**:
   - Scroll to "Authorized redirect URIs" section
   - Click "+ ADD URI"
   - Enter: `http://localhost:8080/gmail_callback`
   - Click "SAVE"
5. **Verify**:
   - Make sure the redirect URI appears in the list
   - No trailing spaces or typos!

### Visual Guide:
```
Google Cloud Console
  └─ APIs & Services
      └─ Credentials
          └─ OAuth 2.0 Client IDs
              └─ [Your Client ID] (click to edit)
                  └─ Authorized redirect URIs
                      └─ + ADD URI
                          └─ http://localhost:8080/gmail_callback
```

---

## ✅ Step 2: Database Configuration

### Current Setup (SQLite - Development):
- **Status**: ✅ Already configured
- **Location**: `job_applications.db` (local file)
- **No action needed** for local development

### For Production (PostgreSQL):
When you're ready to deploy, you'll need a PostgreSQL database. Here are free options:

#### Option A: Supabase (Recommended - Easiest)
1. Go to https://supabase.com/
2. Sign up for free account
3. Create a new project
4. Go to Settings → Database
5. Copy the "Connection string" (URI format)
6. Add to `.env`:
   ```bash
   DATABASE_URL=postgresql://postgres:[YOUR-PASSWORD]@db.[PROJECT-REF].supabase.co:5432/postgres
   ```

#### Option B: Railway
1. Go to https://railway.app/
2. Sign up (free tier available)
3. Create new project → Add PostgreSQL
4. Copy connection string
5. Add to `.env` as above

#### Option C: Render
1. Go to https://render.com/
2. Create free PostgreSQL database
3. Copy connection string
4. Add to `.env` as above

### Database Migration:
When switching to PostgreSQL, the tables will be created automatically on first run (SQLAlchemy handles this).

---

## ✅ Step 3: Environment Variables Verification

### Check Your Current .env File:
Run this command to see your current setup:
```bash
cat .env
```

### Required Variables:
Your `.env` file should have:

```bash
# Gmail API Configuration
GMAIL_CREDENTIALS_FILE=credentials.json

# Gemini API Configuration  
GEMINI_API_KEY=your_gemini_api_key_here

# Encryption Key (for Gmail OAuth tokens)
ENCRYPTION_KEY=IbyQySz8vu81eTNR1-yt00UKPhoo28Dq4_THP2QnoN4=

# Flask Secret Key (for sessions)
SECRET_KEY=e7a7873dce88437e37990e8cd6b83e2fd9d0668598be12a7317f8410f077baa4

# Database (optional - defaults to SQLite)
# DATABASE_URL=sqlite:///job_applications.db
# For PostgreSQL: DATABASE_URL=postgresql://user:password@host:port/database
```

### Verification Commands:

**Check if all variables are set:**
```bash
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('ENCRYPTION_KEY:', 'SET' if os.getenv('ENCRYPTION_KEY') else 'MISSING'); print('SECRET_KEY:', 'SET' if os.getenv('SECRET_KEY') else 'MISSING'); print('GEMINI_API_KEY:', 'SET' if os.getenv('GEMINI_API_KEY') else 'MISSING')"
```

---

## 🚀 Step 4: Test the Application

### Start the Web Server:
```bash
python3 web_app.py
```

### Expected Output:
```
🌐 Starting Job Application Tracker Web Dashboard...
📱 Open your browser and go to: http://localhost:8080
 * Running on http://0.0.0.0:8080
```

### Test Flow:
1. **Open Browser**: Go to http://localhost:8080
2. **Register**: Click "Sign up" and create an account
3. **Login**: Sign in with your credentials
4. **Connect Gmail**: Click "⚠ Connect Gmail" button
5. **Authorize**: Complete Google OAuth flow
6. **Automatic Scan**: App will scan last 10 days of emails
7. **View Dashboard**: See your job applications!

---

## 🔧 Troubleshooting

### Issue: "Gmail authorization error"
- **Solution**: Make sure redirect URI is exactly `http://localhost:8080/gmail_callback` in Google Cloud Console

### Issue: "Database connection failed"
- **Solution**: For SQLite, make sure you have write permissions in the project directory
- **Solution**: For PostgreSQL, verify connection string is correct

### Issue: "ENCRYPTION_KEY not found"
- **Solution**: Make sure `.env` file exists and has `ENCRYPTION_KEY=` line
- **Solution**: Regenerate: `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

---

## 📝 Quick Reference

### Generate New Keys (if needed):
```bash
# Generate ENCRYPTION_KEY
python3 -c "from cryptography.fernet import Fernet; print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())"

# Generate SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"
```

### CLI Commands:
```bash
# List all users
python3 main.py users

# Scan emails for a user
python3 main.py scan --email user@example.com

# List applications
python3 main.py list --email user@example.com --limit 20
```

