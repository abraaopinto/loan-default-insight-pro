from __future__ import annotations

import streamlit as st

from src.components.sidebar import render_filters
from src.core.metrics import compute_kpis, compare_drivers, segment_default_rate, top_segments_multi
from src.core.processing import apply_filters
from src.database.loader import load_dataset
from src.visualizations import (
    fig_credit_score_bins,
    fig_default_rate_by_category,
    fig_driver_deltas,
    fig_scatter_risk,
)


DEFAULT_DIMENSIONS = ["LoanPurpose", "EmploymentType", "Education", "MaritalStatus"]
NUMERIC_DRIVERS = ["Income", "LoanAmount", "CreditScore", "InterestRate", "DTIRatio", "MonthsEmployed", "NumCreditLines"]


def fmt_br_number(x: float) -> str:
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def main() -> None:
    st.set_page_config(page_title="Loan Default Insight Pro", layout="wide")
    st.title("Loan Default Insight Pro")
    st.caption("Prototype (Streamlit + Plotly) — Kaggle: nikhil1e9/loan-default")

    # ---- Load
    try:
        df = load_dataset("Loan_default.csv")
    except Exception as exc:
        st.error(f"Falha ao carregar dataset: {exc}")
        st.stop()

    # ---- Filters
    filters = render_filters(df)

    try:
        df_f = apply_filters(df, filters)
    except Exception as exc:
        st.error(f"Falha ao aplicar filtros: {exc}")
        st.stop()

    if df_f.empty:
        st.warning("Nenhum registro após aplicação dos filtros.")
        st.stop()

    # ---- KPIs
    kpis = compute_kpis(df_f)
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Operações", f"{kpis['total_loans']:,}".replace(",", "."))
    c2.metric("Taxa de Default", f"{kpis['default_rate']:.2%}")
    c3.metric("Ticket Médio", fmt_br_number(kpis["avg_loan_amount"]))
    c4.metric("Credit Score Médio", f"{kpis['avg_credit_score']:.1f}")
    c5.metric("Juros Médio", f"{kpis['avg_interest_rate']:.2f}%")

    st.divider()

    tabs = st.tabs(["Visão Geral", "Insights", "Risk Explorer", "Exportação", "Narrativa para o Pitch"])

    # -------------------- Visão Geral
    with tabs[0]:
        left, right = st.columns(2)

        with left:
            # segment by purpose with a sensible minimum volume
            rate_purpose = segment_default_rate(df_f, "LoanPurpose", min_count=200)
            st.plotly_chart(
                fig_default_rate_by_category(rate_purpose, "LoanPurpose"),
                use_container_width=True,
                key="vg_default_by_purpose",
            )

        with right:
            st.plotly_chart(
                fig_credit_score_bins(df_f),
                use_container_width=True,
                key="vg_credit_score_bins",
            )

        st.plotly_chart(
            fig_scatter_risk(df_f),
            use_container_width=True,
            key="vg_scatter_risk",
        )

    # -------------------- Insights
    with tabs[1]:
        st.subheader("Insights por Segmento (com controle de volume)")
        st.caption("Mostra segmentos com maior taxa de default, descartando grupos pequenos para evitar distorções.")

        min_count = st.slider("Volume mínimo por segmento", min_value=50, max_value=2000, value=200, step=50)

        results = top_segments_multi(df_f, DEFAULT_DIMENSIONS, min_count=min_count, top_n=5)

        cols = st.columns(2)
        for i, dim in enumerate(DEFAULT_DIMENSIONS):
            with cols[i % 2]:
                st.markdown(f"### Top 5 — {dim}")
                seg = results[dim]
                if seg.empty:
                    st.info("Sem segmentos suficientes para o volume mínimo selecionado.")
                else:
                    view = seg.copy()
                    view["default_rate"] = view["default_rate"].map(lambda x: f"{x:.2%}")
                    st.dataframe(view, use_container_width=True)

    # -------------------- Risk Explorer
    with tabs[2]:
        st.subheader("Risk Explorer")
        st.caption("Ranking de categorias e comparação de drivers entre inadimplentes vs adimplentes.")

        dim = st.selectbox("Escolha a dimensão para ranking", DEFAULT_DIMENSIONS, index=0)
        min_count = st.slider("Volume mínimo (ranking)", min_value=50, max_value=2000, value=200, step=50, key="min_count_rank")

        seg = segment_default_rate(df_f, dim, min_count=min_count)
        st.plotly_chart(
            fig_default_rate_by_category(seg, dim),
            use_container_width=True,
            key=f"re_default_by_{dim}",
        )

        st.markdown("### Drivers numéricos (Default=1 vs Default=0)")
        drivers = compare_drivers(df_f, NUMERIC_DRIVERS)
        st.plotly_chart(
            fig_driver_deltas(drivers),
            use_container_width=True,
            key="re_driver_deltas",
        )

        with st.expander("Tabela de drivers (detalhada)"):
            if drivers.empty:
                st.info("Sem dados suficientes para comparação.")
            else:
                st.dataframe(drivers, use_container_width=True)

    # -------------------- Exportação
    with tabs[3]:
        st.subheader("Exportação")
        st.caption("Baixe o dataset filtrado para análises externas ou anexos do Pitch.")
        csv_bytes = df_f.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="Baixar CSV filtrado",
            data=csv_bytes,
            file_name="loan_default_filtered.csv",
            mime="text/csv",
        )
        with st.expander("Prévia dos dados filtrados"):
            st.dataframe(df_f.head(50), use_container_width=True)

    # -------------------- Narrativa para o Pitch
    with tabs[4]:
        st.subheader("Narrativa pronta (texto-base para slides e fala)")
        st.markdown(
            """
**Problema de negócio**  
Em carteiras de crédito, a inadimplência impacta diretamente receita, provisões e alocação de capital.  
Sem uma visão consolidada, decisões ficam reativas: ajustes de política acontecem tarde e com baixa precisão.

**Abordagem (BI orientado a decisão)**  
Este protótipo consolida dados de empréstimos e entrega:  
- KPIs de risco (taxa de default, ticket médio, score e juros médios);  
- segmentação com controle de volume (evita distorções estatísticas);  
- exploração de drivers para entender o que mais diferencia inadimplentes de adimplentes;  
- exportação de recortes para validação e apoio a decisões.

**Principais entregas do dashboard**  
- Filtros globais para simular políticas e segmentos;  
- Rankings de risco por finalidade, tipo de emprego, escolaridade e estado civil;  
- Comparativo de drivers numéricos (diferença relativa Default=1 vs Default=0).

**Como isso apoia decisão**  
Permite priorizar segmentos críticos, calibrar políticas (ex.: limites, juros, prazos) e orientar ações de prevenção  
com base em evidências, não apenas em percepções.

**Próximos passos (evolução natural)**  
- scorecard/thresholds por segmento;  
- monitoramento temporal (se houver datas) e alertas;  
- integração com pipeline de dados e camada de governança.
"""
        )


if __name__ == "__main__":
    main()
