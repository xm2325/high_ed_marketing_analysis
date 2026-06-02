"""Reusable helpers for the interactive CRM tool."""

from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

import pandas as pd

try:
    from .rule_based_triage import triage_score
    from .workflow_rules import assign_action
except ImportError:  # allows Streamlit to import from src on sys.path
    from rule_based_triage import triage_score
    from workflow_rules import assign_action

REQUIRED_UPLOAD_COLUMNS = [
    "lead_id",
    "subject_area",
    "course_interest",
    "campaign_source",
    "domicile_group",
    "page_views",
    "last_activity_days",
    "consent_status",
    "email_opened",
    "email_clicked",
    "event_attended",
    "prospectus_downloaded",
    "form_completed",
    "application_submitted",
]

BOOLEAN_COLUMNS = [
    "email_opened",
    "email_clicked",
    "event_attended",
    "prospectus_downloaded",
    "form_completed",
    "application_submitted",
]

DEFAULTS = {
    "lead_id": "manual_001",
    "subject_area": "Business and Management",
    "course_interest": "BSc Management",
    "campaign_source": "Open Day",
    "domicile_group": "UK",
    "page_views": 6,
    "last_activity_days": 14,
    "consent_status": "yes",
    "email_opened": True,
    "email_clicked": True,
    "event_attended": False,
    "prospectus_downloaded": True,
    "form_completed": False,
    "application_submitted": False,
}


def make_upload_template() -> pd.DataFrame:
    """Return a small editable upload template."""
    rows = [
        {
            **DEFAULTS,
            "lead_id": "manual_001",
            "subject_area": "Computer Science and AI",
            "course_interest": "MSc Data Science",
            "campaign_source": "Webinar",
            "page_views": 12,
            "last_activity_days": 5,
            "event_attended": True,
            "form_completed": False,
        },
        {
            **DEFAULTS,
            "lead_id": "manual_002",
            "subject_area": "Business and Management",
            "course_interest": "BSc Management",
            "campaign_source": "Paid Search",
            "page_views": 4,
            "last_activity_days": 28,
            "email_clicked": False,
            "prospectus_downloaded": False,
        },
        {
            **DEFAULTS,
            "lead_id": "manual_003",
            "subject_area": "Psychology",
            "course_interest": "BSc Psychology",
            "campaign_source": "Open Day",
            "domicile_group": "International",
            "page_views": 18,
            "last_activity_days": 3,
            "event_attended": True,
            "form_completed": True,
        },
    ]
    return pd.DataFrame(rows, columns=REQUIRED_UPLOAD_COLUMNS)


def missing_upload_columns(columns: Iterable[str]) -> list[str]:
    """Return required columns not found in an uploaded file."""
    present = set(columns)
    return [col for col in REQUIRED_UPLOAD_COLUMNS if col not in present]


def _to_bool(value) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "y", "true", "1", "t"}
    if pd.isna(value):
        return False
    return bool(value)


def prepare_uploaded_leads(df: pd.DataFrame) -> pd.DataFrame:
    """Clean a small uploaded or edited lead table for scoring."""
    out = df.copy()
    for col, default in DEFAULTS.items():
        if col not in out.columns:
            out[col] = default
        out[col] = out[col].fillna(default)

    for col in BOOLEAN_COLUMNS:
        out[col] = out[col].map(_to_bool)

    out["page_views"] = pd.to_numeric(out["page_views"], errors="coerce").fillna(DEFAULTS["page_views"]).clip(lower=0)
    out["last_activity_days"] = (
        pd.to_numeric(out["last_activity_days"], errors="coerce")
        .fillna(DEFAULTS["last_activity_days"])
        .clip(lower=0)
        .astype(int)
    )
    out["consent_status"] = out["consent_status"].astype(str).str.lower().replace({"true": "yes", "false": "no"})
    return out[REQUIRED_UPLOAD_COLUMNS]


def score_and_assign_uploaded_leads(df: pd.DataFrame) -> pd.DataFrame:
    """Score an uploaded lead table and assign workflow actions."""
    prepared = prepare_uploaded_leads(df)
    scored_rows = []
    for row in prepared.to_dict(orient="records"):
        row["lead_score"] = triage_score(row)
        action = asdict(assign_action(row))
        row.update(action)
        scored_rows.append(row)
    out = pd.DataFrame(scored_rows)
    sort_cols = ["priority_level", "lead_score", "last_activity_days"]
    return out.sort_values(sort_cols, ascending=[True, False, True]).reset_index(drop=True)
