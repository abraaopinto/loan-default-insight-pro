from __future__ import annotations

import io
import logging

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from src.components.sidebar import render_smart_filters
from src.core.processing import apply_smart_filters
from src.core.risk import (
    classify_risk_band,
    compute_risk_score,
    compute_value_at_risk,
    flag_critical_dti,
)
from src.core.story import headline_risk_concentration
from src.core.formatting import fmt_int_ptbr, fmt_money_ptbr, fmt_pct
from src.database.loader import load_dataset
from src.visualizations import build_segment_profile, fig_risk_by_segment


def enrich_risk(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enrich dataframe with risk proxy, value-at-risk per item, DTI critical flags and risk bands.
    """
    rs = compute_risk_score(df)
    out = df.copy()
    out["risk_score"] = rs
    out["risk_band"] = classify_risk_band(out["risk_score"])
    out["value_at_risk_item"] = out["LoanAmount"].astype(float) * out["risk_score"]
    out["critical_dti"] = flag_critical_dti(out, 0.40)
    return out


def compute_panorama_kpis(df_cur: pd.DataFrame, df_base: pd.DataFrame) -> dict[str, float | int]:
    """
    Compute KPIs for current filtered view and baseline, plus deltas.
    """
    # Current
    default_rate_cur = float(df_cur["Default"].mean())
    var_cur = compute_value_at_risk(df_cur, df_cur["risk_score"])
    score_cur = float(df_cur["CreditScore"].mean())
    crit_rate_cur = float(df_cur["critical_dti"].mean())
    crit_count_cur = int(df_cur["critical_dti"].sum())

    # Baseline
    default_rate_base = float(df_base["Default"].mean())
    var_base = compute_value_at_risk(df_base, df_base["risk_score"])
    score_base = float(df_base["CreditScore"].mean())
    crit_rate_base = float(df_base["critical_dti"].mean())

    return {
        "default_rate_cur": default_rate_cur,
        "var_cur": var_cur,
        "score_cur": score_cur,
        "crit_rate_cur": crit_rate_cur,
        "crit_count_cur": crit_count_cur,
        "default_rate_base": default_rate_base,
        "var_base": var_base,
        "score_base": score_base,
        "crit_rate_base": crit_rate_base,
        "d_default": default_rate_cur - default_rate_base,
        "d_var": var_cur - var_base,
        "d_score": score_cur - score_base,
        "d_crit": crit_rate_cur - crit_rate_base,
    }


def render_panorama(df_cur: pd.DataFrame, df_base: pd.DataFrame) -> None:
    k = compute_panorama_kpis(df_cur, df_base)

    st.subheader("O Panorama — Estamos seguros?")
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "Taxa de Default (recorte)",
            fmt_pct(k["default_rate_cur"], 2),
            f"{k['d_default']:+.2%}",
            border=True,
        )
    with c2:
        st.metric(
            "Exposição em Risco (R$)",
            fmt_money_ptbr(float(k["var_cur"]), 0),
            fmt_money_ptbr(float(k["d_var"]), 0),
            border=True,
        )
    with c3:
        st.metric(
            "Score Médio",
            f"{float(k['score_cur']):.0f}",
            f"{float(k['d_score']):+.0f}",
            border=True,
        )
    with c4:
        st.metric(
            "Alertas Críticos (DTI > 40%)",
            f"{fmt_int_ptbr(int(k['crit_count_cur']))} ({fmt_pct(float(k['crit_rate_cur']), 1)})",
            f"{float(k['d_crit']):+.1%}",
            border=True,
        )

    st.caption(
        "Delta calculado como recorte atual vs baseline (dataset completo), por ausência de data no dataset. "
        "Legenda: Default 0 = adimplente | 1 = inadimplente. "
        "Faixas de risco: Neutro (baixo), Alerta (médio), Crítico (alto). "
        "DTI crítico: DTIRatio > 40%."
    )

    with st.container(border=True):
        st.markdown("**Distribuição por faixa de risco (recorte atual)**")
        band_counts = (
            df_cur["risk_band"]
            .value_counts(dropna=False)
            .rename_axis("risk_band")
            .reset_index(name="count")
        )
        band_counts["count"] = band_counts["count"].astype(int)
        st.dataframe(band_counts, width='content', hide_index=True)


def render_problema(df_cur: pd.DataFrame) -> None:
    st.subheader("O Problema — Onde está o fogo?")
    st.caption("Segmentos priorizados por Valor em Risco (proxy). Passe o mouse para ver o perfil do grupo.")

    seg_purpose = build_segment_profile(df_cur, "LoanPurpose")
    seg_emp = build_segment_profile(df_cur, "EmploymentType")

    left, right = st.columns(2)
    with left:
        st.plotly_chart(
            fig_risk_by_segment(seg_purpose, "LoanPurpose"),
            width='stretch',
            key="p1_risk_purpose",
        )
    with right:
        st.plotly_chart(
            fig_risk_by_segment(seg_emp, "EmploymentType"),
            width='stretch',
            key="p1_risk_emp",
        )

    # Data Copy (conclusão automática)
    if not seg_purpose.empty:
        st.success("Conclusão: " + headline_risk_concentration(seg_purpose, "LoanPurpose"))
    else:
        st.info("Sem segmentos suficientes para concluir concentração de risco no recorte atual.")

    st.divider()

    # Microinteração: Profile Card do segmento selecionado
    st.markdown("### Microinteração — Perfil predominante do segmento selecionado")

    colA, colB = st.columns([1, 1])
    with colA:
        seg_choice_dim = st.selectbox(
            "Dimensão",
            ["LoanPurpose", "EmploymentType"],
            index=0,
            key="seg_choice_dim",
        )
        seg_table = seg_purpose if seg_choice_dim == "LoanPurpose" else seg_emp

        if seg_table.empty:
            st.warning("Sem segmentos disponíveis neste recorte.")
            return

        seg_value = st.selectbox(
            "Segmento",
            seg_table[seg_choice_dim].astype(str).tolist(),
            key="seg_value",
        )

    with colB:
        row = seg_table[seg_table[seg_choice_dim].astype(str) == str(seg_value)].iloc[0]

        with st.container(border=True):
            st.markdown(f"**Segmento:** {seg_choice_dim} = `{seg_value}`")

            st.write(
                f"**Participação no risco:** {fmt_pct(float(row['risk_share']), 0)}  \n"
                f"**Taxa de default:** {fmt_pct(float(row['default_rate']), 2)}  \n"
                f"**Volume:** {fmt_int_ptbr(int(row['count']))}"
            )

            st.write(
                f"**Medianas:** Idade {int(row['age_med'])} | "
                f"Renda {fmt_money_ptbr(float(row['income_med']), 0)} | "
                f"Score {int(row['score_med'])} | "
                f"DTI {float(row['dti_med']):.2f}"
            )

            st.write(
                f"**Predominância:** Emprego {row['emp_mode']} | "
                f"Escolaridade {row['edu_mode']} | "
                f"Estado civil {row['mar_mode']}"
            )


def render_acao(df_cur: pd.DataFrame) -> None:
    st.subheader("A Ação — Qual mangueira usar agora?")
    st.caption("Lista priorizada por risco estimado (proxy). Use os controles para focar no que é mais acionável.")

    controls = st.columns([1, 1, 1])
    with controls[0]:
        top_n = st.slider("Top N", 50, 2000, 200, step=50, key="top_n_action")
    with controls[1]:
        only_critical = st.checkbox("Somente DTI crítico (>40%)", value=False, key="only_critical")
    with controls[2]:
        sort_by = st.radio(
            "Ordenar por",
            ["risk_score", "value_at_risk_item"],
            horizontal=True,
            key="sort_by",
        )

    action = df_cur.sort_values([sort_by], ascending=False).head(top_n).copy()
    if only_critical:
        action = action[action["critical_dti"]].copy()

    # Minimização: ocultar LoanID por padrão
    cols = [
        "risk_band",
        "risk_score",
        "value_at_risk_item",
        "critical_dti",
        "Default",
        "LoanAmount",
        "Income",
        "CreditScore",
        "DTIRatio",
        "InterestRate",
        "LoanTerm",
        "LoanPurpose",
        "EmploymentType",
        "Education",
        "MaritalStatus",
    ]
    view = action[cols].copy()

    with st.container(border=True):
        st.markdown("**Lista priorizada (recorte atual)**")
        st.dataframe(view, width='content')

    # Exports
    st.markdown("### Exportação (lista de ação)")
    c1, c2 = st.columns(2)

    csv_bytes = view.to_csv(index=False).encode("utf-8")
    with c1:
        st.download_button(
            "Baixar CSV",
            data=csv_bytes,
            file_name="action_list.csv",
            mime="text/csv",
            key="dl_action_csv",
        )

    xlsx_buffer = io.BytesIO()
    view.to_excel(xlsx_buffer, index=False, sheet_name="action_list")
    with c2:
        st.download_button(
            "Baixar Excel",
            data=xlsx_buffer.getvalue(),
            file_name="action_list.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="dl_action_xlsx",
        )


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    st.set_page_config(page_title="Loan Default Insight Pro", layout="wide")
    st.title("Loan Default Insight Pro")
    st.caption("Consultor de risco (Summary-to-Detail): KPIs → Segmentos críticos → Lista de ação")

    # Load
    try:
        df = load_dataset("Loan_default.csv")
    except Exception as exc:
        st.error(f"Falha ao carregar dataset: {exc}")
        st.stop()

    # Smart filters (persistent)
    f = render_smart_filters(df)
    df_f = apply_smart_filters(df, f)

    if df_f.empty:
        st.warning("Nenhum registro após aplicação dos filtros.")
        st.stop()

    # Enrich risk (baseline + filtered)
    df_base = enrich_risk(df)
    df_cur = enrich_risk(df_f)

    # Layout: Panorama -> Problema -> Ação
    render_panorama(df_cur, df_base)
    st.divider()
    render_problema(df_cur)
    st.divider()
    render_acao(df_cur)

    # Transparência e roadmap (Princípios base)
    with st.expander("Transparência, limitações e uso responsável"):
        st.markdown(
            """
- **Fonte**: dataset público do Kaggle (loan-default).  
- **Limitações**: não há variável temporal; deltas são recorte vs baseline (não YoY/MoM).  
- **Risco estimado**: proxy rule-based (DTI + Score + Juros) para simulação rápida e explicabilidade.  
- **Uso responsável**: resultados devem orientar políticas/monitoramento; não usar para decisões individuais automatizadas sem governança.  
"""
        )

    with st.expander("Roadmap (P2): Modelo e explicabilidade"):
        st.markdown(
            """
- Treinar modelo baseline (ex.: Logistic Regression) para **AUC/Recall**.  
- Exibir **importância de variáveis** (coeficientes padronizados / permutation importance).  
- Opcional: **SHAP** (custo/depêndencia adicional).  
"""
        )


if __name__ == "__main__":
    main()
