"""
Processing modules for statement manipulation and calculations
"""

from .date_sequencer import DateSequencer
from .balance_calculator import BalanceCalculator
from .column_cleaner import ColumnCleaner
from .page_detector import PageDetector

__all__ = [
    'DateSequencer',
    'BalanceCalculator',
    'ColumnCleaner',
    'PageDetector'
]


class StatementProcessor:
    """
    Unified processor that combines all processing steps
    """
    
    def __init__(self):
        self.date_sequencer = DateSequencer()
        self.balance_calculator = BalanceCalculator()
        self.column_cleaner = ColumnCleaner()
        self.page_detector = PageDetector()
    
    def process_statement(self, statement, edit_request=None):
        """
        Apply all processing steps to a statement
        
        Args:
            statement: BankStatement object
            edit_request: EditRequest object (optional)
        
        Returns:
            Processed BankStatement
        """
        from models.statement_schema import BankStatement, EditRequest
        
        # Clean columns
        statement = self.column_cleaner.clean(statement, {})
        
        # Filter pages
        if statement.original_page_ranges:
            relevant_pages = self.page_detector.filter_relevant_pages(
                statement.original_page_ranges
            )
            statement.original_page_ranges = relevant_pages
        
        # Apply date sequencing if requested
        if edit_request and edit_request.apply_date_sequencing:
            if edit_request.start_date and edit_request.end_date:
                statement.transactions = self.date_sequencer.sequence_dates(
                    statement.transactions,
                    edit_request.start_date,
                    edit_request.end_date,
                    edit_request.date_distribution_method
                )
        
        # Recalculate balances
        statement = self.balance_calculator.recalculate(statement)
        
        return statement


__all__.append('StatementProcessor')