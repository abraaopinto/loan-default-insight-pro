from __future__ import annotations

import streamlit as st

from src.components.sidebar import render_filters
from src.core.metrics import compute_kpis, default_rate_by
from src.core.processing import apply_filters
from src.database.loader import load_dataset
from src.visualizations import fig_credit_score_bins, fig_default_rate_by_category, fig_scatter_risk


def main() -> None:
    st.set_page_config(page_title="Loan Default Insight Pro", layout="wide")
    st.title("Loan Default Insight Pro")
    st.caption("Prototype (Streamlit + Plotly) — Kaggle: nikhil1e9/loan-default")

    try:
        df = load_dataset("Loan_default.csv")
    except Exception as exc:
        st.error(f"Falha ao carregar dataset: {exc}")
        st.stop()

    filters = render_filters(df)

    try:
        df_f = apply_filters(df, filters)
    except Exception as exc:
        st.error(f"Falha ao aplicar filtros: {exc}")
        st.stop()

    if df_f.empty:
        st.warning("Nenhum registro após aplicação dos filtros.")
        st.stop()

    # KPIs
    kpis = compute_kpis(df_f)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Operações", f"{kpis['total_loans']:,}".replace(",", "."))
    c2.metric("Taxa de Default", f"{kpis['default_rate']:.2%}")
    c3.metric("Ticket Médio", f"{kpis['avg_loan_amount']:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
    c4.metric("Credit Score Médio", f"{kpis['avg_credit_score']:.1f}")
    c5.metric("Juros Médio", f"{kpis['avg_interest_rate']:.2f}%")

    st.divider()

    # Visualizações
    left, right = st.columns(2)

    with left:
        rate_purpose = default_rate_by(df_f, "LoanPurpose")
        st.plotly_chart(fig_default_rate_by_category(rate_purpose, "LoanPurpose"), use_container_width=True)

    with right:
        st.plotly_chart(fig_credit_score_bins(df_f), use_container_width=True)

    st.plotly_chart(fig_scatter_risk(df_f), use_container_width=True)

    st.divider()

    # Export
    st.subheader("Exportação")
    st.caption("Baixe o dataset filtrado para análises externas ou anexos do Pitch.")
    csv_bytes = df_f.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="Baixar CSV filtrado",
        data=csv_bytes,
        file_name="loan_default_filtered.csv",
        mime="text/csv",
        use_container_width=False,
    )

    with st.expander("Prévia dos dados filtrados"):
        st.dataframe(df_f.head(50), use_container_width=True)


if __name__ == "__main__":
    main()
