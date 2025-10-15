"""
Output generators for creating formatted bank statements
"""

from .pdf_generator import PDFGenerator
from .docx_generator import DOCXGenerator

__all__ = [
    'PDFGenerator',
    'DOCXGenerator'
]


def get_generator(format_type: str):
    """
    Factory function to get appropriate generator based on format
    
    Args:
        format_type: Output format ('pdf' or 'docx')
    
    Returns:
        Generator instance
    
    Raises:
        ValueError: If format is not supported
    """
    format_type = format_type.lower()
    
    if format_type == 'pdf':
        return PDFGenerator()
    elif format_type in ['docx', 'doc']:
        return DOCXGenerator()
    else:
        raise ValueError(f"Unsupported format: {format_type}")


class GeneratorBase:
    """
    Base class for all generators with common functionality
    """
    
    def format_currency(self, amount: float, currency_symbol: str = '₹') -> str:
        """Format amount as currency string"""
        return f"{currency_symbol}{amount:,.2f}"
    
    def format_date(self, date_obj, format_str: str = '%d-%m-%Y') -> str:
        """Format date object as string"""
        return date_obj.strftime(format_str)
    
    def truncate_text(self, text: str, max_length: int = 40) -> str:
        """Truncate text to max length with ellipsis"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + '...'


__all__.append('GeneratorBase')