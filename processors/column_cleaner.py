from typing import Dict, List, Any
from models.statement_schema import BankStatement

class ColumnCleaner:
    CANONICAL_COLUMNS = {"date", "description", "credit", "debit", "balance", "ref"}
    
    COLUMN_MAPPINGS = {
        "particulars": "description",
        "narration": "description",
        "cheque no": "ref",
        "chq no": "ref",
        "reference": "ref",
        "withdrawal": "debit",
        "deposit": "credit",
    }
    
    @staticmethod
    def clean(statement: BankStatement, extracted_data: dict) -> BankStatement:
        """Remove extra columns and map known aliases"""
        
        if "extra_columns" in extracted_data:
            # Store extra columns separately
            statement.extra_columns = extracted_data["extra_columns"]
        
        return statement