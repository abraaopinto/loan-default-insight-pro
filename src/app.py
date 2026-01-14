import streamlit as st

st.set_page_config(page_title="Loan Default Insight Pro", layout="wide")

st.title("Loan Default Insight Pro")
st.caption("Prototype (Streamlit + Plotly) — Dataset: Kaggle loan-default")

st.info(
    "Etapa 1 concluída: estrutura e infra. "
    "Na Etapa 2 entra o loader via kagglehub + cache + filtros + KPIs."
)