from __future__ import annotations

from io import BytesIO
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from app_utils import safe_div, pct_change, fmt_pct, fmt_change

ADMISSIONS_REQUIRED = [
    "population", "cycle", "cycle_week", "snapshot_date", "faculty", "school",
    "department", "sub_department", "course_code", "course_name", "fee_status",
    "country_of_domicile", "academic_level", "month_of_entry", "mode_of_attendance",
    "applications", "offers", "replies", "acceptances", "deferred"
]

METRICS = ["applications", "offers", "replies", "acceptances"]
STATUS_COLUMNS = [
    "status_new", "status_in_review", "status_conditional_offer",
    "status_unconditional_offer", "status_rejected", "status_withdrawn"
]


def aggregate_metrics(df: pd.DataFrame) -> dict[str, float]:
    return {metric: float(df[metric].fillna(0).sum()) for metric in METRICS}


def comparison_summary(df: pd.DataFrame, current_cycle: int, previous_cycle: int, week: int) -> pd.DataFrame:
    current = aggregate_metrics(df[(df.cycle == current_cycle) & (df.cycle_week == week)])
    previous = aggregate_metrics(df[(df.cycle == previous_cycle) & (df.cycle_week == week)])
    rows = []
    for metric in METRICS:
        change = pct_change(current[metric], previous[metric])
        rows.append({
            "Metric": metric.replace("_", " ").title(),
            "Current cycle": int(current[metric]),
            "Previous cycle": int(previous[metric]),
            "Change": fmt_change(change),
        })
    return pd.DataFrame(rows)


def cycle_summary(df: pd.DataFrame, selected_cycles: list[int], week: int) -> pd.DataFrame:
    view = df[(df.cycle.isin(selected_cycles)) & (df.cycle_week == week)]
    out = view.groupby(["cycle", "fee_status"], as_index=False)[METRICS].sum()
    return out.sort_values(["cycle", "fee_status"], ascending=[False, True])


def status_summary(df: pd.DataFrame, selected_cycles: list[int], week: int) -> pd.DataFrame:
    view = df[(df.cycle.isin(selected_cycles)) & (df.cycle_week == week)]
    available = [c for c in STATUS_COLUMNS if c in view.columns]
    out = view.groupby(["cycle", "course_code", "course_name"], as_index=False)[available + METRICS].sum()
    return out.sort_values(["course_name", "cycle"], ascending=[True, False])


def deferral_summary(df: pd.DataFrame, cycle: int, week: int) -> pd.DataFrame:
    view = df[(df.population == "UG") & (df.cycle == cycle) & (df.cycle_week == week)].copy()
    if view.empty:
        return pd.DataFrame(columns=["Academic year of entry", "Fee status", "Deferred applications"])
    view["Academic year of entry"] = view.apply(lambda r: str(int(r["cycle"]) + 1) if int(r["deferred"]) > 0 else str(int(r["cycle"])), axis=1)
    out = view.groupby(["Academic year of entry", "fee_status"], as_index=False)["deferred"].sum()
    return out.rename(columns={"fee_status": "Fee status", "deferred": "Deferred applications"})


def latest_snapshot_dates(df: pd.DataFrame, current_cycle: int, previous_cycle: int, week: int) -> tuple[str, str]:
    def one(cycle: int) -> str:
        vals = df[(df.cycle == cycle) & (df.cycle_week == week)]["snapshot_date"]
        return "N/A" if vals.empty else str(vals.iloc[0])
    return one(current_cycle), one(previous_cycle)


def pdf_summary_bytes(title: str, filter_note: str, summary: pd.DataFrame, detail: pd.DataFrame) -> bytes:
    buff = BytesIO()
    doc = SimpleDocTemplate(buff, pagesize=landscape(A4), rightMargin=1.2 * cm, leftMargin=1.2 * cm, topMargin=1.2 * cm, bottomMargin=1.2 * cm)
    styles = getSampleStyleSheet()
    elems = [Paragraph(title, styles["Title"]), Spacer(1, 0.3 * cm), Paragraph(filter_note, styles["BodyText"]), Spacer(1, 0.3 * cm)]
    elems.append(Paragraph("Summary", styles["Heading2"]))
    elems.append(_df_table(summary))
    elems.append(Spacer(1, 0.4 * cm))
    elems.append(Paragraph("Filtered detail (first 35 rows)", styles["Heading2"]))
    elems.append(_df_table(detail.head(35)))
    doc.build(elems)
    return buff.getvalue()


def _df_table(df: pd.DataFrame) -> Table:
    safe = df.copy().fillna("").astype(str)
    data = [list(safe.columns)] + safe.values.tolist()
    col_widths = [min(5.2 * cm, max(1.4 * cm, len(str(col)) * 0.12 * cm)) for col in safe.columns]
    table = Table(data, repeatRows=1, colWidths=col_widths)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
    ]))
    return table
