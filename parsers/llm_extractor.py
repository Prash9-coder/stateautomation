import os
import json
from typing import Optional

class LLMExtractor:
    def __init__(self):
        # Import settings
        try:
            from config.settings import settings
            self.provider = settings.LLM_PROVIDER
            self.groq_key = settings.GROQ_API_KEY
            self.gemini_key = settings.GEMINI_API_KEY
        except Exception as e:
            print(f"⚠️  Warning: Could not load settings: {e}")
            self.provider = os.getenv("LLM_PROVIDER", "gemini")
            self.groq_key = os.getenv("GROQ_API_KEY", "")
            self.gemini_key = os.getenv("GEMINI_API_KEY", "")
        
        print(f"🤖 LLM Provider: {self.provider}")
        
        # Initialize the appropriate client
        if self.provider == "groq":
            try:
                from groq import Groq
                self.client = Groq(api_key=self.groq_key)
                self.model = "mixtral-8x7b-32768"
                print(f"✅ Groq client initialized with model: {self.model}")
            except Exception as e:
                print(f"❌ Failed to initialize Groq: {e}")
                raise
        else:  # gemini
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.gemini_key)
                self.model = "gemini-2.0-flash-thinking-exp-01-21"  # Updated to latest model
                print(f"✅ Gemini client initialized with model: {self.model}")
            except Exception as e:
                print(f"❌ Failed to initialize Gemini: {e}")
                raise
    
    def extract_structured_data(self, raw_text: str) -> dict:
        """Use LLM to extract structured data from raw statement text"""
        
        print(f"📊 Extracting data using {self.provider}...")
        print(f"   Text length: {len(raw_text)} characters")
        
        # Limit text to avoid token limits
        max_chars = 15000
        if len(raw_text) > max_chars:
            print(f"   ⚠️  Truncating text from {len(raw_text)} to {max_chars} chars")
            raw_text = raw_text[:max_chars]
        
        prompt = f"""
You are a bank statement parser. Extract the following information from the text and return ONLY valid JSON.

Required format:
{{
  "header": {{
    "bank_name": "string or null",
    "account_holder": "string",
    "account_number": "string",
    "ifsc": "string or null",
    "micr": "string or null",
    "branch": "string or null",
    "statement_period": "string or null",
    "address": "string or null"
  }},
  "transactions": [
    {{
      "date": "YYYY-MM-DD",
      "description": "string",
      "credit": 0.0,
      "debit": 0.0,
      "balance": 0.0,
      "ref": "string or null"
    }}
  ],
  "opening_balance": 0.0,
  "closing_balance": 0.0
}}

Rules:
- Extract ALL transactions in chronological order
- Credit/Debit amounts must be positive numbers (or 0)
- If a field is missing, use null for strings, 0.0 for numbers
- Dates must be in YYYY-MM-DD format
- Return ONLY the JSON object, no markdown, no explanation

Bank Statement Text:
{raw_text}

Return the JSON now:
"""
        
        try:
            if self.provider == "groq":
                content = self._query_groq(prompt)
            else:
                content = self._query_gemini(prompt)
            
            # Clean and parse JSON
            json_data = self._clean_json_response(content)
            
            print(f"✅ Successfully extracted data")
            print(f"   Found {len(json_data.get('transactions', []))} transactions")
            
            return json_data
            
        except Exception as e:
            print(f"❌ LLM extraction failed: {e}")
            # Return dummy data as fallback
            return self._get_dummy_data()
    
    def _query_groq(self, prompt: str) -> str:
        """Query Groq API"""
        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a precise bank statement data extractor. Return only valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model=self.model,
            temperature=0.1,
            max_tokens=8000
        )
        return response.choices[0].message.content
    
    def _query_gemini(self, prompt: str) -> str:
        """Query Gemini API"""
        import google.generativeai as genai
        
        model = genai.GenerativeModel(
            self.model,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 8000,
            }
        )
        
        response = model.generate_content(prompt)
        return response.text
    
    def _clean_json_response(self, content: str) -> dict:
        """Clean and parse JSON from LLM response"""
        
        # Remove markdown code blocks
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        
        if content.endswith("```"):
            content = content[:-3]
        
        content = content.strip()
        
        # Parse JSON
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parse error: {e}")
            print(f"   Response preview: {content[:200]}...")
            
            # Try to fix common issues
            # Remove any text before first {
            if '{' in content:
                content = content[content.index('{'):]
            # Remove any text after last }
            if '}' in content:
                content = content[:content.rindex('}')+1]
            
            try:
                return json.loads(content)
            except:
                print("❌ Could not parse JSON even after cleaning")
                raise
    
    def _get_dummy_data(self) -> dict:
        """Return dummy data when extraction fails"""
        from datetime import date
        
        print("⚠️  Returning dummy data")
        
        return {
            "header": {
                "bank_name": "Unknown Bank",
                "account_holder": "Please Edit",
                "account_number": "0000000000",
                "ifsc": None,
                "micr": None,
                "branch": None,
                "statement_period": None,
                "address": None
            },
            "transactions": [
                {
                    "date": date.today().isoformat(),
                    "description": "Dummy transaction - LLM extraction failed",
                    "credit": 0.0,
                    "debit": 0.0,
                    "balance": 0.0,
                    "ref": None
                }
            ],
            "opening_balance": 0.0,
            "closing_balance": 0.0
        }