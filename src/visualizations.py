from __future__ import annotations

import plotly.graph_objects as go


def fig_placeholder() -> go.Figure:
    fig = go.Figure()
    fig.update_layout(title="Placeholder figure (Stage 2+)")
    return fig
