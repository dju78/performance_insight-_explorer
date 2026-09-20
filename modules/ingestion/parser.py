"""Comprehensive Data Ingestion Engine for Performance Insight Explorer.
Supports CSV, XLSX/XLS, Parquet, JSON, chunked processing, configurable delimiters and encodings.
Maintains pristine original data and records all transformations.
"""
import io
import json
import os
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd


def detect_file_format(filename: str) -> str:
    """Identify file format from extension."""
    ext = os.path.splitext(filename)[1].lower()
    mapping = {
        ".csv": "csv",
        ".tsv": "tsv",
        ".txt": "csv",
        ".xlsx": "excel",
        ".xls": "excel",
        ".parquet": "parquet",
        ".pq": "parquet",
        ".json": "json"
    }
    return mapping.get(ext, "unknown")


def read_file_contents(
    file_bytes: bytes,
    filename: str,
    sheet_name: Optional[str] = None,
    delimiter: Optional[str] = None,
    encoding: Optional[str] = None,
    chunk_size: Optional[int] = None
) -> Tuple[Optional[pd.DataFrame], List[str], Dict[str, Any]]:
    """Parse raw bytes into a pandas DataFrame.
    Returns (dataframe, list_of_sheets_if_excel, metadata_dict).
    """
    fmt = detect_file_format(filename)
    sheets: List[str] = []
    meta: Dict[str, Any] = {
        "filename": filename,
        "format": fmt,
        "file_size_bytes": len(file_bytes),
        "file_size_mb": round(len(file_bytes) / (1024 * 1024), 3),
        "encoding_used": encoding or "auto",
        "delimiter_used": delimiter or "auto",
        "active_sheet": sheet_name or ""
    }

    try:
        if fmt == "excel":
            excel_bio = io.BytesIO(file_bytes)
            xl = pd.ExcelFile(excel_bio)
            sheets = xl.sheet_names
            target_sheet = sheet_name if sheet_name in sheets else sheets[0]
            meta["active_sheet"] = target_sheet
            df = pd.read_excel(excel_bio, sheet_name=target_sheet)
            return df, sheets, meta

        elif fmt in ["csv", "tsv"]:
            encodings_to_try = [encoding] if encoding else ["utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"]
            delimiters_to_try = [delimiter] if delimiter else [",", "\t", ";", "|"]
            
            df = None
            used_enc = ""
            used_delim = ""
            
            for enc in encodings_to_try:
                for d in delimiters_to_try:
                    try:
                        bio = io.BytesIO(file_bytes)
                        if chunk_size and chunk_size > 0:
                            chunks = pd.read_csv(bio, encoding=enc, sep=d, chunksize=chunk_size)
                            df = pd.concat(chunks, ignore_index=True)
                        else:
                            df = pd.read_csv(bio, encoding=enc, sep=d)
                        
                        # Basic validity check: must have > 1 column or 1 row
                        if len(df.columns) > 1 or len(df) > 0:
                            used_enc = enc
                            used_delim = d
                            break
                    except Exception:
                        continue
                if df is not None:
                    break
            
            if df is None:
                # Fallback simple utf-8
                bio = io.BytesIO(file_bytes)
                df = pd.read_csv(bio, encoding="utf-8", errors="replace")
                used_enc = "utf-8 (replace)"
                used_delim = ","

            meta["encoding_used"] = used_enc
            meta["delimiter_used"] = used_delim
            return df, ["Default"], meta

        elif fmt == "parquet":
            bio = io.BytesIO(file_bytes)
            df = pd.read_parquet(bio)
            return df, ["Default"], meta

        elif fmt == "json":
            bio = io.BytesIO(file_bytes)
            # Try records orientation first
            try:
                df = pd.read_json(bio, orient="records")
            except Exception:
                bio.seek(0)
                df = pd.read_json(bio)
            return df, ["Default"], meta

        else:
            # Attempt generic text/csv parse
            bio = io.BytesIO(file_bytes)
            df = pd.read_csv(bio, encoding="utf-8", errors="replace")
            return df, ["Default"], meta

    except Exception as e:
        meta["error"] = str(e)
        return None, [], meta


def apply_column_transformation(
    df: pd.DataFrame,
    transform_type: str,
    params: Dict[str, Any]
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Apply an explicit transformation and return (updated_df, audit_record).
    Never silently changes data.
    """
    out_df = df.copy()
    audit_entry = {
        "transform_type": transform_type,
        "params": params,
        "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if transform_type == "rename_column":
        old_name = params.get("old_name")
        new_name = params.get("new_name")
        if old_name in out_df.columns and new_name:
            out_df = out_df.rename(columns={old_name: new_name})
            audit_entry["details"] = f"Renamed column '{old_name}' to '{new_name}'"

    elif transform_type == "cast_type":
        col = params.get("column")
        target_type = params.get("target_type")  # numeric, datetime, string, category
        if col in out_df.columns:
            if target_type == "numeric":
                out_df[col] = pd.to_numeric(out_df[col], errors="coerce")
            elif target_type == "datetime":
                out_df[col] = pd.to_datetime(out_df[col], errors="coerce")
            elif target_type == "string":
                out_df[col] = out_df[col].astype(str).replace({"nan": None, "None": None})
            elif target_type == "category":
                out_df[col] = out_df[col].astype("category")
            audit_entry["details"] = f"Casted column '{col}' to '{target_type}'"

    elif transform_type == "drop_column":
        col = params.get("column")
        if col in out_df.columns:
            out_df = out_df.drop(columns=[col])
            audit_entry["details"] = f"Dropped column '{col}'"

    elif transform_type == "filter_rows":
        col = params.get("column")
        allowed_values = params.get("allowed_values", [])
        if col in out_df.columns and allowed_values:
            before_len = len(out_df)
            out_df = out_df[out_df[col].isin(allowed_values)]
            audit_entry["details"] = f"Filtered '{col}' to {len(allowed_values)} values (Rows {before_len:,} -> {len(out_df):,})"

    return out_df, audit_entry
