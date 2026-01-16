from __future__ import annotations


def fmt_pct(x: float) -> str:
    return f"{x:.2%}"


def fmt_br_money(x: float) -> str:
    return f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_int_ptbr(n: int) -> str:
    return f"{n:,}".replace(",", ".")
