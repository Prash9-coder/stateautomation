import os
import re
import json
from datetime import datetime, date as Date
from typing import Optional, List, Tuple


class LLMExtractor:
    def __init__(self):
        """Initialize LLM client if possible; otherwise run in offline mode."""
        self.provider = "offline"
        self.model = "offline"
        self.client = None
        self._online_enabled = False

        # Import settings
        try:
            from config.settings import settings
            configured_provider = (settings.LLM_PROVIDER or "").lower()
            groq_key = settings.GROQ_API_KEY
            gemini_key = settings.GEMINI_API_KEY
            groq_model = getattr(settings, "GROQ_MODEL", "mixtral-8x7b-32768")
            gemini_model = getattr(settings, "GEMINI_MODEL", "gemini-pro")
        except Exception as e:
            print(f"⚠️  Warning: Could not load settings: {e}")
            configured_provider = os.getenv("LLM_PROVIDER", "").lower()
            groq_key = os.getenv("GROQ_API_KEY", "")
            gemini_key = os.getenv("GEMINI_API_KEY", "")
            groq_model = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
            gemini_model = os.getenv("GEMINI_MODEL", "gemini-pro")

        # Attempt to initialize selected provider; fall back to offline on any failure
        if configured_provider == "groq" and groq_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=groq_key)
                self.provider = "groq"
                self.model = groq_model
                self._online_enabled = True
                print(f"✅ Groq client initialized with model: {self.model}")
            except Exception as e:
                print(f"❌ Failed to initialize Groq; falling back to offline: {e}")
        elif configured_provider == "gemini" and gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                self.provider = "gemini"
                self.model = gemini_model
                self._online_enabled = True
                print(f"✅ Gemini client configured with model: {self.model}")
            except Exception as e:
                print(f"❌ Failed to initialize Gemini; falling back to offline: {e}")
        else:
            print("ℹ️  No valid LLM provider configured; running in offline mode")

        print(f"🤖 Effective provider: {self.provider}")

    def extract_structured_data(self, raw_text: str) -> dict:
        """Extract structured bank statement data; prefer online, otherwise offline rules."""
        print(f"📊 Extracting data using {self.provider}...")
        print(f"   Text length: {len(raw_text)} characters")

        # Limit text to avoid token limits
        max_chars = 15000
        if len(raw_text) > max_chars:
            print(f"   ⚠️  Truncating text from {len(raw_text)} to {max_chars} chars")
            raw_text = raw_text[:max_chars]

        if self._online_enabled and self.provider in {"groq", "gemini"}:
            prompt = self._build_prompt(raw_text)
            try:
                if self.provider == "groq":
                    content = self._query_groq(prompt)
                else:
                    content = self._query_gemini(prompt)
                json_data = self._clean_json_response(content)
                print("✅ Successfully extracted data via LLM")
                print(f"   Found {len(json_data.get('transactions', []))} transactions")
                return json_data
            except Exception as e:
                print(f"❌ LLM extraction failed: {e}; falling back to offline rules")

        # Offline extraction
        try:
            data = self._extract_with_rules(raw_text)
            print("✅ Successfully extracted data via offline rules")
            return data
        except Exception as e:
            print(f"❌ Offline rule extraction failed: {e}; returning dummy data")
            return self._get_dummy_data()

    def _build_prompt(self, raw_text: str) -> str:
        return f"""
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
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]

        if content.endswith("```"):
            content = content[:-3]

        content = content.strip()
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON parse error: {e}")
            # Remove any text before first {
            if "{" in content:
                content = content[content.index("{"):]
            if "}" in content:
                content = content[: content.rindex("}") + 1]
            return json.loads(content)

    def _extract_with_rules(self, raw_text: str) -> dict:
        """Extract statement structure using simple regex-based rules (offline mode)."""
        lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]

        # Header extraction heuristics
        def _find(patterns: List[str]) -> Optional[str]:
            for pat in patterns:
                for ln in lines:
                    m = re.search(pat, ln, flags=re.IGNORECASE)
                    if m:
                        grp = m.group(1).strip()
                        return grp
            return None

        account_holder = _find([r"account\s*holder[:\-]\s*(.+)", r"holder[:\-]\s*(.+)"])
        account_number = _find([r"account\s*number[:\-]\s*([\w\- ]+)", r"a/c\s*no[:\-]\s*([\w\- ]+)"])
        bank_name = _find([r"bank[:\-]\s*(.+)", r"(.+?)\s+bank\b"])
        ifsc = _find([r"ifsc[:\-]\s*([A-Z0-9]{5,})"])
        branch = _find([r"branch[:\-]\s*(.+)"])

        # Transaction extraction - lines starting with YYYY-MM-DD
        txn_pattern = re.compile(
            r"^(?P<date>\d{4}-\d{2}-\d{2})\s+(?P<desc>.+?)\s+(?P<amount1>[₹$]?[\d,]+(?:\.\d{1,2})?)?\s*(?P<amount2>[₹$]?[\d,]+(?:\.\d{1,2})?)?\s*(?P<balance>[₹$]?[\d,]+(?:\.\d{1,2})?)?$"
        )

        def _parse_amount(text: Optional[str]) -> float:
            if not text:
                return 0.0
            cleaned = re.sub(r"[₹$,\s]", "", text)
            try:
                return round(float(cleaned), 2)
            except Exception:
                return 0.0

        transactions = []
        opening_balance = 0.0
        closing_balance = 0.0

        ob_match = _find([r"opening\s*balance[:\-]\s*([₹$]?[\d,]+(?:\.\d{1,2})?)"])
        if ob_match:
            opening_balance = _parse_amount(ob_match)

        for ln in lines:
            m = txn_pattern.match(ln)
            if not m:
                continue
            dt = m.group("date")
            desc = m.group("desc")
            a1 = _parse_amount(m.group("amount1"))
            a2 = _parse_amount(m.group("amount2"))
            bal = _parse_amount(m.group("balance"))

            # Decide credit/debit by which amount is non-zero if both present assume a1=credit, a2=debit
            credit = a1 if a1 and not a2 else (a1 if (a1 and a2 == 0) else 0.0)
            debit = a2 if a2 and not a1 else (a2 if (a2 and a1 == 0) else 0.0)

            transactions.append(
                {
                    "date": dt,
                    "description": desc,
                    "credit": credit,
                    "debit": debit,
                    "balance": bal,
                    "ref": None,
                }
            )

        # If balances were not part of lines, compute running from opening_balance
        if transactions:
            running = opening_balance
            for t in transactions:
                if t["balance"] == 0.0:
                    running += t["credit"]
                    running -= t["debit"]
                    t["balance"] = round(running, 2)
                else:
                    running = t["balance"]
            closing_balance = transactions[-1]["balance"]

        header = {
            "bank_name": bank_name or "Unknown Bank",
            "account_holder": account_holder or "Unknown",
            "account_number": (account_number or "0000000000").replace(" ", ""),
            "ifsc": ifsc,
            "micr": None,
            "branch": branch,
            "statement_period": None,
            "address": None,
        }

        return {
            "header": header,
            "transactions": transactions or [
                {
                    "date": datetime.today().strftime("%Y-%m-%d"),
                    "description": "Parsed with offline rules",
                    "credit": 0.0,
                    "debit": 0.0,
                    "balance": opening_balance,
                    "ref": None,
                }
            ],
            "opening_balance": opening_balance,
            "closing_balance": closing_balance if transactions else opening_balance,
        }

    def _get_dummy_data(self) -> dict:
        """Return minimal valid data when all extraction fails."""
        today = datetime.today().strftime("%Y-%m-%d")
        return {
            "header": {
                "bank_name": "Unknown Bank",
                "account_holder": "Please Edit",
                "account_number": "0000000000",
                "ifsc": None,
                "micr": None,
                "branch": None,
                "statement_period": None,
                "address": None,
            },
            "transactions": [
                {
                    "date": today,
                    "description": "Dummy transaction - offline fallback",
                    "credit": 0.0,
                    "debit": 0.0,
                    "balance": 0.0,
                    "ref": None,
                }
            ],
            "opening_balance": 0.0,
            "closing_balance": 0.0,
        }