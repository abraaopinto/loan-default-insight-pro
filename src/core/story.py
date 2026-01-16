from __future__ import annotations

import pandas as pd


def headline_risk_concentration(seg: pd.DataFrame, dim: str) -> str:
    """
    Build an executive headline like:
    '60% do risco está concentrado em LoanPurpose = Education ...'
    Requires seg to have: [dim, risk_share, default_rate, count]
    """
    if seg is None or seg.empty:
        return "Sem segmentos suficientes no recorte atual para concluir concentração de risco."

    top = seg.iloc[0]
    val = top[dim]
    share = float(top["risk_share"])
    dr = float(top["default_rate"])
    cnt = int(top["count"])

    return (
        f"{share:.0%} do risco do recorte está concentrado em {dim} = {val} "
        f"(default {dr:.2%}, n={cnt})."
    )
