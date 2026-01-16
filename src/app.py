from __future__ import annotations

import io
import logging

import streamlit as st
from dotenv import load_dotenv

from src.components.sidebar import render_smart_filters
from src.core.processing import apply_smart_filters
from src.core.risk import compute_risk_score, compute_value_at_risk, flag_critical_dti
from src.database.loader import load_dataset
from src.visualizations import build_segment_profile, fig_risk_by_segment


def main() -> None:
    load_dotenv()
    logging.basicConfig(level=logging.INFO)

    st.set_page_config(page_title="Loan Default Insight Pro", layout="wide")
    st.title("Loan Default Insight Pro")
    st.caption("Summary-to-Detail — KPIs → Segmentos críticos → Lista de ação")

    # Load
    try:
        df = load_dataset("Loan_default.csv")
    except Exception as exc:
        st.error(f"Falha ao carregar dataset: {exc}")
        st.stop()

    # Smart filters
    f = render_smart_filters(df)
    df_f = apply_smart_filters(df, f)

    if df_f.empty:
        st.warning("Nenhum registro após aplicação dos filtros.")
        st.stop()

    # Baseline vs filtered comparison
    def enrich_risk(d: "pd.DataFrame"):
        rs = compute_risk_score(d)
        d = d.copy()
        d["risk_score"] = rs
        d["value_at_risk_item"] = d["LoanAmount"].astype(float) * rs
        d["critical_dti"] = flag_critical_dti(d, 0.40)
        return d

    df_base = enrich_risk(df)
    df_cur = enrich_risk(df_f)

    # KPIs (Current)
    default_rate_cur = float(df_cur["Default"].mean())
    var_cur = compute_value_at_risk(df_cur, df_cur["risk_score"])
    score_cur = float(df_cur["CreditScore"].mean())
    crit_rate_cur = float(df_cur["critical_dti"].mean())
    crit_count_cur = int(df_cur["critical_dti"].sum())

    # KPIs (Baseline)
    default_rate_base = float(df_base["Default"].mean())
    var_base = compute_value_at_risk(df_base, df_base["risk_score"])
    score_base = float(df_base["CreditScore"].mean())
    crit_rate_base = float(df_base["critical_dti"].mean())

    # Deltas (filtered vs baseline)
    d_default = default_rate_cur - default_rate_base
    d_var = var_cur - var_base
    d_score = score_cur - score_base
    d_crit = crit_rate_cur - crit_rate_base

    # ---------------- Panorama (Big Numbers)
    st.subheader("O Panorama — Estamos seguros?")
    k1, k2, k3, k4 = st.columns(4)

    k1.metric("Taxa de Default", f"{default_rate_cur:.2%}", f"{d_default:+.2%}", border=True)
    k2.metric("Exposição em Risco (R$)", f"{var_cur:,.0f}".replace(",", "."), f"{d_var:+,.0f}".replace(",", "."), border=True)
    k3.metric("Score Médio", f"{score_cur:.0f}", f"{d_score:+.0f}", border=True)
    k4.metric("Alertas Críticos (DTI > 40%)", f"{crit_count_cur} ({crit_rate_cur:.1%})", f"{d_crit:+.1%}", border=True)

    st.caption("Delta calculado como recorte atual vs baseline (dataset completo), por ausência de data no dataset.")

    st.divider()

    # ---------------- Problema (onde está o fogo)
    st.subheader("O Problema — Onde está o fogo?")
    left, right = st.columns(2)

    seg_purpose = build_segment_profile(df_cur, "LoanPurpose")
    seg_emp = build_segment_profile(df_cur, "EmploymentType")

    with left:
        st.plotly_chart(fig_risk_by_segment(seg_purpose, "LoanPurpose"), width='stretch', key="risk_purpose")

    with right:
        st.plotly_chart(fig_risk_by_segment(seg_emp, "EmploymentType"), width='stretch', key="risk_emp")

    # Copy conclusiva (Top1)
    if not seg_purpose.empty:
        top = seg_purpose.iloc[0]
        st.success(
            f"Conclusão: {top['risk_share']:.0%} do risco do recorte está concentrado em LoanPurpose = "
            f"{top['LoanPurpose']} (default {top['default_rate']:.2%}, n={int(top['count'])})."
        )

    st.divider()

    # ---------------- Ação (lista priorizada)
    st.subheader("A Ação — Qual mangueira usar agora?")
    st.caption("Lista priorizada por risco estimado (rule-based), com destaque para DTI crítico.")

    top_n = st.slider("Quantidade de casos para priorização", 50, 2000, 200, step=50)

    action = (
        df_cur.sort_values(["risk_score", "value_at_risk_item"], ascending=False)
        .head(top_n)
        .copy()
    )

    # Minimização: ocultar LoanID por padrão
    cols = [
        "risk_score",
        "value_at_risk_item",
        "Default",
        "critical_dti",
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
    action_view = action[cols].copy()
    st.dataframe(action_view, width='stretch')

    # Export (CSV + Excel)
    csv_bytes = action_view.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Baixar lista de ação (CSV)",
        data=csv_bytes,
        file_name="action_list.csv",
        mime="text/csv",
    )

    xlsx_buffer = io.BytesIO()
    action_view.to_excel(xlsx_buffer, index=False, sheet_name="action_list")
    st.download_button(
        "Baixar lista de ação (Excel)",
        data=xlsx_buffer.getvalue(),
        file_name="action_list.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    with st.expander("Transparência, limitações e uso responsável"):
        st.markdown(
            """
- **Fonte**: dataset público do Kaggle (loan-default).  
- **Limitações**: não há variável temporal; portanto, deltas são recorte vs baseline, não YoY/MoM.  
- **Risco estimado**: nesta versão, o risco é um proxy rule-based (DTI + Score + Juros), com objetivo de simulação rápida e explicabilidade.  
- **Uso responsável**: insights devem orientar políticas/monitoramento; não usar para decisões individuais automatizadas sem governança.  
"""
        )

    with st.expander("Roadmap de modelo (AUC/Recall + Importância/SHAP)"):
        st.markdown(
            """
- Treinar modelo baseline (LogReg) para AUC/Recall.  
- Exibir Feature Importance (coeficientes padronizados) e, opcionalmente, SHAP (se aceitarmos dependência/custo).  
"""
        )


if __name__ == "__main__":
    main()
