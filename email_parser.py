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
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def parse_job_email(self, email_data: Dict) -> Optional[Dict]:
        """Parse job application email and extract structured information."""
        try:
            # Prepare email content for AI processing
            email_content = self._prepare_email_content(email_data)
            
            # Create prompt for Gemini
            prompt = self._create_extraction_prompt(email_content)
            
            # Get AI response
            response = self.model.generate_content(prompt)
            
            # Parse AI response
            extracted_data = self._parse_ai_response(response.text)
            
            if extracted_data:
                # Add email metadata
                extracted_data.update({
                    'email_subject': email_data.get('subject'),
                    'email_body': email_data.get('body'),
                    'email_date': self._parse_email_date(email_data.get('date')),
                    'gmail_message_id': email_data.get('message_id')
                })
                
                return extracted_data
            
            return None
            
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
            max_body_length = 2000
            if len(body) > max_body_length:
                body = body[:max_body_length] + "..."
            content_parts.append(f"Body: {body}")
        
        return "\n\n".join(content_parts)
    
    def _create_extraction_prompt(self, email_content: str) -> str:
        """Create prompt for Gemini to extract job application information."""
        return f"""
You are an AI assistant that extracts job application information from emails. 

Please analyze the following email and extract the following information in JSON format:

{{
    "company_name": "Name of the company",
    "job_title": "Title of the position applied for",
    "platform": "Platform used (workday, greenhouse, lever, etc.)",
    "status": "Current status (applied, interview, rejected, etc.)",
    "date_applied": "Date when the application was submitted (YYYY-MM-DD format)"
}}

Rules:
1. Extract only information that is explicitly mentioned in the email
2. If information is not available, use null
3. For platform, identify from the sender email domain or email content
4. For status, determine from email content (e.g., "application received" = "applied")
5. For date_applied, extract from email content or use email date as fallback
6. Return ONLY valid JSON, no additional text

Email content:
{email_content}

JSON response:
"""
    
    def _parse_ai_response(self, response_text: str) -> Optional[Dict]:
        """Parse AI response and extract JSON data."""
        try:
            # Clean up response text
            response_text = response_text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                json_start = -1
                json_end = -1
                
                for i, line in enumerate(lines):
                    if line.strip() in ['```', '```json']:
                        if json_start == -1:
                            json_start = i + 1
                        else:
                            json_end = i
                            break
                
                if json_start != -1 and json_end != -1:
                    response_text = '\n'.join(lines[json_start:json_end])
            
            # Parse JSON
            data = json.loads(response_text)
            
            # Validate required fields
            required_fields = ['company_name', 'job_title', 'platform']
            for field in required_fields:
                if not data.get(field):
                    print(f"Missing required field: {field}")
                    return None
            
            # Clean and validate data
            cleaned_data = self._clean_extracted_data(data)
            
            return cleaned_data
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse AI response as JSON: {e}")
            print(f"Response text: {response_text}")
            return None
        except Exception as e:
            print(f"Error parsing AI response: {e}")
            return None
    
    def _clean_extracted_data(self, data: Dict) -> Dict:
        """Clean and validate extracted data."""
        cleaned = {}
        
        # Clean company name
        company_name = data.get('company_name', '').strip()
        if company_name:
            cleaned['company_name'] = company_name
        
        # Clean job title
        job_title = data.get('job_title', '').strip()
        if job_title:
            cleaned['job_title'] = job_title
        
        # Clean platform
        platform = data.get('platform', '').strip().lower()
        if platform:
            cleaned['platform'] = platform
        
        # Clean status
        status = data.get('status', '').strip().lower()
        if status:
            cleaned['status'] = status
        else:
            cleaned['status'] = 'applied'  # Default status
        
        # Parse and clean date
        date_applied = data.get('date_applied')
        if date_applied:
            parsed_date = self._parse_date_string(date_applied)
            if parsed_date:
                cleaned['date_applied'] = parsed_date
        
        return cleaned
    
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
