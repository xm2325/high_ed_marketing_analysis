"""Scenario calculations for the public-data evidence-to-strategy tool.

The functions deliberately separate public evidence from scenario assumptions.
No slider value is presented as an estimated causal effect.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import pandas as pd

@dataclass(frozen=True)
class ConversionScenario:
    offer_holders: int
    baseline_firm_rate: float
    contacted_share: float
    fee_guidance_uplift_pp: float
    accommodation_uplift_pp: float
    subject_value_uplift_pp: float


def simulate_offer_holder_conversion(s: ConversionScenario) -> dict[str, float]:
    """Return scenario output using explicitly user-chosen percentage-point assumptions."""
    baseline_firms = s.offer_holders * s.baseline_firm_rate
    contacted = s.offer_holders * s.contacted_share
    total_uplift_pp = s.fee_guidance_uplift_pp + s.accommodation_uplift_pp + s.subject_value_uplift_pp
    scenario_firms = baseline_firms + contacted * total_uplift_pp / 100.0
    scenario_firms = min(float(s.offer_holders), max(0.0, scenario_firms))
    return {
        **asdict(s),
        'baseline_firms': baseline_firms,
        'scenario_firms': scenario_firms,
        'additional_firms': scenario_firms - baseline_firms,
        'scenario_firm_rate': scenario_firms / s.offer_holders if s.offer_holders else 0.0,
        'total_assumed_uplift_pp_for_contacted': total_uplift_pp,
    }


def make_content_plan(audience: str, include_fee: bool, include_accommodation: bool, include_rankings: bool, include_contextual: bool) -> pd.DataFrame:
    rows=[]
    if include_fee:
        rows.append({'week':'T-6 weeks','audience':audience,'message':'Fee-value and affordability guidance','channel':'Email + landing page','success_metric':'Landing-page visits; webinar registrations; firm-choice conversion','evidence_link':'International tuition-fee cost signal'})
    if include_accommodation:
        rows.append({'week':'T-5 weeks','audience':audience,'message':'Accommodation options, booking timeline, and Q&A','channel':'Email + webinar/open-day session','success_metric':'Accommodation-page clicks; session attendance; firm-choice conversion','evidence_link':'Accommodation decision signal'})
    if include_rankings:
        rows.append({'week':'T-4 weeks','audience':audience,'message':'Subject quality, rankings, graduate value, and entry-requirement clarification','channel':'Subject-level email + course landing page','success_metric':'Course-page clicks; FAQ clicks; firm-choice conversion','evidence_link':'FSE rankings and entry-requirements signal'})
    if include_contextual:
        rows.append({'week':'T-3 weeks','audience':audience,'message':'Contextual admissions, bursary, and eligible travel-cost support signposting','channel':'Eligibility-tool prompt + email + outreach','success_metric':'Eligibility-tool clicks; open-day registrations; completed applications','evidence_link':'Access plan and contextual-admissions pages'})
    if not rows:
        rows.append({'week':'T-4 weeks','audience':audience,'message':'General offer-holder follow-up','channel':'Email','success_metric':'Open rate; click rate; firm-choice conversion','evidence_link':'Baseline'})
    return pd.DataFrame(rows)


def make_access_outreach_scenario(segment_size: int, contact_rate: float, current_event_rate: float, assumed_event_uplift_pp: float) -> dict[str, float]:
    baseline_attendees = segment_size * current_event_rate
    contacted = segment_size * contact_rate
    scenario_attendees = baseline_attendees + contacted * assumed_event_uplift_pp / 100.0
    scenario_attendees = min(float(segment_size), max(0.0, scenario_attendees))
    return {
        'segment_size': segment_size,
        'contacted': contacted,
        'baseline_attendees': baseline_attendees,
        'scenario_attendees': scenario_attendees,
        'additional_attendees': scenario_attendees - baseline_attendees,
    }
