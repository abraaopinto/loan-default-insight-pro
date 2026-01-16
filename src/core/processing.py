from __future__ import annotations

import pandas as pd

from src.components.sidebar import SmartFilters


def apply_smart_filters(df: pd.DataFrame, f: SmartFilters) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)

    mask &= df["Income"].between(f.income_range[0], f.income_range[1])

    if f.loan_purpose:
        mask &= df["LoanPurpose"].isin(f.loan_purpose)

    if f.employment_type:
        mask &= df["EmploymentType"].isin(f.employment_type)

    return df.loc[mask].copy()
