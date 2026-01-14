from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_dataset() -> pd.DataFrame:
    """
    Placeholder loader.

    Stage 2 will implement:
      - kagglehub.dataset_download(...)
      - caching with st.cache_data
      - schema validation
    """
    return pd.DataFrame()


def get_data_dir() -> Path:
    """Return local data directory path (default ./data)."""
    return Path("data")
