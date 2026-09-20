"""Enterprise Security, Privacy and Governance Module.
Implements:
- Spreadsheet formula injection protection
- Small-cell statistical suppression (GDPR / re-identification protection)
- Role-Based Access Control (RBAC)
- Audit log integrity hashing
"""
import hashlib
import re
from typing import Any, Dict, List, Optional, Union
import pandas as pd
from core.constants import UserRole


# Characters that trigger formula execution in Excel / Calc
DANGEROUS_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r", "\n")


def is_index_like_column(col_name: Any, series: Optional[pd.Series] = None) -> bool:
    """Identify if a column is an unnamed index, sequential row counter, or index-like artifact.
    Used to exclude such columns from automatic analytical recommendations (trends, metrics, drivers).
    """
    if col_name is None:
        return False
    name_str = str(col_name).strip()
    
    # 1. Matches Unnamed: 0, Unnamed: 1, etc.
    if re.match(r"^unnamed:\s*\d+", name_str, re.IGNORECASE) or name_str.lower().startswith("unnamed:"):
        return True
        
    # 2. Matches common system index names
    if name_str.lower() in ["index", "idx", "row_id", "row_num", "row_number", "level_0", "__index_level_0__"]:
        return True
        
    # 3. If series is provided, check if it is a monotonic 0-based or 1-based sequential integer series
    if series is not None and len(series) > 2:
        if pd.api.types.is_numeric_dtype(series):
            valid_vals = series.dropna()
            if len(valid_vals) > 2:
                first_val = valid_vals.iloc[0]
                last_val = valid_vals.iloc[-1]
                if first_val in [0, 1] and (last_val - first_val == len(valid_vals) - 1):
                    if valid_vals.is_monotonic_increasing:
                        diffs = valid_vals.diff().iloc[1:]
                        if (diffs == 1).all():
                            # If name has id/num/index or is purely numeric
                            if any(k in name_str.lower() for k in ["id", "no", "num", "seq", "index", "idx", "unnamed"]) or name_str.isdigit():
                                return True
                                
    return False



def sanitize_for_spreadsheet(value: Any) -> Any:
    """Sanitize cell value against CSV / Excel Formula Injection (CWE-1236).
    If a string starts with =, +, -, @, or tab/return, prepends an apostrophe '.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        return value
    
    val_str = str(value)
    if val_str.startswith(DANGEROUS_FORMULA_PREFIXES):
        # Escape leading formula trigger
        return "'" + val_str
    return val_str


def sanitize_dataframe_for_export(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize all text/object columns in a dataframe prior to CSV or Excel export."""
    if df is None or len(df) == 0:
        return df
    
    sanitized = df.copy()
    for col in sanitized.select_dtypes(include=["object", "string"]).columns:
        sanitized[col] = sanitized[col].apply(sanitize_for_spreadsheet)
    return sanitized


def apply_statistical_suppression(
    df: pd.DataFrame,
    count_column: str,
    threshold: int = 5,
    replacement: str = "< 5 (Suppressed)"
) -> pd.DataFrame:
    """Apply statistical disclosure control / suppression for small group counts (< 5).
    Protects against individual re-identification in sensitive healthcare or public-sector datasets.
    """
    if df is None or count_column not in df.columns:
        return df
    
    out_df = df.copy()
    # Check if numeric
    if pd.api.types.is_numeric_dtype(out_df[count_column]):
        mask = (out_df[count_column] > 0) & (out_df[count_column] < threshold)
        if mask.any():
            out_df[count_column] = out_df[count_column].astype(object)
            out_df.loc[mask, count_column] = replacement
    return out_df


def check_role_permission(user_role: Union[UserRole, str], required_role: UserRole) -> bool:
    """Check if the user's role satisfies the required permission level.
    Hierarchy: Administrator > Lead Analyst > Executive Viewer.
    """
    role_weights = {
        UserRole.ADMIN.value: 30,
        UserRole.ANALYST.value: 20,
        UserRole.VIEWER.value: 10,
        "Administrator": 30,
        "Lead Analyst": 20,
        "Executive Viewer": 10
    }
    
    user_str = user_role.value if isinstance(user_role, UserRole) else str(user_role)
    req_str = required_role.value if isinstance(required_role, UserRole) else str(required_role)
    
    user_w = role_weights.get(user_str, 10)
    req_w = role_weights.get(req_str, 10)
    
    return user_w >= req_w


def compute_audit_hash(prev_hash: str, timestamp: str, event_type: str, details_str: str) -> str:
    """Compute a tamper-evident SHA-256 chain hash for an audit log entry."""
    payload = f"{prev_hash}::{timestamp}::{event_type}::{details_str}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
