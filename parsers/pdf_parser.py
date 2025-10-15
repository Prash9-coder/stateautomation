import pdfplumber
import PyPDF2
import fitz  # PyMuPDF
from typing import Tuple, List
from parsers.llm_extractor import LLMExtractor
from parsers.ocr_handler import OCRHandler
from models.statement_schema import BankStatement, PageRange

class PDFParser:
    def __init__(self):
        self.llm_extractor = LLMExtractor()
        self.ocr_handler = OCRHandler()
    
    def extract_text(self, file_path: str) -> Tuple[str, List[PageRange]]:
        """Extract text from PDF, use OCR if needed"""
        text = ""
        page_ranges = []
        
        # Try text extraction first
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)
            current_range = None
            
            for i, page in enumerate(pdf.pages, 1):
                page_text = page.extract_text() or ""
                
                # Detect page type
                page_type = self._classify_page(page_text)
                
                if current_range and current_range.page_type == page_type:
                    current_range.end = i
                else:
                    if current_range:
                        page_ranges.append(current_range)
                    current_range = PageRange(start=i, end=i, page_type=page_type)
                
                if page_type == "statement":
                    if len(page_text.strip()) < 50:  # Likely scanned
                        page_text = self.ocr_handler.extract_from_page(file_path, i-1)
                    text += page_text + "\n\n"
            
            if current_range:
                page_ranges.append(current_range)
        
        return text, page_ranges
    
    def _classify_page(self, text: str) -> str:
        """Classify page type using keywords"""
        text_lower = text.lower()
        
        if len(text.strip()) < 20:
            return "blank"
        
        statement_keywords = ["account number", "ifsc", "transaction", "debit", "credit", "balance"]
        if any(kw in text_lower for kw in statement_keywords):
            return "statement"
        
        promo_keywords = ["offer", "advertisement", "apply now", "terms and conditions"]
        if any(kw in text_lower for kw in promo_keywords):
            return "promotional"
        
        return "attachment"
    
    def parse(self, file_path: str) -> BankStatement:
        """Full PDF parsing pipeline"""
        raw_text, page_ranges = self.extract_text(file_path)
        extracted_data = self.llm_extractor.extract_structured_data(raw_text)
        
        # Convert to BankStatement model
        statement = BankStatement(**extracted_data)
        statement.original_page_ranges = page_ranges
        
        return statement