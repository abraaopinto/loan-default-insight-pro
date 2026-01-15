from __future__ import annotations

from typing import Any

import pandas as pd


def compute_kpis(df: pd.DataFrame) -> dict[str, Any]:
    if df.empty:
        return {
            "total_loans": 0,
            "default_rate": 0.0,
            "avg_loan_amount": 0.0,
            "avg_credit_score": 0.0,
            "avg_interest_rate": 0.0,
        }

    total = int(len(df))
    default_rate = float(df["Default"].mean())
    return {
        "total_loans": total,
        "default_rate": default_rate,
        "avg_loan_amount": float(df["LoanAmount"].mean()),
        "avg_credit_score": float(df["CreditScore"].mean()),
        "avg_interest_rate": float(df["InterestRate"].mean()),
    }


def default_rate_by(df: pd.DataFrame, by: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame({by: [], "default_rate": [], "count": []})

    out = (
        df.groupby(by, dropna=False)
        .agg(default_rate=("Default", "mean"), count=("LoanID", "count"))
        .reset_index()
        .sort_values(["default_rate", "count"], ascending=[False, False])
    )
    return out
