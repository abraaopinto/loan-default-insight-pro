from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS: list[str] = [
    "LoanID",
    "Age",
    "Income",
    "LoanAmount",
    "CreditScore",
    "MonthsEmployed",
    "NumCreditLines",
    "InterestRate",
    "LoanTerm",
    "DTIRatio",
    "Education",
    "EmploymentType",
    "MaritalStatus",
    "HasMortgage",
    "HasDependents",
    "LoanPurpose",
    "HasCoSigner",
    "Default",
]


def get_data_dir() -> Path:
    """
    Resolve the local data directory.
    Priority:
      1) DATA_DIR env (from .env)
      2) ./data
    """
    return Path(os.getenv("DATA_DIR", "data")).resolve()


def _validate_schema(df: pd.DataFrame, required: Iterable[str]) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset schema mismatch. Missing columns: {missing}")


def normalize_binary_yes_no(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize Yes/No columns to 1/0.
    """
    yn_map = {"Yes": 1, "No": 0}
    for col in ["HasMortgage", "HasDependents", "HasCoSigner"]:
        df[col] = df[col].astype(str).str.strip().map(yn_map)

        # Fail-fast if unexpected values exist
        if df[col].isna().any():
            raise ValueError(
                f"Unexpected values in {col}. Expected only Yes/No. "
                "Tip: inspect raw values with df[col].value_counts()."
            )
        df[col] = df[col].astype(int)

    return df


def _find_csv(data_dir: Path, filename: str) -> Path | None:
    direct = data_dir / filename
    if direct.exists():
        return direct

    target = filename.lower()
    for p in data_dir.rglob("*.csv"):
        if p.name.lower() == target:
            return p
    return None


def _ensure_csv_exists(data_dir: Path, filename: str) -> Path:
    data_dir.mkdir(parents=True, exist_ok=True)

    found = _find_csv(data_dir, filename)
    if found:
        return found

    # KaggleHub download only if explicitly enabled (corporate SSL may block it)
    if os.getenv("USE_KAGGLEHUB_DOWNLOAD", "0") != "1":
        raise FileNotFoundError(
            f"Could not find '{filename}' under {data_dir}. "
            "Place the file at data/Loan_default.csv or set DATA_DIR accordingly. "
            "If you want runtime download, set USE_KAGGLEHUB_DOWNLOAD=1."
        )

    import kagglehub  # local import

    os.environ.setdefault("KAGGLEHUB_CACHE", str(data_dir))
    kagglehub.dataset_download("nikhil1e9/loan-default")

    found = _find_csv(data_dir, filename)
    if not found:
        raise FileNotFoundError(
            f"KaggleHub finished but '{filename}' still not found under {data_dir}."
        )
    return found


@st.cache_data(show_spinner="Carregando dataset...")
def load_dataset(filename: str = "Loan_default.csv") -> pd.DataFrame:
    """
    Load dataset with Streamlit cache, logging essential metadata.
    """
    t0 = time.perf_counter()
    data_dir = get_data_dir()
    csv_path = _ensure_csv_exists(data_dir, filename)

    logger.info("Loading dataset from: %s", csv_path)
    df = pd.read_csv(csv_path)

    df = normalize_binary_yes_no(df)
    _validate_schema(df, REQUIRED_COLUMNS)

    df["Default"] = df["Default"].astype(int)

    dt = time.perf_counter() - t0
    logger.info("Loaded dataset: shape=%s, seconds=%.3f", df.shape, dt)

    return df
