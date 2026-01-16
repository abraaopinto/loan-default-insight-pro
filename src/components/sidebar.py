from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import streamlit as st


@dataclass(frozen=True)
class SmartFilters:
    income_range: tuple[float, float]
    loan_purpose: list[str]
    employment_type: list[str]


def _minmax(series: pd.Series) -> tuple[float, float]:
    return float(series.min()), float(series.max())


def render_smart_filters(df: pd.DataFrame) -> SmartFilters:
    """
    Smart + persistent filters (session_state).
    """
    with st.sidebar:
        st.header("Filtros (simulação rápida)")

        inc_min, inc_max = _minmax(df["Income"])

        # Persistência via session_state
        if "income_range" not in st.session_state:
            st.session_state["income_range"] = (inc_min, inc_max)
        if "loan_purpose" not in st.session_state:
            st.session_state["loan_purpose"] = []
        if "employment_type" not in st.session_state:
            st.session_state["employment_type"] = []

        income_range = st.slider(
            "Faixa de renda (Income)",
            min_value=inc_min,
            max_value=inc_max,
            value=st.session_state["income_range"],
            key="income_range",
        )

        loan_purpose = st.multiselect(
            "Finalidade (LoanPurpose)",
            sorted(df["LoanPurpose"].dropna().unique().tolist()),
            default=st.session_state["loan_purpose"],
            key="loan_purpose",
        )

        employment_type = st.multiselect(
            "Tipo de emprego (EmploymentType)",
            sorted(df["EmploymentType"].dropna().unique().tolist()),
            default=st.session_state["employment_type"],
            key="employment_type",
        )

    return SmartFilters(
        income_range=income_range,
        loan_purpose=loan_purpose,
        employment_type=employment_type,
    )
