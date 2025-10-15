from typing import List
from models.statement_schema import Transaction, BankStatement

class BalanceCalculator:
    @staticmethod
    def recalculate(statement: BankStatement) -> BankStatement:
        """Recalculate all running balances and totals"""
        running_balance = statement.opening_balance
        total_credits = 0.0
        total_debits = 0.0
        
        for txn in statement.transactions:
            # Add credits, subtract debits
            running_balance += txn.credit
            running_balance -= txn.debit
            
            txn.balance = round(running_balance, 2)
            total_credits += txn.credit
            total_debits += txn.debit
        
        statement.total_credits = round(total_credits, 2)
        statement.total_debits = round(total_debits, 2)
        statement.closing_balance = round(running_balance, 2)
        
        return statement