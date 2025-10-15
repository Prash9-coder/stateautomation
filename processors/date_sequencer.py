from datetime import date, timedelta
from typing import List
from models.statement_schema import Transaction
import numpy as np

class DateSequencer:
    @staticmethod
    def sequence_dates(
        transactions: List[Transaction],
        start_date: date,
        end_date: date,
        method: str = "preserve_spacing"
    ) -> List[Transaction]:
        """
        Reassign transaction dates while preserving relative spacing
        """
        if not transactions:
            return transactions
        
        # Store original dates for audit
        for txn in transactions:
            txn.original_date = txn.date
        
        if method == "preserve_spacing":
            return DateSequencer._preserve_spacing(transactions, start_date, end_date)
        else:
            return DateSequencer._uniform_distribution(transactions, start_date, end_date)
    
    @staticmethod
    def _preserve_spacing(
        transactions: List[Transaction],
        start_date: date,
        end_date: date
    ) -> List[Transaction]:
        """Scale original date intervals to fit new range"""
        original_dates = [txn.date for txn in transactions]
        
        if len(set(original_dates)) == 1:  # All dates identical
            return DateSequencer._uniform_distribution(transactions, start_date, end_date)
        
        # Convert dates to numeric values (days since min date)
        min_orig = min(original_dates)
        max_orig = max(original_dates)
        
        orig_range = (max_orig - min_orig).days
        new_range = (end_date - start_date).days
        
        if orig_range == 0:
            return DateSequencer._uniform_distribution(transactions, start_date, end_date)
        
        scale_factor = new_range / orig_range
        
        for txn in transactions:
            days_from_start = (txn.date - min_orig).days
            new_days = int(days_from_start * scale_factor)
            txn.date = start_date + timedelta(days=new_days)
        
        return transactions
    
    @staticmethod
    def _uniform_distribution(
        transactions: List[Transaction],
        start_date: date,
        end_date: date
    ) -> List[Transaction]:
        """Distribute transactions uniformly across date range"""
        num_txns = len(transactions)
        total_days = (end_date - start_date).days
        
        if num_txns == 1:
            transactions[0].date = start_date
        else:
            day_interval = total_days / (num_txns - 1)
            
            for i, txn in enumerate(transactions):
                days_offset = int(i * day_interval)
                txn.date = start_date + timedelta(days=days_offset)
        
        return transactions