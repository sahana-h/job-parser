# Quick Start Guide

## ✅ Current Status Check

All environment variables are configured! ✅

## 🎯 Next Steps (In Order):

### 1. Gmail OAuth Setup (5-10 minutes)

**⚠️ IMPORTANT: Your current credentials.json is for "Desktop application". For web OAuth, you need a "Web application" client.**

#### Option A: Create New Web Application OAuth Client (Recommended)

1. **Go to**: https://console.cloud.google.com/apis/credentials
2. **Click** "+ CREATE CREDENTIALS" → "OAuth client ID"
3. **Select**: "Web application" as the application type
4. **Name it**: "Job Tracker Web Client" (or any name)
5. **Add Authorized redirect URI**:
   - Click "+ ADD URI"
   - Enter: `http://localhost:8080/gmail_callback`
   - Click "SAVE"
6. **Download the new credentials.json**:
   - Click the download icon (⬇️) next to your new Web application client
   - Replace your current `credentials.json` file with the new one

#### Option B: Convert Existing Client (If Possible)

1. **Go to**: https://console.cloud.google.com/apis/credentials
2. **Click** on your existing OAuth 2.0 Client ID
3. **Check** if you can change "Application type" to "Web application"
4. **If yes**: Change it and add redirect URI: `http://localhost:8080/gmail_callback`
5. **If no**: Use Option A above

**The redirect URI must match EXACTLY**: `http://localhost:8080/gmail_callback`

### 2. Database Setup (Already Done!)

✅ **Current**: Using SQLite (local file) - No action needed
- Database file: `job_applications.db` (will be created automatically)

📝 **For Production Later**: 
- Set `DATABASE_URL` in `.env` to PostgreSQL connection string
- Free options: Supabase, Railway, Render, Neon

### 3. Start the Application

```bash
python3 web_app.py
```

Then open: http://localhost:8080

### 4. Test the Flow

1. **Register** a new account
2. **Login** with your credentials  
3. **Click "Connect Gmail"** button
4. **Authorize** the app in Google's OAuth screen
5. **Wait** for automatic 10-day email scan
6. **View** your job applications!

---

## 🔍 Verification Checklist

Run these to verify everything is ready:

```bash
# Check environment variables
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('✅ All set!' if all([os.getenv('ENCRYPTION_KEY'), os.getenv('SECRET_KEY'), os.getenv('GEMINI_API_KEY')]) else '❌ Missing variables')"

# Check credentials file
ls -la credentials.json && echo "✅ credentials.json found" || echo "❌ credentials.json missing"

# Test imports
python3 -c "import web_app; print('✅ All imports successful!')"
```

---

## 🆘 Common Issues

### "redirect_uri_mismatch" error
- **Fix**: Make sure redirect URI in Google Cloud Console is exactly: `http://localhost:8080/gmail_callback`

### "Invalid client" error  
- **Fix**: Your credentials.json might be for Desktop app. Create a new Web application OAuth client.

### Database errors
- **Fix**: Make sure you have write permissions in the project directory (for SQLite)

---

## 📚 More Details

See `SETUP_GUIDE.md` for detailed instructions on each step.

