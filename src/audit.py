"""Audit trail logging system for Performance Insight Explorer.
Records all data lifecycle events, user mappings, quality checks, metrics, and exports.
"""
import datetime
import os
from typing import List, Dict, Any, Optional
import pandas as pd


class AuditLogger:
    """Thread-safe and session-safe audit logger."""
    
    def __init__(self):
        self.events: List[Dict[str, Any]] = []

    def log(
        self,
        event_type: str,
        description: str,
        filename: str = "",
        sheet_name: str = "",
        row_count: Optional[int] = None,
        col_count: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        user_notes: str = ""
    ):
        now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        entry = {
            "timestamp": now_utc,
            "event_type": event_type,
            "description": description,
            "filename": filename,
            "sheet_name": sheet_name,
            "row_count": str(row_count) if row_count is not None else "",
            "col_count": str(col_count) if col_count is not None else "",
            "details": str(details) if details else "",
            "user_notes": user_notes
        }
        self.events.append(entry)

    def get_dataframe(self) -> pd.DataFrame:
        if not self.events:
            return pd.DataFrame(columns=[
                "timestamp", "event_type", "description", "filename",
                "sheet_name", "row_count", "col_count", "details", "user_notes"
            ])
        return pd.DataFrame(self.events)

    def to_csv(self, filepath: Optional[str] = None) -> str:
        df = self.get_dataframe()
        if filepath:
            os.makedirs(os.path.dirname(filepath), exist_ok=True) if os.path.dirname(filepath) else None
            df.to_csv(filepath, index=False, encoding="utf-8")
            return filepath
        return df.to_csv(index=False, encoding="utf-8")

    def clear(self):
        self.events = []
