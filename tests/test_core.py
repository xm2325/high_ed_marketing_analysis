from __future__ import annotations

import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app_utils import pct_change, safe_div
from calendar_tools import build_utm_url, calendar_to_ics, normalise_calendar
from crm_tools import crm_quality_issues, triage_leads
from strategy_tools import OfferHolderScenario, simulate_offer_holder


def test_safe_percentage_change_handles_zero_denominator():
    assert pct_change(10, 0) is None
    assert safe_div(2, 0) is None


def test_utm_builder_preserves_external_url_and_adds_tags():
    url = build_utm_url("https://example.org/page", "email", "sequence", "ug_2026", "open_day")
    assert "utm_source=email" in url
    assert "utm_medium=sequence" in url
    assert "utm_campaign=ug_2026" in url
    assert "utm_content=open_day" in url


def test_calendar_ics_contains_event():
    df = pd.DataFrame([{
        "start_date": "2026-07-02", "end_date": "2026-07-02", "event": "Clearing opens", "population": "UG",
        "audience": "Clearing prospects", "phase": "Clearing", "channel": "Email", "owner_team": "Marketing",
        "primary_kpi": "Registrations", "recommended_action": "Launch journey", "date_type": "Official public date", "source_id": "source"
    }])
    payload = calendar_to_ics(df).decode("utf-8")
    assert "BEGIN:VCALENDAR" in payload
    assert "SUMMARY:Clearing opens" in payload


def test_offer_holder_scenario_additional_firms_positive():
    out = simulate_offer_holder(OfferHolderScenario(5000, .35, .6, 1, 1.5, .5, 120))
    assert round(out["baseline_firms"]) == 1750
    assert round(out["additional_firms"]) == 90


def test_crm_triage_and_quality_issue_detection():
    df = pd.DataFrame([{
        "lead_id": "x1", "population": "UG", "audience_stage": "Offer-holder", "subject_area": "Engineering",
        "course_interest": "BEng", "campaign_source": "Email", "utm_campaign": "test", "domicile_group": "UK",
        "email": "bad-email", "consent_status": "unknown", "page_views": 10, "last_activity_days": 3,
        "email_opened": True, "email_clicked": True, "form_started": True, "form_completed": False,
        "event_registered": False, "offer_holder": True, "accommodation_page_view": False, "funding_page_view": False,
    }])
    issues = crm_quality_issues(df)
    triaged = triage_leads(df)
    assert len(issues) >= 2
    assert triaged.loc[0, "priority_level"] == "Data check"

from marketing_action_tools import (
    action_plan_to_calendar,
    build_action_plan,
    build_measurement_plan,
    build_workflow_rules,
    get_playbook,
    list_objectives,
)


def test_marketing_action_centre_builds_timed_playbook_and_measurement_plan():
    objective = "Improve international offer-holder conversion"
    playbook = get_playbook(objective)
    plan = build_action_plan(objective, playbook.default_anchor_date, .60, 5000, 120)
    measurement = build_measurement_plan(objective, "Randomised A/B test")
    workflow = build_workflow_rules(objective)
    assert len(list_objectives()) >= 5
    assert len(plan) >= 5
    assert plan.loc[0, "targeted_records"] == 3000
    assert "firm_choice" in set(measurement["field"])
    assert workflow.loc[0, "primary_kpi"] == "Firm-choice conversion"


def test_marketing_action_playbook_exports_to_ics_calendar_schema():
    objective = "Recover incomplete enquiry or support forms"
    playbook = get_playbook(objective)
    plan = build_action_plan(objective, playbook.default_anchor_date, .75, 1000, 50)
    calendar = action_plan_to_calendar(plan)
    payload = calendar_to_ics(calendar).decode("utf-8")
    assert "BEGIN:VCALENDAR" in payload
    assert "Send automated reminder with direct form link" in payload
