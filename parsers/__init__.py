"""
Parsers for extracting data from various bank statement formats
"""

from .pdf_parser import PDFParser
from .docx_parser import DOCXParser
from .ocr_handler import OCRHandler
from .llm_extractor import LLMExtractor

__all__ = [
    'PDFParser',
    'DOCXParser',
    'OCRHandler',
    'LLMExtractor'
]


def get_parser(file_path: str):
    """
    Factory function to get appropriate parser based on file extension
    
    Args:
        file_path: Path to the statement file
    
    Returns:
        Parser instance (PDFParser or DOCXParser)
    
    Raises:
        ValueError: If file type is not supported
    """
    from pathlib import Path
    
    ext = Path(file_path).suffix.lower()
    
    if ext == '.pdf':
        return PDFParser()
    elif ext in ['.docx', '.doc']:
        return DOCXParser()
    else:
        raise ValueError(f"Unsupported file type: {ext}")