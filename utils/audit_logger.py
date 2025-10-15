import json
from datetime import datetime
from typing import Any
from models.statement_schema import AuditLogEntry
from config.settings import settings

class AuditLogger:
    def __init__(self, log_file: str = None):
        self.log_file = log_file or settings.AUDIT_LOG_FILE
        self.entries = []
    
    def log_change(
        self,
        field_name: str,
        old_value: Any,
        new_value: Any,
        change_type: str,
        transaction_index: int = None,
        user_id: str = "system"
    ):
        """Log a single change"""
        entry = AuditLogEntry(
            user_id=user_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            transaction_index=transaction_index,
            change_type=change_type
        )
        self.entries.append(entry)
    
    def save(self):
        """Save all entries to JSONL file"""
        with open(self.log_file, 'a') as f:
            for entry in self.entries:
                f.write(entry.model_dump_json() + "\n")
    
    def get_summary(self) -> dict:
        """Get summary of all changes"""
        # Use JSON mode to ensure datetime fields are serialized
        return {
            "total_changes": len(self.entries),
            "changes_by_type": self._count_by_type(),
            "changes": [e.model_dump(mode='json') for e in self.entries]
        }
    
    def _count_by_type(self) -> dict:
        counts = {}
        for entry in self.entries:
            counts[entry.change_type] = counts.get(entry.change_type, 0) + 1
        return counts