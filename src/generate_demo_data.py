"""Generate deterministic synthetic datasets for the public portfolio demo.

These records are not University of Manchester internal records. They are designed
only to demonstrate the filters and workflows described in publicly accessible
reporting guidance and the uploaded admissions app user guide.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "data" / "demo"
UPLOAD = ROOT / "data" / "upload_schema"
DEMO.mkdir(parents=True, exist_ok=True)
UPLOAD.mkdir(parents=True, exist_ok=True)

RNG = np.random.default_rng(42)

COURSES = [
    ("UG", "Faculty of Science and Engineering", "School of Engineering", "Mechanical Engineering", "Mechanical Engineering", "H300", "BEng Mechanical Engineering"),
    ("UG", "Faculty of Science and Engineering", "School of Engineering", "Electrical and Electronic Engineering", "Electrical and Electronic Engineering", "H600", "BEng Electrical and Electronic Engineering"),
    ("UG", "Faculty of Science and Engineering", "School of Engineering", "Computer Science", "Computer Science", "G400", "BSc Computer Science"),
    ("UG", "Faculty of Biology, Medicine and Health", "School of Medical Sciences", "Medicine", "Medicine", "A106", "MBChB Medicine"),
    ("UG", "Faculty of Biology, Medicine and Health", "School of Medical Sciences", "Dentistry", "Dentistry", "A206", "BDS Dentistry"),
    ("UG", "Faculty of Biology, Medicine and Health", "School of Biological Sciences", "Biological Sciences", "Biomedical Sciences", "B940", "BSc Biomedical Sciences"),
    ("UG", "Faculty of Humanities", "Alliance Manchester Business School", "Management", "Management", "N201", "BSc Management"),
    ("UG", "Faculty of Humanities", "School of Arts, Languages and Cultures", "Languages", "Languages", "R110", "BA French Studies"),
    ("PGT", "Faculty of Science and Engineering", "School of Engineering", "Computer Science", "Artificial Intelligence", "PG-AI", "MSc Artificial Intelligence"),
    ("PGT", "Faculty of Humanities", "Alliance Manchester Business School", "Management", "Business Analytics", "PG-BA", "MSc Business Analytics"),
    ("PGT", "Faculty of Biology, Medicine and Health", "School of Health Sciences", "Public Health", "Public Health", "PG-PH", "MPH Public Health"),
    ("PGR", "Faculty of Science and Engineering", "School of Engineering", "Computer Science", "Computer Science", "PGR-CS", "PhD Computer Science"),
    ("PGR", "Faculty of Humanities", "Alliance Manchester Business School", "Management", "Management", "PGR-MGT", "PhD Management"),
]

COUNTRIES = {
    "Home": ["United Kingdom"],
    "Overseas": ["China", "India", "United States", "Malaysia", "Hong Kong", "United Arab Emirates", "Singapore", "Nigeria", "Saudi Arabia", "Canada"],
    "Pending assessment": ["Pending fee assessment"],
}

BASE_FINAL = {
    "UG": 920,
    "PGT": 410,
    "PGR": 92,
}


def logistic_progress(week: int, population: str) -> float:
    midpoint = {"UG": 13.0, "PGT": 20.0, "PGR": 21.0}[population]
    steepness = {"UG": 0.23, "PGT": 0.15, "PGR": 0.13}[population]
    return float(1 / (1 + np.exp(-steepness * (week - midpoint))))


def make_admissions_demo() -> pd.DataFrame:
    rows: list[dict] = []
    cycle_start = {2023: "2022-09-26", 2024: "2023-09-25", 2025: "2024-09-30", 2026: "2025-09-29"}
    for population, faculty, school, department, sub_department, code, course in COURSES:
        course_scale = RNG.uniform(0.7, 1.35)
        if code in {"A106", "A206"}:
            course_scale *= 1.9
        for cycle in [2023, 2024, 2025, 2026]:
            cycle_scale = {2023: 0.91, 2024: 0.96, 2025: 1.0, 2026: 1.04}[cycle]
            for fee_status, fee_scale in [("Home", 0.67), ("Overseas", 0.29), ("Pending assessment", 0.04)]:
                for week in range(1, 41):
                    final_apps = BASE_FINAL[population] * course_scale * cycle_scale * fee_scale
                    applications = max(0, int(round(final_apps * logistic_progress(week, population) + RNG.normal(0, 2))))
                    offer_rate = {"UG": 0.48, "PGT": 0.56, "PGR": 0.34}[population]
                    if code in {"A106", "A206"}:
                        offer_rate *= 0.44
                    offer_rate *= {"Home": 1.0, "Overseas": 0.82, "Pending assessment": 0.65}[fee_status]
                    maturation = max(0.0, min(1.0, (week - 5) / 22))
                    offers = int(round(applications * offer_rate * maturation))
                    replies = int(round(offers * max(0.0, min(0.92, (week - 10) / 25))))
                    accepts = int(round(replies * {"UG": 0.72, "PGT": 0.67, "PGR": 0.61}[population]))
                    deferred = int(round(accepts * (0.055 if population == "UG" else 0.025)))
                    rejected = max(0, int(round(applications * 0.22 * maturation)))
                    withdrawn = max(0, int(round(applications * 0.035 * maturation)))
                    in_review = max(0, applications - offers - rejected - withdrawn)
                    cond = int(round(offers * 0.82))
                    uncond = max(0, offers - cond)
                    new = max(0, int(round(applications * max(0.0, 0.22 - week / 250))))
                    country = COUNTRIES[fee_status][(hash((code, cycle, week, fee_status)) % len(COUNTRIES[fee_status]))]
                    academic_level = "Year 0/1" if population == "UG" and hash((code, week, cycle)) % 5 else "Year 2+"
                    if population != "UG":
                        academic_level = "Not applicable"
                    month_of_entry = "September" if population == "UG" else ["September", "January", "April"][hash((code, cycle, fee_status)) % 3]
                    mode = "FT" if population == "UG" else ["FT", "PT", "DL FT", "DL PT"][hash((code, cycle, fee_status, "mode")) % 4]
                    snapshot_date = pd.Timestamp(cycle_start[cycle]) + pd.Timedelta(days=7 * (week - 1))
                    rows.append({
                        "population": population,
                        "cycle": cycle,
                        "cycle_week": week,
                        "snapshot_date": snapshot_date.date().isoformat(),
                        "faculty": faculty,
                        "school": school,
                        "department": department,
                        "sub_department": sub_department,
                        "course_code": code,
                        "course_name": course,
                        "fee_status": fee_status,
                        "country_of_domicile": country,
                        "academic_level": academic_level,
                        "month_of_entry": month_of_entry,
                        "mode_of_attendance": mode,
                        "applications": applications,
                        "offers": offers,
                        "replies": replies,
                        "acceptances": accepts,
                        "status_new": new,
                        "status_in_review": in_review,
                        "status_conditional_offer": cond,
                        "status_unconditional_offer": uncond,
                        "status_rejected": rejected,
                        "status_withdrawn": withdrawn,
                        "deferred": deferred,
                        "target": int(round(final_apps * 0.49)),
                        "provisional_student_number": int(round(final_apps * 0.47)),
                        "data_mode": "Synthetic demonstration",
                    })
    return pd.DataFrame(rows)


def make_crm_demo(n: int = 240) -> pd.DataFrame:
    sources = ["Open Day", "Webinar", "Paid Search", "Organic Search", "School Outreach", "Clearing Updates", "Email Newsletter"]
    subjects = ["Engineering", "Computer Science", "Life Sciences", "Business", "Medicine", "Humanities"]
    courses = ["BEng Mechanical Engineering", "BSc Computer Science", "BSc Biomedical Sciences", "BSc Management", "MBChB Medicine", "BA French Studies"]
    doms = ["UK", "International", "EU"]
    rows = []
    for i in range(n):
        subject_idx = int(RNG.integers(0, len(subjects)))
        consent = RNG.choice(["yes", "no", "unknown"], p=[0.88, 0.04, 0.08])
        email = f"student{i+1:03d}@example.org" if RNG.random() > 0.035 else "invalid-email"
        source = RNG.choice(sources)
        audience = RNG.choice(["Prospective student", "Applicant", "Offer-holder", "Clearing registrant"], p=[0.42, 0.28, 0.22, 0.08])
        rows.append({
            "lead_id": f"demo_{i+1:04d}",
            "population": RNG.choice(["UG", "PGT", "PGR"], p=[0.72, 0.22, 0.06]),
            "audience_stage": audience,
            "subject_area": subjects[subject_idx],
            "course_interest": courses[subject_idx],
            "campaign_source": source,
            "utm_campaign": f"{source.lower().replace(' ', '_')}_2026",
            "domicile_group": RNG.choice(doms, p=[0.58, 0.36, 0.06]),
            "email": email,
            "consent_status": consent,
            "page_views": int(RNG.integers(0, 28)),
            "last_activity_days": int(RNG.integers(0, 61)),
            "email_opened": bool(RNG.random() < 0.62),
            "email_clicked": bool(RNG.random() < 0.39),
            "form_started": bool(RNG.random() < 0.52),
            "form_completed": bool(RNG.random() < 0.34),
            "event_registered": bool(RNG.random() < 0.26),
            "offer_holder": audience == "Offer-holder",
            "accommodation_page_view": bool(RNG.random() < 0.22),
            "funding_page_view": bool(RNG.random() < 0.19),
        })
    # add one duplicate to demonstrate data checks
    rows.append(dict(rows[7]))
    return pd.DataFrame(rows)


def make_digital_demo() -> pd.DataFrame:
    campaigns = [
        ("ug_2026_open_day_june", "Prospective students", "Email", "Open Day"),
        ("ug_2026_international_fees", "International offer-holders", "Email", "Fee-value guidance"),
        ("ug_2026_accommodation_webinar", "Offer-holders", "Email", "Accommodation webinar"),
        ("ug_2026_clearing_updates", "Clearing prospects", "Paid Search", "Clearing updates"),
        ("ug_2026_contextual_support", "Contextual admissions prospects", "School outreach", "Contextual support"),
        ("pgt_2026_business_webinar", "PGT prospects", "Organic Search", "PGT webinar"),
    ]
    rows = []
    for day in pd.date_range("2026-04-01", "2026-07-15", freq="7D"):
        for campaign, audience, channel, content in campaigns:
            impressions = int(RNG.integers(700, 7000))
            sessions = int(impressions * RNG.uniform(0.06, 0.28))
            lpv = int(sessions * RNG.uniform(0.72, 0.98))
            starts = int(lpv * RNG.uniform(0.12, 0.44))
            completions = int(starts * RNG.uniform(0.42, 0.84))
            registrations = int(completions * RNG.uniform(0.08, 0.55))
            applications = int(completions * RNG.uniform(0.05, 0.32))
            rows.append({
                "date": day.date().isoformat(),
                "campaign": campaign,
                "audience": audience,
                "channel": channel,
                "content": content,
                "impressions": impressions,
                "sessions": sessions,
                "landing_page_views": lpv,
                "form_starts": starts,
                "form_completions": completions,
                "event_registrations": registrations,
                "applications": applications,
                "opt_outs": int(max(0, RNG.normal(4, 2))),
                "data_mode": "Synthetic GA4-style demonstration",
            })
    return pd.DataFrame(rows)


def make_calendar_enriched() -> pd.DataFrame:
    rows = [
        ("2025-09-02", "2025-09-02", "UCAS applications open", "UG", "Prospective students", "Discovery", "Email + landing page", "Student Marketing", "Course-page visits", "Launch course discovery journey", "Official public date", "uom_ug_applying_2026"),
        ("2025-10-15", "2025-10-15", "Medicine and Dentistry deadline", "UG", "Medicine and Dentistry applicants", "Application", "Email", "Admissions + Marketing", "Application completions", "Send final form-completeness reminder", "Official public date", "uom_ug_applying_2026"),
        ("2026-01-14", "2026-01-14", "UG equal-consideration deadline", "UG", "Most undergraduate applicants", "Application", "Email + landing page", "Student Marketing", "Application completions", "Send final application support reminder", "Official public date", "uom_ug_applying_2026"),
        ("2026-02-26", "2026-02-26", "UCAS Extra opens", "UG", "Eligible applicants without offers", "Application", "Email + landing page", "Student Marketing", "Course discovery clicks", "Explain eligibility and course discovery", "Official public date", "uom_ug_applying_2026"),
        ("2026-05-13", "2026-05-13", "University decision day", "UG", "On-time undergraduate applicants", "Decision", "Email", "Admissions + Marketing", "Journey activation rate", "Start segmented offer-holder and unsuccessful-applicant journeys", "Official public date", "uom_ug_applying_2026"),
        ("2026-06-03", "2026-06-03", "Replying to an offer deadline", "UG", "Offer-holders receiving decisions by 13 May", "Offer-holder conversion", "Email", "Student Marketing", "Reply completion", "Final consent-aware reminder", "Official public date", "uom_ug_applying_2026"),
        ("2026-06-27", "2026-06-27", "Undergraduate open day", "UG", "Prospective students", "Awareness and consideration", "Open Day + email", "Events + Marketing", "Registrations and attendance", "Registration prompt and post-event follow-up", "Official public date", "uom_open_days_2026"),
        ("2026-06-30", "2026-06-30", "Application deadline for 2026", "UG", "Late undergraduate applicants", "Application", "Email + landing page", "Student Marketing", "Application completions", "Explain clearing transition", "Official public date", "uom_ug_applying_2026"),
        ("2026-07-02", "2026-07-02", "Early Clearing opens; Manchester list goes live", "UG", "Clearing prospects", "Clearing", "Email + paid search + landing page", "Clearing team + Marketing", "Clearing update registrations", "Launch Clearing update journey and live course link", "Official public date", "uom_clearing_2026"),
        ("2026-07-04", "2026-07-04", "Undergraduate open day", "UG", "Prospective students", "Awareness and consideration", "Open Day + email", "Events + Marketing", "Registrations and attendance", "Registration prompt and post-event follow-up", "Official public date", "uom_open_days_2026"),
        ("2026-07-06", "2026-07-10", "Virtual undergraduate open days", "UG", "Prospective students unable to attend in person", "Awareness and consideration", "Virtual event + email", "Events + Marketing", "Session registrations", "Send topic-level registration prompts", "Official public date", "uom_open_days_2026"),
        ("2026-09-24", "2026-09-24", "Final date for applications", "UG", "Late applicants", "Clearing", "Email + landing page", "Clearing team", "Completed applications", "Final late-stage reminder", "Official public date", "uom_clearing_2026"),
        ("2026-10-03", "2026-10-03", "Undergraduate open day", "UG", "Prospective students", "Awareness and consideration", "Open Day + email", "Events + Marketing", "Registrations", "Registration prompt when booking opens", "Official public date", "uom_open_days_2026"),
        ("2026-10-10", "2026-10-10", "Undergraduate open day", "UG", "Prospective students", "Awareness and consideration", "Open Day + email", "Events + Marketing", "Registrations", "Registration prompt when booking opens", "Official public date", "uom_open_days_2026"),
        ("2026-10-19", "2026-10-19", "Clearing closes", "UG", "Clearing prospects", "Clearing", "Email", "Clearing team", "Journey evaluation", "Close campaign and report outcomes", "Official public date", "uom_clearing_2026"),
        ("2026-11-16", "2026-11-20", "Virtual undergraduate open days", "UG", "Prospective students unable to attend in person", "Awareness and consideration", "Virtual event + email", "Events + Marketing", "Session registrations", "Send topic-level registration prompts", "Official public date", "uom_open_days_2026"),
        ("2026-07-15", "2026-07-15", "PGT webinar planning checkpoint", "PGT", "PGT prospects", "Discovery", "Webinar + email", "Faculty Marketing", "Webinar registrations", "Example editable planning event", "Planning template", "custom_template"),
    ]
    cols = ["start_date", "end_date", "event", "population", "audience", "phase", "channel", "owner_team", "primary_kpi", "recommended_action", "date_type", "source_id"]
    return pd.DataFrame(rows, columns=cols)


def main() -> None:
    admissions = make_admissions_demo()
    admissions.to_csv(DEMO / "synthetic_admissions_operations.csv", index=False)
    admissions.head(160).to_csv(UPLOAD / "admissions_upload_template.csv", index=False)
    crm = make_crm_demo()
    crm.to_csv(DEMO / "synthetic_crm_records.csv", index=False)
    crm.head(25).to_csv(UPLOAD / "crm_upload_template.csv", index=False)
    digital = make_digital_demo()
    digital.to_csv(DEMO / "synthetic_digital_journey.csv", index=False)
    digital.head(40).to_csv(UPLOAD / "digital_analytics_upload_template.csv", index=False)
    calendar = make_calendar_enriched()
    calendar.to_csv(DEMO / "campaign_calendar_enriched.csv", index=False)
    calendar.head(5).to_csv(UPLOAD / "campaign_calendar_upload_template.csv", index=False)
    print(f"Generated {len(admissions):,} admissions rows, {len(crm):,} CRM rows, {len(digital):,} digital rows and {len(calendar):,} calendar rows.")

if __name__ == "__main__":
    main()
