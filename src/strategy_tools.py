from __future__ import annotations

from dataclasses import dataclass, asdict
import pandas as pd


@dataclass
class OfferHolderScenario:
    cohort_size: int
    current_firm_rate: float
    targeted_share: float
    fee_value_uplift_pp: float
    accommodation_uplift_pp: float
    subject_content_uplift_pp: float
    adviser_capacity: int


def simulate_offer_holder(s: OfferHolderScenario) -> dict:
    total_uplift = max(0.0, s.fee_value_uplift_pp + s.accommodation_uplift_pp + s.subject_content_uplift_pp) / 100
    scenario_rate = min(1.0, s.current_firm_rate + s.targeted_share * total_uplift)
    baseline = s.cohort_size * s.current_firm_rate
    scenario = s.cohort_size * scenario_rate
    contacted = s.cohort_size * s.targeted_share
    adviser_reviews = min(int(round(contacted * 0.08)), int(s.adviser_capacity))
    out = asdict(s)
    out.update({
        "baseline_firms": baseline,
        "scenario_firms": scenario,
        "additional_firms": scenario - baseline,
        "scenario_firm_rate": scenario_rate,
        "contacted_offer_holders": contacted,
        "estimated_adviser_reviews": adviser_reviews,
    })
    return out


def campaign_plan(audience: str, include_fee: bool, include_accommodation: bool, include_subject: bool, include_contextual: bool) -> pd.DataFrame:
    rows = []
    if include_fee:
        rows.append([audience, "Post-offer", "Fee-value guidance and eligible funding signposting", "Email + landing page", "T-6 weeks", "Click-through rate", "Student Marketing", "Test variant internally"])
    if include_accommodation:
        rows.append([audience, "Post-offer", "Accommodation timeline, bursary signposting and Q&A registration", "Email + webinar", "T-5 weeks", "Webinar registrations", "Student Marketing + Accommodation", "Test variant internally"])
    if include_subject:
        rows.append([audience, "Post-offer", "Subject-value content and entry-requirement FAQ", "Segmented email", "T-4 weeks", "Firm-choice conversion", "Faculty Marketing", "Test variant internally"])
    if include_contextual:
        rows.append([audience, "Pre-application", "Contextual admissions, bursary and eligible travel support signposting", "Email + official guidance page", "Before Open Day", "Guidance-page visits", "Access and Outreach", "Link to official eligibility checker"])
    rows.append([audience, "Evaluation", "Report delivery, open, click, event registration, conversion and opt-out", "Dashboard", "T+1 week", "Conversion and opt-out rate", "Marketing Analytics", "Use consent-aware internal records"])
    return pd.DataFrame(rows, columns=["Audience", "Stage", "Message", "Channel", "Timing", "Primary KPI", "Owner", "Evaluation note"])


def access_registration_scenario(segment_size: int, contacted_share: float, current_rate: float, uplift_pp: float) -> dict:
    baseline = segment_size * current_rate
    scenario = baseline + segment_size * contacted_share * uplift_pp / 100
    return {"baseline_registrations": baseline, "scenario_registrations": scenario, "additional_registrations": scenario - baseline}
