"""
Input validation and data sanitization utilities
"""

import re
from datetime import date, datetime
from typing import Optional, Tuple
from pathlib import Path
import magic  # python-magic for file type detection

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def validate_file_upload(file_path: str, max_size_mb: int = 50) -> Tuple[bool, str]:
    """
    Validate uploaded file type and size
    
    Args:
        file_path: Path to uploaded file
        max_size_mb: Maximum file size in MB
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    path = Path(file_path)
    
    # Check if file exists
    if not path.exists():
        return False, "File does not exist"
    
    # Check file size
    file_size_mb = path.stat().st_size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        return False, f"File size ({file_size_mb:.2f}MB) exceeds limit ({max_size_mb}MB)"
    
    # Check file extension
    allowed_extensions = {'.pdf', '.docx'}
    if path.suffix.lower() not in allowed_extensions:
        return False, f"File type {path.suffix} not allowed. Use PDF or DOCX"
    
    # Validate actual file type (not just extension)
    try:
        mime = magic.Magic(mime=True)
        file_type = mime.from_file(str(path))
        
        allowed_mimes = {
            'application/pdf',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword'
        }
        
        if file_type not in allowed_mimes:
            return False, f"Invalid file type: {file_type}"
    except Exception as e:
        # If magic fails, rely on extension check
        pass
    
    return True, "File is valid"


def validate_date_range(start_date: date, end_date: date) -> Tuple[bool, str]:
    """
    Validate date range for transaction sequencing
    
    Args:
        start_date: Start date
        end_date: End date
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(start_date, date) or not isinstance(end_date, date):
        return False, "Dates must be date objects"
    
    if start_date > end_date:
        return False, "Start date must be before or equal to end date"
    
    if end_date > date.today():
        return False, "End date cannot be in the future"
    
    # Check if range is reasonable (not more than 10 years)
    days_diff = (end_date - start_date).days
    if days_diff > 3650:  # 10 years
        return False, "Date range too large (max 10 years)"
    
    if days_diff < 0:
        return False, "Invalid date range"
    
    return True, "Date range is valid"


def validate_account_number(account_number: str) -> Tuple[bool, str]:
    """
    Validate bank account number format
    
    Args:
        account_number: Account number string
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not account_number:
        return False, "Account number is required"
    
    # Remove spaces and special characters
    clean_number = re.sub(r'[\s\-]', '', account_number)
    
    # Check length (typically 9-18 digits for Indian banks)
    if len(clean_number) < 9 or len(clean_number) > 18:
        return False, "Account number must be 9-18 digits"
    
    # Check if only digits
    if not clean_number.isdigit():
        return False, "Account number must contain only digits"
    
    return True, "Account number is valid"


def validate_ifsc_code(ifsc: str) -> Tuple[bool, str]:
    """
    Validate IFSC code format (Indian banking)
    
    Args:
        ifsc: IFSC code string
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not ifsc:
        return True, "IFSC is optional"  # IFSC is optional
    
    # IFSC format: 4 letters (bank code) + 0 + 6 alphanumeric (branch code)
    # Example: SBIN0001234
    ifsc_pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
    
    if not re.match(ifsc_pattern, ifsc.upper()):
        return False, "Invalid IFSC format. Expected: XXXX0XXXXXX (e.g., SBIN0001234)"
    
    return True, "IFSC code is valid"


def validate_micr_code(micr: str) -> Tuple[bool, str]:
    """
    Validate MICR code format
    
    Args:
        micr: MICR code string
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not micr:
        return True, "MICR is optional"
    
    # MICR is 9 digits
    micr_clean = re.sub(r'[\s\-]', '', micr)
    
    if len(micr_clean) != 9:
        return False, "MICR code must be 9 digits"
    
    if not micr_clean.isdigit():
        return False, "MICR code must contain only digits"
    
    return True, "MICR code is valid"


def validate_transaction_data(transaction: dict) -> Tuple[bool, str]:
    """
    Validate individual transaction data
    
    Args:
        transaction: Transaction dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ['date', 'description']
    
    # Check required fields
    for field in required_fields:
        if field not in transaction:
            return False, f"Missing required field: {field}"
    
    # Validate date
    try:
        if isinstance(transaction['date'], str):
            datetime.strptime(transaction['date'], '%Y-%m-%d')
    except ValueError:
        return False, "Invalid date format. Use YYYY-MM-DD"
    
    # Validate amounts
    credit = transaction.get('credit', 0)
    debit = transaction.get('debit', 0)
    
    if credit < 0 or debit < 0:
        return False, "Credit and debit amounts cannot be negative"
    
    if credit > 0 and debit > 0:
        return False, "Transaction cannot have both credit and debit"
    
    # Validate description
    if not transaction.get('description', '').strip():
        return False, "Description cannot be empty"
    
    if len(transaction['description']) > 500:
        return False, "Description too long (max 500 characters)"
    
    return True, "Transaction data is valid"


def sanitize_amount(amount: any) -> float:
    """
    Sanitize and convert amount to float
    
    Args:
        amount: Amount in various formats (string, int, float)
    
    Returns:
        Float amount rounded to 2 decimal places
    """
    if amount is None:
        return 0.0
    
    # Handle string amounts
    if isinstance(amount, str):
        # Remove currency symbols and whitespace
        amount = re.sub(r'[₹$,\s]', '', amount)
        
        # Handle empty string
        if not amount:
            return 0.0
        
        try:
            amount = float(amount)
        except ValueError:
            return 0.0
    
    # Convert to float and round
    try:
        return round(float(amount), 2)
    except (ValueError, TypeError):
        return 0.0


def sanitize_string(text: str, max_length: int = 500) -> str:
    """
    Sanitize string input
    
    Args:
        text: Input text
        max_length: Maximum allowed length
    
    Returns:
        Sanitized string
    """
    if not text:
        return ""
    
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # Trim whitespace
    text = text.strip()
    
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    
    return text


def validate_edit_request(edit_data: dict) -> Tuple[bool, str]:
    """
    Validate complete edit request
    
    Args:
        edit_data: Edit request dictionary
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    # Validate account number if provided
    if edit_data.get('account_number'):
        is_valid, msg = validate_account_number(edit_data['account_number'])
        if not is_valid:
            return False, msg
    
    # Validate IFSC if provided
    if edit_data.get('ifsc'):
        is_valid, msg = validate_ifsc_code(edit_data['ifsc'])
        if not is_valid:
            return False, msg
    
    # Validate MICR if provided
    if edit_data.get('micr'):
        is_valid, msg = validate_micr_code(edit_data['micr'])
        if not is_valid:
            return False, msg
    
    # Validate date range if sequencing is enabled
    if edit_data.get('apply_date_sequencing'):
        start = edit_data.get('start_date')
        end = edit_data.get('end_date')
        
        if not start or not end:
            return False, "Start and end dates required for date sequencing"
        
        # Convert string dates if needed
        if isinstance(start, str):
            try:
                start = datetime.strptime(start, '%Y-%m-%d').date()
            except ValueError:
                return False, "Invalid start date format"
        
        if isinstance(end, str):
            try:
                end = datetime.strptime(end, '%Y-%m-%d').date()
            except ValueError:
                return False, "Invalid end date format"
        
        is_valid, msg = validate_date_range(start, end)
        if not is_valid:
            return False, msg
    
    # Validate salary amount if provided
    if edit_data.get('salary_amount'):
        amount = sanitize_amount(edit_data['salary_amount'])
        if amount <= 0:
            return False, "Salary amount must be positive"
        if amount > 10000000:  # 1 crore
            return False, "Salary amount seems unreasonably high"
    
    # Validate transaction edits if provided
    if edit_data.get('transaction_edits'):
        for txn in edit_data['transaction_edits']:
            is_valid, msg = validate_transaction_data(txn)
            if not is_valid:
                return False, f"Invalid transaction: {msg}"
    
    return True, "Edit request is valid"