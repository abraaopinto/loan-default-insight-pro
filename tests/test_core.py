import pandas as pd

from src.core.metrics import compute_kpis, segment_default_rate


def make_df():
    return pd.DataFrame(
        {
            "LoanID": [1, 2, 3, 4, 5],
            "Default": [0, 1, 0, 1, 1],
            "LoanAmount": [1000, 2000, 1500, 3000, 2500],
            "CreditScore": [700, 600, 720, 580, 610],
            "InterestRate": [10, 12, 9, 15, 14],
            "DTIRatio": [0.2, 0.4, 0.25, 0.5, 0.45],
            "Income": [5000, 4000, 5200, 3500, 3700],
            "MonthsEmployed": [24, 12, 36, 6, 8],
            "NumCreditLines": [3, 4, 2, 5, 4],
            "LoanPurpose": ["A", "A", "B", "B", "B"],
        }
    )


def test_compute_kpis():
    df = make_df()
    kpis = compute_kpis(df)
    assert kpis["total_loans"] == 5
    assert abs(kpis["default_rate"] - 0.6) < 1e-9


def test_segment_default_rate_min_count():
    df = make_df()
    seg = segment_default_rate(df, "LoanPurpose", min_count=3)
    # only "B" appears 3 times
    assert len(seg) == 1
    assert seg.iloc[0]["LoanPurpose"] == "B"
