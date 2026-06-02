from __future__ import annotations

import numpy as np
import pandas as pd

CRM_REQUIRED = [
    "lead_id", "population", "audience_stage", "subject_area", "course_interest",
    "campaign_source", "utm_campaign", "domicile_group", "email", "consent_status",
    "page_views", "last_activity_days", "email_opened", "email_clicked", "form_started",
    "form_completed", "event_registered", "offer_holder", "accommodation_page_view", "funding_page_view"
]


def crm_quality_issues(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    duplicated = df["lead_id"].duplicated(keep=False) if "lead_id" in df else pd.Series(False, index=df.index)
    for idx, row in df.iterrows():
        lead_id = str(row.get("lead_id", f"row_{idx}"))
        if duplicated.loc[idx]:
            rows.append({"lead_id": lead_id, "issue": "Duplicate lead ID", "severity": "High", "recommended_fix": "Merge or remove duplicate record before follow-up."})
        if str(row.get("consent_status", "")).lower() not in {"yes", "no"}:
            rows.append({"lead_id": lead_id, "issue": "Unknown consent status", "severity": "High", "recommended_fix": "Check consent before marketing communication."})
        email = str(row.get("email", ""))
        if "@" not in email or "." not in email.split("@")[-1]:
            rows.append({"lead_id": lead_id, "issue": "Invalid email", "severity": "Medium", "recommended_fix": "Correct contact details or select a permitted alternative channel."})
        if not str(row.get("course_interest", "")).strip():
            rows.append({"lead_id": lead_id, "issue": "Missing course interest", "severity": "Medium", "recommended_fix": "Request or infer course-interest field using approved process."})
        if float(row.get("last_activity_days", 0) or 0) > 45:
            rows.append({"lead_id": lead_id, "issue": "Stale record", "severity": "Low", "recommended_fix": "Review whether the record remains suitable for nurture communication."})
    return pd.DataFrame(rows, columns=["lead_id", "issue", "severity", "recommended_fix"])


def triage_leads(df: pd.DataFrame, high_score_threshold: int = 65, inactive_days_threshold: int = 21, weekly_capacity: int = 80) -> pd.DataFrame:
    out = df.copy()
    bool_cols = ["email_opened", "email_clicked", "form_started", "form_completed", "event_registered", "offer_holder", "accommodation_page_view", "funding_page_view"]
    for col in bool_cols:
        out[col] = out[col].map(_to_bool)
    score = (
        out["page_views"].fillna(0).clip(0, 25) * 1.2
        + out["email_opened"].astype(int) * 8
        + out["email_clicked"].astype(int) * 16
        + out["form_started"].astype(int) * 11
        + out["event_registered"].astype(int) * 14
        + out["offer_holder"].astype(int) * 16
        + out["accommodation_page_view"].astype(int) * 5
        + out["funding_page_view"].astype(int) * 5
        - out["last_activity_days"].fillna(0).clip(0, 60) * 0.6
    )
    out["lead_score"] = score.round(1).clip(0, 100)
    issues = crm_quality_issues(out)
    issue_leads = set(issues[issues.severity == "High"].lead_id) if not issues.empty else set()
    priorities = []
    actions = []
    reasons = []
    owners = []
    for _, row in out.iterrows():
        lead_id = row["lead_id"]
        consent = str(row["consent_status"]).lower()
        if lead_id in issue_leads or consent != "yes":
            priorities.append("Data check")
            actions.append("Check record and consent before marketing follow-up")
            reasons.append("Record has a high-priority data-quality or consent issue")
            owners.append("CRM support")
        elif bool(row["offer_holder"]) and float(row["last_activity_days"]) <= inactive_days_threshold:
            priorities.append("P1")
            actions.append("Offer-holder adviser follow-up")
            reasons.append("Recent offer-holder engagement")
            owners.append("Recruitment adviser")
        elif float(row["lead_score"]) >= high_score_threshold and not bool(row["form_completed"]):
            priorities.append("P1")
            actions.append("Send consent-aware form completion reminder")
            reasons.append("High engagement with incomplete form")
            owners.append("Marketing automation")
        elif bool(row["email_clicked"]) or bool(row["event_registered"]):
            priorities.append("P2")
            actions.append("Add to segmented nurture sequence")
            reasons.append("Observed engagement signal")
            owners.append("Student Marketing")
        else:
            priorities.append("P3")
            actions.append("Retain in low-frequency nurture pool")
            reasons.append("Limited recent engagement")
            owners.append("Student Marketing")
    out["priority_level"] = priorities
    out["recommended_action"] = actions
    out["reason"] = reasons
    out["owner_team"] = owners
    out["next_review_days"] = out["priority_level"].map({"Data check": 1, "P1": 2, "P2": 7, "P3": 21})
    rank = out["priority_level"].map({"Data check": 0, "P1": 1, "P2": 2, "P3": 3})
    out = out.assign(_rank=rank).sort_values(["_rank", "lead_score"], ascending=[True, False]).drop(columns="_rank")
    actionable = out[out.priority_level == "P1"].head(int(weekly_capacity)).lead_id
    out["selected_for_weekly_worklist"] = out.lead_id.isin(set(actionable))
    return out.reset_index(drop=True)


def _to_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in {"true", "1", "yes", "y"}
