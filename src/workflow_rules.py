"""CRM-style workflow rules for recruitment marketing follow-up."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ActionResult:
    priority_level: str
    recommended_action: str
    action_reason: str
    owner_team: str
    next_review_days: int


def _yes(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"yes", "y", "true", "1"}
    return bool(value)


def assign_action(row: dict[str, Any]) -> ActionResult:
    """Assign a practical marketing or recruitment action to one lead.

    The rules turn a lead score and CRM signals into a small action queue.
    They are intentionally simple and auditable so non-technical colleagues
    can understand why a recommendation was made.
    """
    score = float(row.get("lead_score", 0.0) or 0.0)
    last_activity_days = int(row.get("last_activity_days", 999) or 999)
    consent = str(row.get("consent_status", "unknown")).lower()
    application_submitted = _yes(row.get("application_submitted", False))
    form_completed = _yes(row.get("form_completed", False))
    email_clicked = _yes(row.get("email_clicked", False))
    email_opened = _yes(row.get("email_opened", False))
    event_attended = _yes(row.get("event_attended", False))
    course_interest = row.get("course_interest", None)

    if consent != "yes":
        return ActionResult(
            priority_level="Data check",
            recommended_action="Check contact consent before marketing follow-up",
            action_reason="Lead has no confirmed marketing consent",
            owner_team="Marketing Operations",
            next_review_days=7,
        )

    if course_interest in {None, "", "Unknown"}:
        return ActionResult(
            priority_level="Data check",
            recommended_action="Update missing course interest in CRM",
            action_reason="Course interest is missing, which limits useful segmentation",
            owner_team="CRM Support",
            next_review_days=7,
        )

    if score >= 0.75 and not application_submitted and last_activity_days <= 21:
        return ActionResult(
            priority_level="P1",
            recommended_action="Recruitment adviser follow-up",
            action_reason="High score, recent activity, and no application submitted",
            owner_team="Recruitment Team",
            next_review_days=3,
        )

    if score >= 0.60 and event_attended and not application_submitted:
        return ActionResult(
            priority_level="P1",
            recommended_action="Invite to application support session",
            action_reason="Event attended and lead score is high, but application is missing",
            owner_team="Student Recruitment",
            next_review_days=5,
        )

    if not form_completed and (email_clicked or email_opened) and score >= 0.45:
        return ActionResult(
            priority_level="P2",
            recommended_action="Send form completion reminder",
            action_reason="Lead engaged with email but has not completed the enquiry form",
            owner_team="Marketing Automation",
            next_review_days=7,
        )

    if score >= 0.45 and not application_submitted and last_activity_days <= 45:
        return ActionResult(
            priority_level="P2",
            recommended_action="Add to subject-specific nurture campaign",
            action_reason="Moderate score and recent activity without application submission",
            owner_team="Campaign Team",
            next_review_days=14,
        )

    if last_activity_days > 60:
        return ActionResult(
            priority_level="P3",
            recommended_action="Move to low-frequency nurture list",
            action_reason="No recent activity for more than 60 days",
            owner_team="Marketing Automation",
            next_review_days=30,
        )

    return ActionResult(
        priority_level="Monitor",
        recommended_action="No immediate action; keep in normal campaign journey",
        action_reason="No strong follow-up trigger found",
        owner_team="Campaign Team",
        next_review_days=21,
    )
