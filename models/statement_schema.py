from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import date as DateType, datetime
from enum import Enum

class TransactionType(str, Enum):
    CREDIT = "Credit"
    DEBIT = "Debit"

class Transaction(BaseModel):
    date: DateType
    description: str
    credit: float = 0.0
    debit: float = 0.0
    balance: float = 0.0
    ref: Optional[str] = None
    original_date: Optional[DateType] = None  # Line 17 - Fixed!
    
    @field_validator('credit', 'debit', 'balance')
    @classmethod
    def round_amounts(cls, v):
        return round(v, 2)

class Header(BaseModel):
    bank_name: Optional[str] = None
    account_holder: str
    account_number: str
    ifsc: Optional[str] = None
    micr: Optional[str] = None
    branch: Optional[str] = None
    statement_period: Optional[str] = None
    address: Optional[str] = None

class PageRange(BaseModel):
    start: int
    end: int
    page_type: str = "statement"  # statement, attachment, promotional, blank

class BankStatement(BaseModel):
    header: Header
    transactions: List[Transaction]
    original_page_ranges: List[PageRange] = []
    extra_columns: Dict[str, List[Any]] = {}
    opening_balance: float = 0.0
    closing_balance: float = 0.0
    total_credits: float = 0.0
    total_debits: float = 0.0
    
class EditRequest(BaseModel):
    # Header edits
    account_holder: Optional[str] = None
    account_number: Optional[str] = None
    ifsc: Optional[str] = None
    micr: Optional[str] = None
    branch: Optional[str] = None
    
    # Transaction edits
    transaction_edits: Optional[List[Dict]] = None
    
    # Date sequencing
    start_date: Optional[DateType] = None
    end_date: Optional[DateType] = None
    apply_date_sequencing: bool = False
    date_distribution_method: str = "preserve_spacing"  # or "uniform"
    
    # Salary/specific entry edits
    salary_amount: Optional[float] = None
    salary_date: Optional[DateType] = None
    salary_description: str = "Salary Credit"

class AuditLogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    user_id: str = "system"
    field_name: str
    old_value: Any
    new_value: Any
    transaction_index: Optional[int] = None
    change_type: str  # "header", "transaction", "calculation"