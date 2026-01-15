from __future__ import annotations

import pandas as pd

from src.components.sidebar import Filters


def apply_filters(df: pd.DataFrame, f: Filters) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)

    mask &= df["Age"].between(f.age_range[0], f.age_range[1])
    mask &= df["Income"].between(f.income_range[0], f.income_range[1])
    mask &= df["LoanAmount"].between(f.loan_amount_range[0], f.loan_amount_range[1])
    mask &= df["CreditScore"].between(f.credit_score_range[0], f.credit_score_range[1])
    mask &= df["InterestRate"].between(f.interest_rate_range[0], f.interest_rate_range[1])
    mask &= df["DTIRatio"].between(f.dti_range[0], f.dti_range[1])

    if f.education:
        mask &= df["Education"].isin(f.education)
    if f.employment_type:
        mask &= df["EmploymentType"].isin(f.employment_type)
    if f.marital_status:
        mask &= df["MaritalStatus"].isin(f.marital_status)
    if f.loan_purpose:
        mask &= df["LoanPurpose"].isin(f.loan_purpose)

    mask &= df["HasMortgage"].isin(f.has_mortgage)
    mask &= df["HasDependents"].isin(f.has_dependents)
    mask &= df["HasCoSigner"].isin(f.has_cosigner)
    mask &= df["Default"].isin(f.default)

    return df.loc[mask].copy()
