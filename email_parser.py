"""Email parser using Gemini AI for extracting job application information."""

import json
import re
from datetime import datetime
from typing import Dict, Optional
import google.generativeai as genai
from config import GEMINI_API_KEY

class EmailParser:
    """Parser for job application emails using Gemini AI."""
    
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-2.0-flash-001')

        self.STATUS_MAP = {
            "applied": [
                "thank you for applying",
                "application received",
                "we have received your application",
            ],
            "interview": [
                "invite",
                "schedule an interview",
                "interview",
                "call with",
                "recruiter screen",
                "meet",
            ],
            "offer": [
                "congratulations",
                "offer",
                "extend an offer",
                "thrilled to offer",
            ],
            "rejected": [
                "unfortunately",
                "we regret",
                "not moving forward",
                "decline",
            ],
            "withdrawn": ["withdrawn", "you withdrew", "closed application"],
        }
    
    def parse_job_email(self, email_data: Dict) -> Optional[Dict]:
        """Parse job application email and extract structured information."""
        try:
            # Prepare email content for AI processing
            email_content = self._prepare_email_content(email_data)
            
            # Create prompt for Gemini
            prompt = self._create_extraction_prompt(email_content)
            
            # Get AI response
            response = self.model.generate_content(prompt)
            
            raw_text = getattr(response, "text", None)
            if not raw_text and hasattr(response, "candidates"):
                raw_text = response.candidates[0].content.parts[0].text

            extracted_data = self._parse_ai_response(raw_text)

            if not extracted_data:
                return None

            # Fallback rule-based status correction
            body = email_data.get("body", "").lower()
            rule_status = self._infer_status(body)
            if extracted_data.get("status") in [None, "applied"] and rule_status:
                extracted_data["status"] = rule_status

            extracted_data.update(
                {
                    "email_subject": email_data.get("subject"),
                    "email_body": email_data.get("body"),
                    "email_date": self._parse_email_date(email_data.get("date")),
                    "gmail_message_id": email_data.get("message_id"),
                }
            )

            return extracted_data

        except Exception as e:
            print(f"Error parsing email: {e}")
            return None
    
    def _prepare_email_content(self, email_data: Dict) -> str:
        """Prepare email content for AI processing."""
        content_parts = []
        
        # Add subject
        if email_data.get('subject'):
            content_parts.append(f"Subject: {email_data['subject']}")
        
        # Add from field
        if email_data.get('from'):
            content_parts.append(f"From: {email_data['from']}")
        
        # Add body (limit length to avoid token limits)
        body = email_data.get('body', '')
        if body:
            # Truncate body if too long
            max_body_length = 4000
            if len(body) > max_body_length:
                body = body[:max_body_length] + "..."
            content_parts.append(f"Body: {body}")
        
        return "\n\n".join(content_parts)
    
    def _create_extraction_prompt(self, email_content: str) -> str:
        """Prompt for Gemini to extract job application information."""
        return f"""
You are a precise information extraction model.

Your goal is to analyze the following email and determine if it is related to a job application.
If it is not about a job application or not related to the recipient of the email, return exactly this JSON:
{{
  "company_name": null,
  "job_title": null,
  "platform": null,
  "status": null,
  "date_applied": null
}}

If it IS related to a job application, extract:
- company_name
- job_title
- platform (if any mentioned: workday, greenhouse, lever, icims, etc.)
- status (one of: applied, interview, offer, rejected, withdrawn)
- date_applied (prefer from text, else use email date)

Use only information explicitly in the email.
Do not infer or guess values not clearly supported.
For emails that involve updating the recipient of the email but not moving them forward/rejecting them in the application process, keep the status as applied/do not change it. 

Return *only* valid JSON — no code fences, commentary, or explanations.

Example 1:
Email: "Thank you for applying to Google for the Software Engineer Intern role via Workday. Your application was received on October 1, 2025."
JSON:
{{"company_name":"Google","job_title":"Software Engineer Intern","platform":"workday","status":"applied","date_applied":"2025-10-01"}}

Example 2:
Email: "We'd like to invite you to interview for the SWE Intern position at Microsoft."
JSON:
{{"company_name":"Microsoft","job_title":"SWE Intern","platform":null,"status":"interview","date_applied":null}}

Now analyze the following email:
{email_content}

JSON response:
"""
    
    def _parse_ai_response(self, response_text: str) -> Optional[Dict]:
        """Parse AI response and extract JSON data."""
        try:
            if not response_text:
                return None

            response_text = response_text.strip()

            # Strip code fences or markdown
            if response_text.startswith("```"):
                response_text = re.sub(r"^```(?:json)?|```$", "", response_text, flags=re.MULTILINE).strip()

            data = json.loads(response_text)
            if not data or not isinstance(data, dict):
                return None

            # Clean + normalize
            cleaned_data = self._clean_extracted_data(data)
            return cleaned_data

        except json.JSONDecodeError:
            print("⚠️ JSON parsing failed. Raw output:", response_text)
            return None
        except Exception as e:
            print("Error parsing AI response:", e)
            return None
    
    def _clean_extracted_data(self, data: Dict) -> Dict:
        cleaned = {}

        def clean_str(v):
            return v.strip() if isinstance(v, str) and v.strip() else None

        cleaned["company_name"] = clean_str(data.get("company_name"))
        cleaned["job_title"] = clean_str(data.get("job_title"))
        cleaned["platform"] = clean_str(data.get("platform"))
        
        status = data.get("status")
        cleaned["status"] = clean_str(status.lower()) if isinstance(status, str) else "applied"
        
        cleaned["date_applied"] = self._parse_date_string(data.get("date_applied"))
        return cleaned


    def _infer_status(self, text: str) -> Optional[str]:
        """Fallback rule-based status inference from body text."""
        text = text.lower()
        for status, phrases in self.STATUS_MAP.items():
            if any(p in text for p in phrases):
                return status
        return None
    
    def _parse_email_date(self, date_string: str) -> Optional[datetime]:
        """Parse email date string to datetime object."""
        if not date_string:
            return None
        
        try:
            # Try parsing common email date formats
            date_formats = [
                '%a, %d %b %Y %H:%M:%S %z',
                '%a, %d %b %Y %H:%M:%S %Z',
                '%d %b %Y %H:%M:%S %z',
                '%a, %d %b %Y %H:%M:%S %z (%Z)',
                '%a, %d %b %Y %H:%M:%S +0000 (%Z)',
                '%a, %d %b %Y %H:%M:%S -0400 (%Z)',
                '%a, %d %b %Y %H:%M:%S -0500 (%Z)',
                '%a, %d %b %Y %H:%M:%S +0000 (UTC)',
                '%a, %d %b %Y %H:%M:%S -0400 (EDT)',
                '%a, %d %b %Y %H:%M:%S -0500 (EST)',
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue
            
            # If all formats fail, return current time
            print(f"Could not parse date: {date_string}")
            return datetime.now()
            
        except Exception as e:
            print(f"Error parsing email date: {e}")
            return datetime.now()
    
    def _parse_date_string(self, date_string: str) -> Optional[datetime]:
        """Parse date string from AI response."""
        if not date_string:
            return None
        
        try:
            # Try parsing various date formats
            date_formats = [
                '%Y-%m-%d',
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%B %d, %Y',
                '%b %d, %Y',
                '%Y-%m-%d %H:%M:%S'
            ]
            
            for fmt in date_formats:
                try:
                    return datetime.strptime(date_string, fmt)
                except ValueError:
                    continue
            
            # If no format matches, return None
            return None
            
        except Exception as e:
            print(f"Error parsing date string: {e}")
            return None
