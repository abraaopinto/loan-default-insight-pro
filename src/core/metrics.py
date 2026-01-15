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


def segment_default_rate(df: pd.DataFrame, by: str, min_count: int = 200) -> pd.DataFrame:
    """
    Segment default rate with minimum volume threshold.
    Returns columns: [by, default_rate, count]
    """
    if df.empty:
        return pd.DataFrame({by: [], "default_rate": [], "count": []})

    out = (
        df.groupby(by, dropna=False)
        .agg(default_rate=("Default", "mean"), count=("LoanID", "count"))
        .reset_index()
    )
    out = out[out["count"] >= min_count].sort_values(
        ["default_rate", "count"], ascending=[False, False]
    )
    return out


def top_segments_multi(df: pd.DataFrame, dimensions: list[str], min_count: int = 200, top_n: int = 5) -> dict[str, pd.DataFrame]:
    """
    For each dimension, compute segment default rate table and return top_n.
    """
    results: dict[str, pd.DataFrame] = {}
    for dim in dimensions:
        seg = segment_default_rate(df, dim, min_count=min_count).head(top_n)
        results[dim] = seg
    return results


def compare_drivers(df: pd.DataFrame, numeric_cols: list[str]) -> pd.DataFrame:
    """
    Compare average numeric drivers between Default=1 and Default=0.
    Output columns: feature, mean_default_0, mean_default_1, delta, delta_pct
    """
    if df.empty:
        return pd.DataFrame(columns=["feature", "mean_default_0", "mean_default_1", "delta", "delta_pct"])

    g = df.groupby("Default")[numeric_cols].mean(numeric_only=True)
    if 0 not in g.index or 1 not in g.index:
        return pd.DataFrame(columns=["feature", "mean_default_0", "mean_default_1", "delta", "delta_pct"])

    rows = []
    for col in numeric_cols:
        m0 = float(g.loc[0, col])
        m1 = float(g.loc[1, col])
        delta = m1 - m0
        delta_pct = (delta / m0) if m0 != 0 else 0.0
        rows.append(
            {"feature": col, "mean_default_0": m0, "mean_default_1": m1, "delta": delta, "delta_pct": delta_pct}
        )

    out = pd.DataFrame(rows).sort_values("delta_pct", ascending=False)
    return out
