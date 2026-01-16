from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def fig_default_rate_by_category(df_rate: pd.DataFrame, category: str) -> go.Figure:
    if df_rate.empty:
        fig = go.Figure()
        fig.update_layout(title=f"Default rate por {category} (sem dados)")
        return fig

    fig = px.bar(
        df_rate,
        x=category,
        y="default_rate",
        hover_data={"count": True, "default_rate": ":.2%"},
        title=f"Taxa de Default por {category} (com volume mínimo)",
    )
    fig.update_yaxes(tickformat=".0%")
    return fig


def fig_credit_score_bins(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="Default rate por faixas de CreditScore (sem dados)")
        return fig

    bins = [300, 500, 600, 650, 700, 750, 800, 850]
    labels = [f"{bins[i]}-{bins[i+1]-1}" for i in range(len(bins) - 1)]
    tmp = df.copy()
    tmp["CreditScoreBin"] = pd.cut(tmp["CreditScore"], bins=bins, labels=labels, include_lowest=True)

    rate = (
        tmp.groupby("CreditScoreBin", dropna=False)
        .agg(default_rate=("Default", "mean"), count=("LoanID", "count"))
        .reset_index()
    )

    fig = px.line(
        rate,
        x="CreditScoreBin",
        y="default_rate",
        markers=True,
        hover_data={"count": True, "default_rate": ":.2%"},
        title="Taxa de Default por Faixa de Credit Score",
    )
    fig.update_yaxes(tickformat=".0%")
    return fig


def fig_scatter_risk(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        fig = go.Figure()
        fig.update_layout(title="Risco: LoanAmount vs CreditScore (sem dados)")
        return fig

    fig = px.scatter(
        df.sample(min(len(df), 5000), random_state=42),
        x="CreditScore",
        y="LoanAmount",
        color="Default",
        hover_data=["Income", "InterestRate", "LoanPurpose", "EmploymentType", "DTIRatio"],
        title="Risco: Valor do Empréstimo vs Credit Score (amostra)",
    )
    return fig


def fig_driver_deltas(drivers: pd.DataFrame) -> go.Figure:
    """
    Bar chart: delta_pct for numeric drivers (Default=1 vs Default=0).
    """
    if drivers.empty:
        fig = go.Figure()
        fig.update_layout(title="Drivers (sem dados)")
        return fig

    top = drivers.head(10).copy()
    fig = px.bar(
        top,
        x="feature",
        y="delta_pct",
        hover_data={"delta_pct": ":.2%","delta": ":.3f","mean_default_0": ":.3f","mean_default_1": ":.3f"},
        title="Top 10 Drivers Numéricos — Diferença relativa (Default=1 vs Default=0)",
    )
    fig.update_yaxes(tickformat=".0%")
    return fig

def build_segment_profile(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """
    Returns a segment table with:
    - risk_share: share of total value_at_risk
    - default_rate, count
    - demographic/contract medians (hover)
    - dominant categories (hover)
    """
    if df.empty:
        return pd.DataFrame()

    def mode_or_na(s: pd.Series) -> str:
        s = s.dropna()
        return str(s.mode().iloc[0]) if not s.empty else "N/A"

    out = (
        df.groupby(by, dropna=False)
        .agg(
            count=("LoanID", "count"),
            default_rate=("Default", "mean"),
            var_sum=("value_at_risk_item", "sum"),
            age_med=("Age", "median"),
            income_med=("Income", "median"),
            score_med=("CreditScore", "median"),
            dti_med=("DTIRatio", "median"),
            emp_mode=("EmploymentType", mode_or_na),
            edu_mode=("Education", mode_or_na),
            mar_mode=("MaritalStatus", mode_or_na),
        )
        .reset_index()
    )

    total_var = float(out["var_sum"].sum()) if out["var_sum"].sum() else 0.0
    out["risk_share"] = (out["var_sum"] / total_var) if total_var > 0 else 0.0
    out = out.sort_values(["var_sum", "default_rate", "count"], ascending=[False, False, False])
    return out


def fig_risk_by_segment(seg: pd.DataFrame, by: str) -> go.Figure:
    if seg.empty:
        fig = go.Figure()
        fig.update_layout(title=f"Risco por {by} (sem dados)")
        return fig

    fig = px.bar(
        seg.head(15),
        x=by,
        y="var_sum",
        hover_data={
            "risk_share": ":.2%",
            "default_rate": ":.2%",
            "count": True,
            "age_med": ":.0f",
            "income_med": ":.0f",
            "score_med": ":.0f",
            "dti_med": ":.2f",
            "emp_mode": True,
            "edu_mode": True,
            "mar_mode": True,
        },
        title=f"Top segmentos por Valor em Risco — {by}",
    )
    return fig
