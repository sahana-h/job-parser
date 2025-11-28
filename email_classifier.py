"""Classifies whether an email is recruiting-related using Gemini AI."""

import google.generativeai as genai
from config import GEMINI_API_KEY

class RecruitingEmailClassifier:
    """Uses Gemini AI to determine if an email is recruiting- or job-related."""

    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel("gemini-2.0-flash-001")

    def is_job_related(self, email_data: dict) -> bool:
        """Return True if Gemini believes the email is recruiting-related."""
        try:
            subject = email_data.get("subject", "")
            body = email_data.get("body", "")
            sender = email_data.get("from", "")

            # Prompt focuses on reasoning, short context, and classification only
            prompt = f"""
You are an email classifier. Respond "yes" only if this email is clearly about one of the following:
- A confirmation or receipt that the recipient of the email has applied to a job or internship
- An invitation or scheduling email for an interview for the recipient of the email
- A request to complete an online assessment or test for a specific role for the recipient of the email
- A rejection or update indicating the recipient of the email is no longer being considered

If the email is about anything else (such as newsletters, marketing, software projects, 
system alerts, account notifications, or unrelated communication), respond "no".

Output only one word: "yes" or "no".

Sender: {sender}
Subject: {subject}
Body:
{body[:1500]}
"""
            response = self.model.generate_content(prompt)
            text = response.text.strip().lower()
            return text.startswith("yes")

        except Exception as e:
            print(f"⚠️ Error classifying email: {e}")
            return False
