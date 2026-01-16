from __future__ import annotations

import pandas as pd


def flag_critical_dti(df: pd.DataFrame, threshold: float = 0.40) -> pd.Series:
    return df["DTIRatio"] > threshold


def compute_risk_score(df: pd.DataFrame) -> pd.Series:
    """
    Risk score rule-based (0..1), designed for explainability and fast simulation.

    Intuition:
    - Higher DTI increases risk
    - Lower CreditScore increases risk
    - Higher InterestRate increases risk
    """
    # Normalize to 0..1 with robust clipping
    dti = df["DTIRatio"].clip(lower=0, upper=1)

    # CreditScore typical range: 300..850
    cs_norm = ((df["CreditScore"].clip(300, 850) - 300) / (850 - 300)).clip(0, 1)
    cs_risk = 1 - cs_norm

    # InterestRate: normalize to 0..1 using p5..p95 to reduce outlier effect
    ir = df["InterestRate"].astype(float)
    p5, p95 = ir.quantile(0.05), ir.quantile(0.95)
    ir_norm = ((ir - p5) / (p95 - p5)).clip(0, 1) if p95 > p5 else ir * 0

    # Weighted sum (simple + defensible)
    score = (0.45 * dti) + (0.35 * cs_risk) + (0.20 * ir_norm)
    return score.clip(0, 1)


def compute_value_at_risk(df: pd.DataFrame, risk_score: pd.Series) -> float:
    """
    Value at risk proxy: sum(LoanAmount * risk_score)
    """
    return float((df["LoanAmount"].astype(float) * risk_score).sum())
