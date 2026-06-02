"""Small rule-based score for the interactive single-lead sandbox."""

from __future__ import annotations

import math
from typing import Any


def triage_score(row: dict[str, Any]) -> float:
    """Return a transparent lead score for an entered lead.

    This is not the trained model. It is a simple sandbox score used in the
    dashboard to explain how CRM signals can change priority.
    """
    page_views = float(row.get("page_views", 0) or 0)
    last_activity_days = float(row.get("last_activity_days", 120) or 120)
    raw = (
        -2.05
        + 0.22 * math.log1p(page_views)
        + 0.50 * int(bool(row.get("email_opened", False)))
        + 0.70 * int(bool(row.get("email_clicked", False)))
        + 0.80 * int(bool(row.get("event_attended", False)))
        + 0.45 * int(bool(row.get("prospectus_downloaded", False)))
        + 0.85 * int(bool(row.get("form_completed", False)))
        - 0.012 * last_activity_days
    )
    return round(1 / (1 + math.exp(-raw)), 3)
