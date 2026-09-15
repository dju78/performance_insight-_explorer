"""Audit trail logging system for Performance Insight Explorer.
Records all data lifecycle events, user mappings, quality checks, metrics, and exports.
"""
import datetime
import os
import json
import logging
from typing import List, Dict, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


class AuditLogger:
    """Thread-safe, session-safe, and fail-safe audit logger."""
    
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
        user_notes: str = "",
        *args,
        **kwargs
    ):
        """Log an event to the audit trail safely without failing callers."""
        try:
            now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
            
            # Merge explicit details with extra kwargs
            extra_details: Dict[str, Any] = {}
            if details and isinstance(details, dict):
                extra_details.update(details)
            elif details:
                extra_details["details"] = str(details)

            # Handle alias keyword arguments
            if "rows" in kwargs and row_count is None:
                row_count = kwargs.pop("rows")
            if "cols" in kwargs and col_count is None:
                col_count = kwargs.pop("cols")
            if "worksheet" in kwargs and not sheet_name:
                sheet_name = str(kwargs.pop("worksheet"))
            if "file" in kwargs and not filename:
                filename = str(kwargs.pop("file"))

            # Capture remaining kwargs (e.g. role, dataset_id, health_score, etc.)
            for k, v in kwargs.items():
                extra_details[k] = v

            details_str = json.dumps(extra_details, default=str) if extra_details else ""

            entry = {
                "timestamp": now_utc,
                "event_type": str(event_type),
                "description": str(description),
                "filename": str(filename),
                "sheet_name": str(sheet_name),
                "row_count": str(row_count) if row_count is not None else "",
                "col_count": str(col_count) if col_count is not None else "",
                "details": details_str,
                "user_notes": str(user_notes)
            }
            self.events.append(entry)
        except Exception as e:
            logger.warning(f"AuditLogger.log non-fatal exception: {e}")

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
