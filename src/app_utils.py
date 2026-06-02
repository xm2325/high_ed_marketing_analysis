from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Iterable
import pandas as pd

DATA_MODE_COLOURS = {
    "Official public data": "#0f766e",
    "Published historical data": "#2563eb",
    "Provisional published figure": "#b45309",
    "Planning assumption": "#7c3aed",
    "Synthetic demonstration": "#6b7280",
    "Authorised upload": "#166534",
    "Internal-data placeholder": "#9f1239",
}


def badge(text: str, colour: str = "#334155") -> str:
    safe = str(text).replace("<", "&lt;").replace(">", "&gt;")
    return f'<span style="display:inline-block;background:{colour};color:white;padding:0.20rem 0.58rem;border-radius:999px;font-size:0.78rem;font-weight:650;margin-right:0.35rem;margin-bottom:0.3rem;">{safe}</span>'


def mode_badge(mode: str) -> str:
    return badge(mode, DATA_MODE_COLOURS.get(mode, "#334155"))


def safe_div(num: float, den: float) -> float | None:
    if den is None or pd.isna(den) or float(den) == 0:
        return None
    return float(num) / float(den)


def fmt_pct(value: float | None, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    return f"{100 * float(value):.{decimals}f}%"


def fmt_change(value: float | None, decimals: int = 1) -> str:
    if value is None or pd.isna(value):
        return "N/A"
    sign = "+" if value > 0 else ""
    return f"{sign}{100 * float(value):.{decimals}f}%"


def pct_change(current: float, previous: float) -> float | None:
    if previous is None or pd.isna(previous) or float(previous) == 0:
        return None
    return (float(current) - float(previous)) / float(previous)


def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def read_csv_or_default(uploaded, default_path: Path) -> tuple[pd.DataFrame, str]:
    if uploaded is None:
        return pd.read_csv(default_path), "Synthetic demonstration"
    return pd.read_csv(uploaded), "Authorised upload"


def require_columns(df: pd.DataFrame, required: Iterable[str]) -> list[str]:
    return sorted(set(required) - set(df.columns))


def html_card(title: str, value: str, note: str = "") -> str:
    note_html = f'<div style="color:#64748b;font-size:0.82rem;margin-top:0.2rem;">{note}</div>' if note else ""
    return (
        '<div class="metric-card">'
        f'<div class="metric-label">{title}</div>'
        f'<div class="metric-value">{value}</div>'
        f'{note_html}'
        '</div>'
    )
