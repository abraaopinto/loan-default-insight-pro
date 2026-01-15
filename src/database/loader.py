from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import pandas as pd
import streamlit as st


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
    env_val = os.getenv("DATA_DIR")
    if env_val:
        return Path(env_val).resolve()
    
    # Se não houver variável de ambiente, usa o padrão ./data
    return Path("./data/datasets/nikhil1e9/loan-default/versions/2/").resolve()


def _validate_schema(df: pd.DataFrame, required: Iterable[str]) -> None:
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset schema mismatch. Missing columns: {missing}")


def _ensure_dataset_file(data_dir: Path, filename: str) -> Path:
    """
    Ensure the CSV exists under data_dir. If not found, attempts KaggleHub download.
    """
    csv_path = data_dir / filename
    if csv_path.exists():
        return csv_path

    # Attempt KaggleHub download (optional)
    try:
        import kagglehub  # local import to keep module import fast

        # Align KaggleHub cache to your data directory (same approach you described)
        os.environ.setdefault("KAGGLEHUB_CACHE", str(data_dir))

        kagglehub.dataset_download("nikhil1e9/loan-default")
    except Exception as exc:
        raise FileNotFoundError(
            f"Could not find '{filename}' in {data_dir}. "
            "Also failed to download via KaggleHub. "
            f"Original error: {exc}"
        ) from exc

    if not csv_path.exists():
        raise FileNotFoundError(
            f"KaggleHub download completed but '{filename}' is still not present in {data_dir}."
        )

    return csv_path


@st.cache_data(show_spinner="Carregando dataset...")
def load_dataset(filename: str = "Loan_default.csv") -> pd.DataFrame:
    """
    Load dataset with Streamlit cache, validating expected columns.
    """
    data_dir = get_data_dir()
    data_dir.mkdir(parents=True, exist_ok=True)

    csv_path = _ensure_dataset_file(data_dir, filename)

    df = pd.read_csv(csv_path)
    # Normalize Yes/No -> 1/0 for binary columns (dataset uses strings)
    yn_map = {"Yes": 1, "No": 0}
    for col in ["HasMortgage", "HasDependents", "HasCoSigner"]:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .map(yn_map)
            .astype(int)
        )
    _validate_schema(df, REQUIRED_COLUMNS)

    # Normalize dtypes (light-touch, safe)
    df["Default"] = df["Default"].astype(int)

    return df
