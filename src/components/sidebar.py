from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st


@dataclass(frozen=True)
class Filters:
    age_range: tuple[int, int]
    income_range: tuple[float, float]
    loan_amount_range: tuple[float, float]
    credit_score_range: tuple[int, int]
    interest_rate_range: tuple[float, float]
    dti_range: tuple[float, float]
    education: list[str]
    employment_type: list[str]
    marital_status: list[str]
    has_mortgage: list[int]
    has_dependents: list[int]
    loan_purpose: list[str]
    has_cosigner: list[int]
    default: list[int]


def _minmax(series: pd.Series) -> tuple[float, float]:
    return float(series.min()), float(series.max())


def render_filters(df: pd.DataFrame) -> Filters:
    with st.sidebar:
        st.header("Filtros")

        # Numeric ranges
        age_min, age_max = int(df["Age"].min()), int(df["Age"].max())
        cs_min, cs_max = int(df["CreditScore"].min()), int(df["CreditScore"].max())

        inc_min, inc_max = _minmax(df["Income"])
        la_min, la_max = _minmax(df["LoanAmount"])
        ir_min, ir_max = _minmax(df["InterestRate"])
        dti_min, dti_max = _minmax(df["DTIRatio"])

        age_range = st.slider("Idade", min_value=age_min, max_value=age_max, value=(age_min, age_max))
        income_range = st.slider(
            "Renda (Income)", min_value=inc_min, max_value=inc_max, value=(inc_min, inc_max)
        )
        loan_amount_range = st.slider(
            "Valor do empréstimo (LoanAmount)",
            min_value=la_min,
            max_value=la_max,
            value=(la_min, la_max),
        )
        credit_score_range = st.slider(
            "Credit Score", min_value=cs_min, max_value=cs_max, value=(cs_min, cs_max)
        )
        interest_rate_range = st.slider(
            "Taxa de juros (InterestRate)",
            min_value=ir_min,
            max_value=ir_max,
            value=(ir_min, ir_max),
        )
        dti_range = st.slider(
            "DTI Ratio (DTIRatio)", min_value=dti_min, max_value=dti_max, value=(dti_min, dti_max)
        )

        # Categorical filters
        education = st.multiselect("Education", sorted(df["Education"].dropna().unique().tolist()), default=[])
        employment_type = st.multiselect(
            "EmploymentType", sorted(df["EmploymentType"].dropna().unique().tolist()), default=[]
        )
        marital_status = st.multiselect(
            "MaritalStatus", sorted(df["MaritalStatus"].dropna().unique().tolist()), default=[]
        )
        loan_purpose = st.multiselect(
            "LoanPurpose", sorted(df["LoanPurpose"].dropna().unique().tolist()), default=[]
        )

        # Binary filters (keep as ints)
        has_mortgage = st.multiselect("HasMortgage", [0, 1], default=[0, 1])
        has_dependents = st.multiselect("HasDependents", [0, 1], default=[0, 1])
        has_cosigner = st.multiselect("HasCoSigner", [0, 1], default=[0, 1])
        default = st.multiselect("Default", [0, 1], default=[0, 1])

    return Filters(
        age_range=age_range,
        income_range=income_range,
        loan_amount_range=loan_amount_range,
        credit_score_range=credit_score_range,
        interest_rate_range=interest_rate_range,
        dti_range=dti_range,
        education=education,
        employment_type=employment_type,
        marital_status=marital_status,
        has_mortgage=has_mortgage,
        has_dependents=has_dependents,
        loan_purpose=loan_purpose,
        has_cosigner=has_cosigner,
        default=default,
    )
