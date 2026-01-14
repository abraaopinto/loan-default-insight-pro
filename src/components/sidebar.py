from __future__ import annotations

import streamlit as st


def render_sidebar() -> None:
    """Sidebar placeholder. Filters will be implemented in Stage 2."""
    with st.sidebar:
        st.header("Filtros")
        st.caption("Etapa 2: filtros globais baseados nas colunas do dataset.")
