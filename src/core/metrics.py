from __future__ import annotations

from typing import Any

import pandas as pd


def compute_kpis(df: pd.DataFrame) -> dict[str, Any]:
    """Placeholder KPI computation (Stage 2+)."""
    return {"rows": int(len(df))}
