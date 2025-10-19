"""Script to check available Gemini models."""

import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_available_models():
    """Check which Gemini models are available."""
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ GEMINI_API_KEY not found in environment variables")
        return
    
    try:
        genai.configure(api_key=api_key)
        
        print("🔍 Checking available Gemini models...")
        print("-" * 50)
        
        # List available models
        models = genai.list_models()
        
        print("Available models:")
        for model in models:
            print(f"  - {model.name}")
            print(f"    Display name: {model.display_name}")
            print(f"    Description: {model.description}")
            print()
        
        # Test a simple generation with gemini-pro
        print("🧪 Testing gemini-pro model...")
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content("Hello, this is a test.")
        print(f"✅ gemini-pro works! Response: {response.text[:50]}...")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check if your API key is correct")
        print("2. Check if you have enabled the Generative AI API in Google AI Studio")
        print("3. Check your API quota and billing")

if __name__ == "__main__":
    check_available_models()
