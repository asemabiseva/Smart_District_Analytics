from __future__ import annotations

from pathlib import Path
import pandas as pd
import streamlit as st


@st.cache_data(ttl=3600)  # Cache for 1 hour to reduce repeated file reads
def safe_read_csv(path: str, **kwargs) -> pd.DataFrame:
    """Load CSV file with caching and error handling.
    
    Args:
        path: Path to CSV file relative to project root
        **kwargs: Additional arguments to pass to pd.read_csv
    
    Returns:
        Loaded DataFrame or empty DataFrame on error
    
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    try:
        return pd.read_csv(path, **kwargs)
    except FileNotFoundError as exc:
        st.error(
            f"❌ Missing dataset: `{path}`  \n"
            f"Please ensure the file exists in the `datasets/` folder."
        )
        raise exc
    except Exception as exc:
        st.error(
            f"⚠️ Error reading `{path}`: {str(exc)[:100]}  \n"
            f"Check file format and permissions."
        )
        raise exc


def max_dataset_mtime(dataset_paths: list[str]) -> str:
    """Get the most recent modification time across dataset files.
    
    Args:
        dataset_paths: List of relative file paths
    
    Returns:
        Formatted timestamp string or "unknown" if no files found
    """
    mtimes = []
    for rel_path in dataset_paths:
        p = Path(rel_path)
        if p.exists():
            mtimes.append(p.stat().st_mtime)
    if not mtimes:
        return "unknown"
    return pd.to_datetime(max(mtimes), unit="s").strftime("%Y-%m-%d %H:%M")

