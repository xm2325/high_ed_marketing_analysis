"""Marketing action-centre playbooks for the public portfolio prototype.

The module converts a selected recruitment objective into an operational,
measurement-ready campaign plan. All expected-uplift figures remain editable
planning assumptions rather than measured University treatment effects.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import re
import pandas as pd


@dataclass(frozen=True)
class Playbook:
    objective: str
    audience: str
    problem_statement: str
    trigger: str
    evidence_basis: str
    public_data_boundary: str
    primary_kpi: str
    guardrail_kpi: str
    owner_team: str
    anchor_label: str
    default_anchor_date: date
    workflow_rule: str
    steps: tuple[dict, ...]
    measurement_fields: tuple[str, ...]


def _step(offset_days: int, timing: str, action: str, channel: str, owner: str, kpi: str, status: str = "Planning template") -> dict:
    return {
        "offset_days": offset_days,
        "timing": timing,
        "action": action,
        "channel": channel,
        "owner_team": owner,
        "step_kpi": kpi,
        "status": status,
    }


PLAYBOOKS: dict[str, Playbook] = {
    "Improve international offer-holder conversion": Playbook(
        objective="Improve international offer-holder conversion",
        audience="International offer-holders with no reply and confirmed consent",
        problem_statement="Some international offer-holders may need clearer fee-value, funding, accommodation and subject-level guidance before the reply deadline.",
        trigger="offer_made = yes AND reply_received = no AND domicile_group = International AND consent_status = yes",
        evidence_basis="Published applicant accept/decliner survey signal: tuition-fee cost and accommodation concerns are useful topics for a testable communication plan. The survey signal is descriptive, not a measured campaign effect.",
        public_data_boundary="Use approved internal CRM fields to identify the audience. The public demo does not contain Manchester offer-holder records.",
        primary_kpi="Firm-choice conversion",
        guardrail_kpi="Opt-out rate and adviser workload",
        owner_team="Student Marketing + International Recruitment + CRM support",
        anchor_label="UCAS reply deadline",
        default_anchor_date=date(2026, 6, 3),
        workflow_rule="Route high-engagement offer-holders with no reply to adviser follow-up after the automated sequence.",
        steps=(
            _step(-42, "T-6 weeks", "Send fee-value guidance and eligible funding signposting", "Email + landing page", "Student Marketing", "Guidance-page click-through rate"),
            _step(-35, "T-5 weeks", "Send accommodation timeline and Q&A webinar invitation", "Email + webinar", "Student Marketing + Accommodation", "Webinar registration rate"),
            _step(-28, "T-4 weeks", "Send subject-level value content and next-step guidance", "Segmented email", "Faculty Marketing", "Course-page engagement"),
            _step(-14, "T-2 weeks", "Send reply-deadline reminder and route high-engagement non-repliers to adviser queue", "Email + CRM task", "Recruitment advisers", "Reply completion rate"),
            _step(7, "T+1 week", "Evaluate delivery, engagement, firm-choice conversion and opt-outs", "Dashboard", "Marketing Analytics", "Firm-choice conversion"),
        ),
        measurement_fields=("campaign_id", "lead_id", "consent_status", "domicile_group", "offer_made", "reply_received", "email_delivered", "email_opened", "email_clicked", "webinar_registered", "firm_choice", "opt_out", "timestamp"),
    ),
    "Increase Open Day attendance and application starts": Playbook(
        objective="Increase Open Day attendance and application starts",
        audience="Prospective students with course-page, enquiry-form or Open Day engagement",
        problem_statement="Registrations do not automatically become attendance or applications. A timed journey can reduce no-shows and improve post-event follow-up.",
        trigger="open_day_registered = yes OR enquiry_form_started = yes OR course_page_view = yes",
        evidence_basis="Official Open Day dates provide operational anchors. Attendance-to-application performance requires approved internal event and CRM records.",
        public_data_boundary="The public demo uses editable planning templates and synthetic engagement records. It does not claim measured Manchester attendance uplift.",
        primary_kpi="Attendance-to-application-start rate",
        guardrail_kpi="Opt-out rate and no-show rate",
        owner_team="Student Marketing + Events + Recruitment",
        anchor_label="Open Day date",
        default_anchor_date=date(2026, 6, 27),
        workflow_rule="After the event, route attendees with no application start into a consent-aware follow-up sequence.",
        steps=(
            _step(-14, "T-14 days", "Send course-specific Open Day invitation or registration confirmation", "Email + landing page", "Student Marketing", "Registration rate"),
            _step(-3, "T-3 days", "Send timetable, travel, accessibility and arrival guidance", "Email", "Events team", "Attendance rate"),
            _step(-1, "T-1 day", "Send short reminder and check-in guidance", "Email", "Events team", "Attendance rate"),
            _step(1, "T+1 day", "Send thank-you message, course links and application guidance", "Email + landing page", "Recruitment", "Application-start rate"),
            _step(7, "T+7 days", "Send follow-up to attendees who have not started an application", "CRM automation", "CRM support", "Recovered application starts"),
            _step(14, "T+14 days", "Evaluate registration, attendance, application starts and completions", "Dashboard", "Marketing Analytics", "Attendance-to-application-start rate"),
        ),
        measurement_fields=("campaign_id", "lead_id", "consent_status", "course_interest", "open_day_registered", "event_attended", "course_page_view", "application_started", "application_submitted", "email_delivered", "email_opened", "email_clicked", "opt_out", "timestamp"),
    ),
    "Recover incomplete enquiry or support forms": Playbook(
        objective="Recover incomplete enquiry or support forms",
        audience="Consent-confirmed prospects who started but did not complete a form",
        problem_statement="Incomplete forms create avoidable leakage in the recruitment journey and can generate manual support work close to deadlines.",
        trigger="form_started = yes AND form_completed = no AND consent_status = yes",
        evidence_basis="Forms and marketing automation are explicit operational areas in the role. Recovery performance must be measured using authorised form and CRM event data.",
        public_data_boundary="The public tool demonstrates workflow logic only. It does not process real applicant records unless an approved upload workflow is used internally.",
        primary_kpi="Recovered form-completion rate",
        guardrail_kpi="Opt-out rate and adviser workload",
        owner_team="CRM support + Student Marketing",
        anchor_label="Form-start date",
        default_anchor_date=date(2026, 6, 4),
        workflow_rule="Trigger reminder within 24 hours, then route high-intent unresolved records to the adviser queue after seven days.",
        steps=(
            _step(1, "Within 24 hours", "Send automated reminder with direct form link", "Email", "CRM automation", "Reminder click-through rate"),
            _step(3, "T+3 days", "Send FAQ and support-contact guidance", "Email + FAQ page", "Student Marketing", "Recovered form completions"),
            _step(7, "T+7 days", "Route high-intent unresolved records to adviser follow-up", "CRM task", "Recruitment advisers", "Adviser-assisted completions"),
            _step(14, "T+14 days", "Evaluate completion, response time, workload and opt-outs", "Dashboard", "Marketing Analytics", "Recovered form-completion rate"),
        ),
        measurement_fields=("campaign_id", "lead_id", "consent_status", "form_id", "form_started", "form_completed", "form_start_timestamp", "form_completion_timestamp", "email_delivered", "email_opened", "email_clicked", "adviser_task_created", "opt_out", "timestamp"),
    ),
    "Run a Clearing rapid-response campaign": Playbook(
        objective="Run a Clearing rapid-response campaign",
        audience="Clearing prospects and consent-confirmed enquiry records",
        problem_statement="Clearing activity is time-sensitive. Course availability, webpage content, enquiry response and adviser queues need a short review cycle.",
        trigger="recruitment_phase = Clearing AND consent_status = yes",
        evidence_basis="The official Clearing date is an operational anchor. Course availability and response performance need approved internal updates during the live period.",
        public_data_boundary="The public prototype does not claim live vacancy availability. Refresh official pages and use approved internal records before operational use.",
        primary_kpi="Enquiry-to-offer conversion and response time",
        guardrail_kpi="Queue age and outdated-content incidents",
        owner_team="Student Marketing + Admissions + Recruitment advisers",
        anchor_label="Early Clearing launch",
        default_anchor_date=date(2026, 7, 2),
        workflow_rule="Review course availability and adviser queue daily during the Clearing window.",
        steps=(
            _step(-7, "T-7 days", "Prepare availability workflow, landing-page content and escalation route", "Web + CRM checklist", "Admissions + Student Marketing", "Content readiness"),
            _step(0, "Launch day", "Publish Clearing journey and start tracked campaign activity", "Landing page + email + social", "Student Marketing", "Enquiry registrations"),
            _step(1, "Daily", "Review traffic, enquiry queue age and course-availability updates", "Dashboard", "Marketing Analytics + Admissions", "Median response time"),
            _step(3, "T+3 days", "Route unresolved high-intent enquiries to adviser worklist", "CRM task", "Recruitment advisers", "Adviser follow-up completion"),
            _step(7, "T+7 days", "Evaluate enquiries, offers, acceptances and content incidents", "Dashboard", "Marketing Analytics", "Enquiry-to-offer conversion"),
        ),
        measurement_fields=("campaign_id", "lead_id", "consent_status", "course_interest", "course_available", "landing_page_view", "enquiry_submitted", "adviser_task_created", "first_response_timestamp", "offer_made", "acceptance", "content_incident", "timestamp"),
    ),
    "Improve contextual-access outreach engagement": Playbook(
        objective="Improve contextual-access outreach engagement",
        audience="Prospective students who may benefit from clear access, outreach and support signposting",
        problem_statement="Prospective students need accessible information about support routes, Open Days and official eligibility guidance.",
        trigger="outreach_segment = eligible_or_prospective AND consent_status = yes",
        evidence_basis="Published access priorities and official contextual-admissions guidance support clear signposting. The public tool does not decide individual eligibility.",
        public_data_boundary="Do not infer individual eligibility in the public demo. Link to official guidance and use approved internal processes.",
        primary_kpi="Outreach registration rate",
        guardrail_kpi="Accessibility issues and opt-out rate",
        owner_team="Access and Outreach + Student Marketing",
        anchor_label="Outreach or Open Day date",
        default_anchor_date=date(2026, 6, 27),
        workflow_rule="Use official eligibility guidance and route unresolved support questions to the approved support channel.",
        steps=(
            _step(-28, "T-4 weeks", "Send clear access and contextual-admissions guidance", "Email + official guidance page", "Access and Outreach", "Guidance-page visits"),
            _step(-21, "T-3 weeks", "Signpost bursary and support information with eligibility links", "Email + official funding page", "Access and Outreach", "Support-page visits"),
            _step(-14, "T-2 weeks", "Invite prospects to Open Day or outreach activity", "Email + registration form", "Student Marketing", "Registration rate"),
            _step(-3, "T-3 days", "Send logistics, accessibility and travel-support guidance", "Email", "Events team", "Attendance rate"),
            _step(7, "T+1 week", "Follow up with official next-step guidance", "Email + official page", "Access and Outreach", "Guidance engagement"),
            _step(14, "T+2 weeks", "Evaluate reach, registration, attendance and support queries", "Dashboard", "Marketing Analytics", "Outreach registration rate"),
        ),
        measurement_fields=("campaign_id", "lead_id", "consent_status", "outreach_segment", "guidance_page_view", "funding_page_view", "event_registered", "event_attended", "support_query", "email_delivered", "email_opened", "email_clicked", "opt_out", "timestamp"),
    ),
}


def list_objectives() -> list[str]:
    return list(PLAYBOOKS)


def get_playbook(objective: str) -> Playbook:
    if objective not in PLAYBOOKS:
        raise KeyError(f"Unknown marketing objective: {objective}")
    return PLAYBOOKS[objective]


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug[:56] or "campaign"


def build_action_plan(objective: str, anchor_date: date, targeted_share: float, audience_size: int, adviser_capacity: int) -> pd.DataFrame:
    playbook = get_playbook(objective)
    target_records = max(0, int(round(audience_size * targeted_share)))
    rows: list[dict] = []
    for index, step in enumerate(playbook.steps, start=1):
        event_date = anchor_date + timedelta(days=int(step["offset_days"]))
        row = {
            "step": index,
            "objective": playbook.objective,
            "audience": playbook.audience,
            "trigger": playbook.trigger,
            "anchor_label": playbook.anchor_label,
            "anchor_date": anchor_date.isoformat(),
            "timing": step["timing"],
            "event_date": event_date.isoformat(),
            "action": step["action"],
            "channel": step["channel"],
            "owner_team": step["owner_team"],
            "step_kpi": step["step_kpi"],
            "primary_kpi": playbook.primary_kpi,
            "guardrail_kpi": playbook.guardrail_kpi,
            "status": step["status"],
            "targeted_records": target_records,
            "weekly_adviser_capacity": int(adviser_capacity),
        }
        rows.append(row)
    return pd.DataFrame(rows)


def build_measurement_plan(objective: str, evaluation_design: str) -> pd.DataFrame:
    playbook = get_playbook(objective)
    fields = []
    for field in playbook.measurement_fields:
        fields.append({
            "objective": objective,
            "evaluation_design": evaluation_design,
            "field": field,
            "purpose": _measurement_purpose(field),
            "data_boundary": "Approved internal field required" if field not in {"campaign_id", "timestamp"} else "Campaign tracking field",
        })
    return pd.DataFrame(fields)


def build_workflow_rules(objective: str) -> pd.DataFrame:
    playbook = get_playbook(objective)
    return pd.DataFrame([
        {
            "objective": objective,
            "audience": playbook.audience,
            "trigger": playbook.trigger,
            "workflow_rule": playbook.workflow_rule,
            "owner_team": playbook.owner_team,
            "primary_kpi": playbook.primary_kpi,
            "guardrail_kpi": playbook.guardrail_kpi,
            "data_boundary": playbook.public_data_boundary,
        }
    ])


def action_plan_to_calendar(plan: pd.DataFrame) -> pd.DataFrame:
    """Convert an action plan to the calendar schema used by the ICS exporter."""
    rows = []
    for _, row in plan.iterrows():
        rows.append({
            "start_date": row["event_date"],
            "end_date": row["event_date"],
            "event": row["action"],
            "population": "Marketing action",
            "audience": row["audience"],
            "phase": row["objective"],
            "channel": row["channel"],
            "owner_team": row["owner_team"],
            "primary_kpi": row["step_kpi"],
            "recommended_action": row["action"],
            "date_type": "Planning template",
            "source_id": "marketing_action_centre",
        })
    return pd.DataFrame(rows)


def _measurement_purpose(field: str) -> str:
    mapping = {
        "campaign_id": "Join activity to the approved campaign definition",
        "lead_id": "Join consent-aware CRM events to the relevant record",
        "consent_status": "Check whether marketing communication is permitted",
        "timestamp": "Support sequence timing and time-to-action reporting",
        "opt_out": "Monitor the communication guardrail",
        "email_delivered": "Measure delivery",
        "email_opened": "Measure engagement",
        "email_clicked": "Measure engagement",
        "firm_choice": "Measure offer-holder conversion",
        "event_attended": "Measure attendance",
        "application_started": "Measure application-journey entry",
        "application_submitted": "Measure completed applications",
        "form_started": "Identify incomplete-form records",
        "form_completed": "Measure recovery",
        "first_response_timestamp": "Measure adviser response time",
    }
    return mapping.get(field, "Required for objective-specific measurement or workflow routing")
