"""University recruitment marketing analytics portfolio prototype — V5.

Public University of Manchester data are clearly separated from synthetic
records used to demonstrate protected internal workflows.
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path
import textwrap
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from app_utils import badge, mode_badge, csv_bytes, fmt_pct, html_card, pct_change, fmt_change, require_columns, safe_div
from admissions_tools import (
    ADMISSIONS_REQUIRED,
    METRICS,
    comparison_summary,
    cycle_summary,
    deferral_summary,
    latest_snapshot_dates,
    pdf_summary_bytes,
    status_summary,
)
from calendar_tools import CALENDAR_REQUIRED, build_utm_url, calendar_to_ics, next_event, normalise_calendar
from crm_tools import CRM_REQUIRED, crm_quality_issues, triage_leads
from strategy_tools import OfferHolderScenario, access_registration_scenario, campaign_plan, simulate_offer_holder

PUBLIC = ROOT / "data" / "public_snapshots"
DEMO = ROOT / "data" / "demo"
UPLOAD = ROOT / "data" / "upload_schema"
REPORTS = ROOT / "reports"

st.set_page_config(
    page_title="Manchester Recruitment Marketing Analytics — V5",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
.block-container { padding-top: 1.25rem; padding-bottom: 2rem; max-width: 1480px; }
h1 { letter-spacing: -0.035em; }
h2, h3 { letter-spacing: -0.02em; }
.metric-card { border: 1px solid rgba(148,163,184,.30); border-radius: 14px; padding: 0.9rem 1rem; min-height: 112px; background: rgba(30,41,59,.18); }
.metric-label { color: #94a3b8; font-size: 0.82rem; font-weight: 650; letter-spacing: 0.03em; text-transform: uppercase; }
.metric-value { color: #f8fafc; font-size: 1.85rem; font-weight: 740; margin-top: 0.18rem; line-height: 1.08; }
.section-note { border-left: 4px solid #38bdf8; background: rgba(14,116,144,.12); padding: 0.7rem 0.9rem; border-radius: 8px; margin: .4rem 0 .9rem 0; }
.small-note { color: #94a3b8; font-size: .84rem; }
.source-box { border: 1px solid rgba(148,163,184,.24); padding: .7rem .85rem; border-radius: 10px; margin-bottom: .6rem; }
[data-testid="stMetricValue"] { font-size: 2rem; }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_data() -> dict[str, pd.DataFrame]:
    data = {
        "institution": pd.read_csv(PUBLIC / "institution_snapshot.csv"),
        "profile": pd.read_csv(PUBLIC / "student_profile_ucas_hesa.csv"),
        "published_funnel": pd.read_csv(PUBLIC / "admissions_funnel.csv"),
        "access_targets": pd.read_csv(PUBLIC / "access_targets.csv"),
        "success_targets": pd.read_csv(PUBLIC / "success_targets.csv"),
        "signals": pd.read_csv(PUBLIC / "marketing_signals.csv"),
        "funding": pd.read_csv(PUBLIC / "support_and_funding.csv"),
        "sources": pd.read_csv(PUBLIC / "source_registry.csv"),
        "quality_rules": pd.read_csv(PUBLIC / "data_quality_rules.csv"),
        "integration": pd.read_csv(PUBLIC / "integration_plan.csv"),
        "calendar": pd.read_csv(DEMO / "campaign_calendar_enriched.csv"),
        "admissions_demo": pd.read_csv(DEMO / "synthetic_admissions_operations.csv"),
        "crm_demo": pd.read_csv(DEMO / "synthetic_crm_records.csv"),
        "digital_demo": pd.read_csv(DEMO / "synthetic_digital_journey.csv"),
    }
    return data


def page_intro(title: str, subtitle: str, badges: list[tuple[str, str]] | None = None) -> None:
    st.header(title)
    st.write(subtitle)
    if badges:
        st.markdown(" ".join(badge(text, colour) for text, colour in badges), unsafe_allow_html=True)


def source_footer(text: str = "Public-data sections use committed snapshots with source metadata. Synthetic workflow sections do not claim access to University internal records.") -> None:
    st.caption(text)


def overview(data: dict[str, pd.DataFrame]) -> None:
    st.title("University Recruitment Marketing Analytics Tool")
    st.subheader("University of Manchester public-data portfolio prototype — V5")
    st.write(
        "Use public recruitment signals to plan campaigns, monitor published admissions funnels, schedule time-sensitive activity, and demonstrate how authorised internal records could feed operational dashboards."
    )
    st.markdown(mode_badge("Official public data") + mode_badge("Synthetic demonstration") + mode_badge("Planning assumption"), unsafe_allow_html=True)
    inst = data["institution"].set_index("metric")
    cols = st.columns(5)
    cards = [
        ("Students", inst.loc["Students", "display_value"], "Official facts PDF, Feb 2026"),
        ("Staff", inst.loc["Staff", "display_value"], "Official facts PDF, Feb 2026"),
        ("Alumni", inst.loc["Alumni", "display_value"], inst.loc["Alumni countries", "display_value"]),
        ("International students", inst.loc["International students outside EU", "display_value"], "Outside the EU; keep separate from UCAS/HESA profile"),
        ("Degree programmes", inst.loc["Degree programmes", "display_value"], "Published institution-level fact"),
    ]
    for col, (label, value, note) in zip(cols, cards):
        col.markdown(html_card(label, str(value), str(note)), unsafe_allow_html=True)

    st.markdown("### Student profile shown by UCAS")
    st.caption("UCAS states that its student statistics are sourced from HESA. The domicile percentages and the institution-level non-EU international headcount use different definitions and are shown separately.")
    prof = data["profile"]
    left, middle, right = st.columns(3)
    with left:
        dom = prof[prof.category == "Domicile"].copy()
        fig = px.bar(dom, x="value", y="segment", orientation="h", text="value", title="Domicile profile", labels={"value": "Percent", "segment": "Student group"})
        fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
        fig.update_xaxes(range=[0, 70])
        st.plotly_chart(fig, width="stretch")
    with middle:
        level = prof[prof.category == "Study level"].copy()
        fig = px.bar(level, x="segment", y="value", text="value", title="Study level", labels={"value": "Percent", "segment": "Study level"})
        fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
        fig.update_yaxes(range=[0, 80])
        st.plotly_chart(fig, width="stretch")
    with right:
        mode = prof[prof.category == "Study mode"].copy()
        fig = px.pie(mode, names="segment", values="value", title="Study mode", hole=.42)
        st.plotly_chart(fig, width="stretch")

    st.markdown("### What this portfolio tool demonstrates")
    c1, c2, c3 = st.columns(3)
    c1.info("**Time-sensitive campaign planning**\n\nOfficial UG deadlines, Open Days and Clearing dates feed a filterable calendar with CSV and ICS export.")
    c2.info("**Admissions operations patterns**\n\nA synthetic upload-ready monitor mirrors UG/PG cycle, status, fee, domicile and hierarchy filters described in reporting guidance.")
    c3.info("**Marketing systems workflow**\n\nSynthetic CRM and GA4-style records demonstrate consent checks, follow-up queues, UTM tracking and data-quality monitoring.")
    source_footer("Independent portfolio prototype. It is not an official University of Manchester system.")


def campaign_calendar(data: dict[str, pd.DataFrame]) -> None:
    page_intro(
        "Recruitment Campaign Calendar",
        "Plan activity around application deadlines, offer-holder decisions, Open Days and Clearing. Official dates remain visually separate from editable planning events.",
        [("Official public dates", "#0f766e"), ("Editable planning events", "#7c3aed")],
    )
    base = normalise_calendar(data["calendar"])
    uploaded = st.file_uploader("Optional: upload an additional campaign calendar CSV", type=["csv"], key="calendar_upload")
    calendar = base.copy()
    if uploaded is not None:
        custom = pd.read_csv(uploaded)
        missing = require_columns(custom, CALENDAR_REQUIRED)
        if missing:
            st.error("Uploaded calendar is missing required columns: " + ", ".join(missing))
        else:
            calendar = pd.concat([calendar.drop(columns=["display_end"], errors="ignore"), custom], ignore_index=True)
            calendar = normalise_calendar(calendar)
            st.success(f"Added {len(custom):,} uploaded calendar rows for this browser session.")
    nxt = next_event(calendar)
    if nxt is not None:
        days = (pd.Timestamp(nxt["start_date"]).date() - date.today()).days
        status = "today" if days == 0 else (f"in {days} days" if days > 0 else f"started {-days} days ago")
        st.info(f"**Next scheduled item:** {nxt['event']} — {pd.Timestamp(nxt['start_date']).date().isoformat()} ({status}).")

    c1, c2, c3, c4 = st.columns(4)
    populations = sorted(calendar.population.dropna().astype(str).unique())
    pop = c1.multiselect("Population", populations, default=populations)
    phases = sorted(calendar.phase.dropna().astype(str).unique())
    phase = c2.multiselect("Phase", phases, default=phases)
    channels = sorted(calendar.channel.dropna().astype(str).unique())
    channel = c3.multiselect("Channel", channels, default=channels)
    owners = sorted(calendar.owner_team.dropna().astype(str).unique())
    owner = c4.multiselect("Owner team", owners, default=owners)
    min_date = calendar.start_date.min().date()
    max_date = calendar.end_date.max().date()
    selected_dates = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start, end = selected_dates
    else:
        start, end = min_date, max_date
    view = calendar[
        calendar.population.astype(str).isin(pop)
        & calendar.phase.astype(str).isin(phase)
        & calendar.channel.astype(str).isin(channel)
        & calendar.owner_team.astype(str).isin(owner)
        & (calendar.start_date.dt.date <= end)
        & (calendar.end_date.dt.date >= start)
    ].copy()

    if view.empty:
        st.warning("No events match the selected filters.")
    else:
        timeline = view.copy()
        timeline["colour_group"] = timeline["date_type"].where(timeline["date_type"].eq("Official public date"), "Planning template")
        fig = px.timeline(
            timeline,
            x_start="start_date",
            x_end="display_end",
            y="event",
            color="colour_group",
            hover_data=["population", "audience", "phase", "channel", "owner_team", "primary_kpi", "recommended_action"],
            title="Filterable recruitment activity timeline",
        )
        fig.update_yaxes(autorange="reversed", title="")
        fig.update_xaxes(title="Date")
        fig.update_layout(height=max(460, 32 * len(timeline) + 150), legend_title_text="Date type")
        st.plotly_chart(fig, width="stretch")
        table = view[["start_date", "end_date", "event", "population", "audience", "phase", "channel", "owner_team", "primary_kpi", "recommended_action", "date_type"]].copy()
        table["start_date"] = table["start_date"].dt.date
        table["end_date"] = table["end_date"].dt.date
        st.dataframe(table, width="stretch", hide_index=True)
        d1, d2, d3 = st.columns(3)
        d1.download_button("Download filtered calendar CSV", csv_bytes(table), "recruitment_campaign_calendar.csv", "text/csv")
        d2.download_button("Download filtered calendar ICS", calendar_to_ics(view), "recruitment_campaign_calendar.ics", "text/calendar")
        d3.download_button("Download upload template", (UPLOAD / "campaign_calendar_upload_template.csv").read_bytes(), "campaign_calendar_upload_template.csv", "text/csv")

    st.markdown("### UTM tracking builder")
    st.caption("Use UTM parameters for external campaign links such as email, social or paid activity. Do not use UTM parameters for internal links between University webpages.")
    u1, u2, u3 = st.columns(3)
    base_url = u1.text_input("Landing-page URL", value="https://www.manchester.ac.uk/study/undergraduate/open-days-visits/open-days/")
    source = u2.text_input("utm_source", value="email")
    medium = u3.text_input("utm_medium", value="offer_holder_sequence")
    u4, u5 = st.columns(2)
    campaign = u4.text_input("utm_campaign", value="ug_2026_open_day_june")
    content = u5.text_input("utm_content", value="registration_prompt")
    tagged = build_utm_url(base_url, source, medium, campaign, content)
    st.code(tagged, language=None)
    st.download_button("Download tracking row CSV", csv_bytes(pd.DataFrame([{"base_url": base_url, "tagged_url": tagged, "utm_source": source, "utm_medium": medium, "utm_campaign": campaign, "utm_content": content}])), "utm_tracking_row.csv", "text/csv")
    source_footer("Official date rows are committed snapshots. Refresh live pages before a real campaign launch because dates and availability can change.")


def admissions_operations(data: dict[str, pd.DataFrame]) -> None:
    page_intro(
        "Admissions Operations Monitor",
        "A dynamic demonstration of UG and PG reporting patterns described in admissions reporting guidance. The committed records are synthetic; an authorised CSV can be uploaded temporarily for schema-compliant analysis.",
        [("Synthetic by default", "#6b7280"), ("Authorised upload supported", "#166534")],
    )
    st.download_button("Download admissions upload template", (UPLOAD / "admissions_upload_template.csv").read_bytes(), "admissions_upload_template.csv", "text/csv")
    uploaded = st.file_uploader("Optional: upload a schema-compliant authorised admissions CSV", type=["csv"], key="admissions_upload")
    df = pd.read_csv(uploaded) if uploaded is not None else data["admissions_demo"].copy()
    mode = "Authorised upload" if uploaded is not None else "Synthetic demonstration"
    missing = require_columns(df, ADMISSIONS_REQUIRED)
    if missing:
        st.error("Admissions file is missing required columns: " + ", ".join(missing))
        return
    st.markdown(mode_badge(mode), unsafe_allow_html=True)

    population_map = {"Undergraduate": "UG", "Postgraduate taught": "PGT", "Postgraduate research": "PGR"}
    population_label = st.segmented_control("Applicant population", list(population_map), default="Undergraduate")
    population = population_map[population_label]
    view = df[df.population == population].copy()
    if view.empty:
        st.warning("No records are available for this population.")
        return

    top1, top2, top3, top4 = st.columns(4)
    current_cycle = int(top1.selectbox("Current cycle", sorted(view.cycle.unique(), reverse=True)))
    week_options = sorted(view[view.cycle == current_cycle].cycle_week.unique())
    week = int(top2.select_slider("Cycle week", options=week_options, value=max(week_options)))
    previous_cycles = sorted([int(x) for x in view.cycle.unique() if int(x) < current_cycle], reverse=True)
    previous_cycle = int(top3.selectbox("Comparison cycle", previous_cycles if previous_cycles else [current_cycle]))
    cycle_count = int(top4.slider("Cycles shown in trend", min_value=2, max_value=min(4, len(view.cycle.unique())), value=min(4, len(view.cycle.unique()))))

    with st.expander("Hierarchy and population filters", expanded=True):
        f1, f2, f3, f4, f5 = st.columns(5)
        view, faculty = _cascade_filter(view, f1, "Faculty", "faculty")
        view, school = _cascade_filter(view, f2, "School", "school")
        view, department = _cascade_filter(view, f3, "Department", "department")
        view, sub_department = _cascade_filter(view, f4, "Sub-department", "sub_department")
        view, course = _cascade_filter(view, f5, "Course", "course_name")
        g1, g2, g3, g4 = st.columns(4)
        fee_status = g1.multiselect("Fee status", sorted(view.fee_status.unique()), default=sorted(view.fee_status.unique()))
        view = view[view.fee_status.isin(fee_status)]
        if population == "UG":
            levels = sorted(view.academic_level.unique())
            selected_levels = g2.multiselect("Academic level of entry", levels, default=levels)
            view = view[view.academic_level.isin(selected_levels)]
            g3.caption("UG deferrals are shown in a separate tab because they use a distinct reporting scope.")
        else:
            months = sorted(view.month_of_entry.unique())
            modes = sorted(view.mode_of_attendance.unique())
            selected_months = g2.multiselect("Month of entry", months, default=months)
            selected_modes = g3.multiselect("Mode of attendance", modes, default=modes)
            view = view[view.month_of_entry.isin(selected_months) & view.mode_of_attendance.isin(selected_modes)]
        pending_as_overseas = g4.toggle("Include pending fee assessment with overseas in headline notes", value=True)

    current_date, previous_date = latest_snapshot_dates(view, current_cycle, previous_cycle, week)
    st.markdown(f"<div class='section-note'><b>Comparable snapshots:</b> Week {week:02d} · current cycle {current_cycle} as of {current_date} · comparison cycle {previous_cycle} as of {previous_date}</div>", unsafe_allow_html=True)
    selected_cycles = sorted(view.cycle.unique(), reverse=True)[:cycle_count]
    comp = comparison_summary(view, current_cycle, previous_cycle, week)
    metric_lookup = {row["Metric"]: row for _, row in comp.iterrows()}
    cols = st.columns(4)
    for col, metric in zip(cols, ["Applications", "Offers", "Replies", "Acceptances"]):
        row = metric_lookup[metric]
        col.metric(metric, f"{int(row['Current cycle']):,}", row["Change"] + f" vs {previous_cycle}")

    tabs = st.tabs(["Summary vs previous cycle", "Summary by cycle", "Applications by status", "UG deferrals", "Course export"])
    with tabs[0]:
        st.dataframe(comp, width="stretch", hide_index=True)
        metric = st.selectbox("Trend metric", METRICS, format_func=lambda x: x.replace("_", " ").title(), key="admissions_metric")
        trend = view[view.cycle.isin(selected_cycles)].groupby(["cycle", "cycle_week"], as_index=False)[metric].sum()
        fig = px.line(trend, x="cycle_week", y=metric, color="cycle", markers=False, title=f"{metric.replace('_', ' ').title()} by comparable cycle week", labels={metric: metric.replace("_", " ").title(), "cycle_week": "Cycle week", "cycle": "Entry cycle"})
        st.plotly_chart(fig, width="stretch")
    with tabs[1]:
        cyc = cycle_summary(view, selected_cycles, week)
        st.dataframe(cyc, width="stretch", hide_index=True)
        long = cyc.melt(id_vars=["cycle", "fee_status"], value_vars=METRICS, var_name="Metric", value_name="Count")
        st.plotly_chart(px.bar(long, x="Metric", y="Count", color="fee_status", facet_col="cycle", barmode="stack", title=f"Admissions metrics at week {week:02d} by cycle and fee status"), width="stretch")
    with tabs[2]:
        stat = status_summary(view, selected_cycles, week)
        st.dataframe(stat, width="stretch", hide_index=True)
    with tabs[3]:
        if population != "UG":
            st.info("The deferral report is an undergraduate-only view.")
        else:
            st.caption("Current cycle only. This view is intentionally separate from previous-cycle comparisons.")
            deff = deferral_summary(view, current_cycle, week)
            st.dataframe(deff, width="stretch", hide_index=True)
    with tabs[4]:
        export = view[(view.cycle == current_cycle) & (view.cycle_week == week)].copy()
        key_cols = ["faculty", "school", "department", "sub_department", "course_code", "course_name", "fee_status", "applications", "offers", "replies", "acceptances", "deferred"]
        st.dataframe(export[key_cols].sort_values(["faculty", "school", "course_name", "fee_status"]), width="stretch", hide_index=True)
        filter_note = f"Population={population_label}; cycle={current_cycle}; week={week}; faculty={faculty}; school={school}; department={department}; sub-department={sub_department}; course={course}; fee status={', '.join(fee_status)}"
        pdf = pdf_summary_bytes("Admissions operations summary", filter_note, comp, export[key_cols])
        d1, d2 = st.columns(2)
        d1.download_button("Download filtered course CSV", csv_bytes(export[key_cols]), "admissions_course_export.csv", "text/csv")
        d2.download_button("Generate PDF summary", pdf, "admissions_operations_summary.pdf", "application/pdf")
    if pending_as_overseas:
        st.caption("Headline-note setting: pending fee assessment may be grouped with overseas for operational comparison. The detailed table retains a separate pending category for transparency.")
    source_footer("This page implements reporting logic using synthetic records. Do not upload personal data to a public deployment unless the organisation has approved the workflow.")


def _cascade_filter(df: pd.DataFrame, container, label: str, column: str) -> tuple[pd.DataFrame, str]:
    options = ["All"] + sorted(df[column].dropna().astype(str).unique())
    selected = container.selectbox(label, options, key=f"cascade_{column}")
    if selected == "All":
        return df, selected
    return df[df[column].astype(str) == selected].copy(), selected


def international_markets(data: dict[str, pd.DataFrame]) -> None:
    page_intro(
        "International Market Monitor",
        "Demonstrate country-of-domicile and Top Markets analysis using synthetic admissions operations records. Upload mode is available in the Admissions Operations Monitor.",
        [("Synthetic demonstration", "#6b7280")],
    )
    df = data["admissions_demo"].copy()
    p1, p2, p3, p4 = st.columns(4)
    population = p1.selectbox("Population", ["UG", "PGT", "PGR"])
    cycles = sorted(df[df.population == population].cycle.unique(), reverse=True)
    cycle = int(p2.selectbox("Current cycle", cycles))
    week = int(p3.select_slider("Cycle week", options=sorted(df[(df.population == population) & (df.cycle == cycle)].cycle_week.unique()), value=40))
    top_n = p4.selectbox("Market view", [10, 25, "All markets"], format_func=lambda x: f"Top {x}" if isinstance(x, int) else x)
    previous = max([c for c in cycles if c < cycle], default=cycle)
    view = df[(df.population == population) & (df.fee_status.isin(["Overseas", "Pending assessment"]))]
    cur = view[(view.cycle == cycle) & (view.cycle_week == week)].groupby("country_of_domicile", as_index=False)[["applications", "offers", "acceptances"]].sum()
    prev = view[(view.cycle == previous) & (view.cycle_week == week)].groupby("country_of_domicile", as_index=False)[["applications", "offers", "acceptances"]].sum().add_suffix("_previous").rename(columns={"country_of_domicile_previous": "country_of_domicile"})
    summary = cur.merge(prev, on="country_of_domicile", how="left").fillna(0)
    summary["application_change"] = summary.apply(lambda r: fmt_change(pct_change(r.applications, r.applications_previous)), axis=1)
    summary["offer_rate"] = summary.apply(lambda r: fmt_pct(safe_div(r.offers, r.applications)), axis=1)
    summary = summary.sort_values("applications", ascending=False)
    if isinstance(top_n, int):
        summary = summary.head(top_n)
    st.dataframe(summary, width="stretch", hide_index=True)
    chart = summary[summary.country_of_domicile != "Pending fee assessment"]
    st.plotly_chart(px.bar(chart, x="applications", y="country_of_domicile", orientation="h", text="applications", title=f"International applications at week {week:02d}: {cycle} cycle", labels={"applications": "Applications", "country_of_domicile": "Country of domicile"}), width="stretch")
    st.download_button("Download filtered international-market CSV", csv_bytes(summary), "international_market_monitor.csv", "text/csv")
    source_footer("The records on this page are synthetic. In an internal system, use approved domicile definitions and data-access rules.")


def published_course_funnels(data: dict[str, pd.DataFrame]) -> None:
    page_intro(
        "Published Course Funnel Explorer",
        "Explore official published application, interview-shortlist and offer counts for selected Medicine and Dentistry routes. Use them for operational examples, not applicant-level prediction.",
        [("Official public data", "#0f766e"), ("Historical information only", "#2563eb")],
    )
    df = data["published_funnel"].copy()
    f1, f2 = st.columns(2)
    program = f1.selectbox("Programme", sorted(df.program.unique()))
    domicile = f2.selectbox("Domicile", ["All", "Home", "Overseas"])
    view = df[df.program == program].copy()
    if domicile != "All":
        view = view[view.domicile == domicile]
    grouped = view.groupby("entry_year", as_index=False)[["applications", "shortlisted_for_interview", "offers_made"]].sum(min_count=1).sort_values("entry_year")
    long = grouped.melt(id_vars="entry_year", var_name="Admissions stage", value_name="Count")
    long["Admissions stage"] = long["Admissions stage"].map({"applications": "Applications", "shortlisted_for_interview": "Interview shortlist", "offers_made": "Offers made"})
    fig = px.line(long, x="entry_year", y="Count", color="Admissions stage", markers=True, title=f"{program}: published funnel counts")
    years = sorted(grouped.entry_year.astype(int).unique())
    fig.update_xaxes(tickmode="array", tickvals=years, ticktext=[str(y) for y in years], title="Entry year")
    st.plotly_chart(fig, width="stretch")
    latest_year = int(grouped.entry_year.max())
    latest = grouped[grouped.entry_year == latest_year].iloc[0]
    status = sorted(view[view.entry_year == latest_year].publication_status.unique())
    status_label = " · ".join(status)
    cols = st.columns(4)
    cols[0].metric("Latest displayed entry year", str(latest_year))
    cols[1].metric("Applications", f"{int(latest.applications):,}")
    cols[2].metric("Interview rate", fmt_pct(safe_div(latest.shortlisted_for_interview, latest.applications)))
    cols[3].metric("Offer / application rate", fmt_pct(safe_div(latest.offers_made, latest.applications)))
    if "provisional_week_5" in status:
        st.warning("Latest Medicine figures are marked as a provisional Week 5 snapshot on the official page and may change slightly.")
    st.caption(f"Latest displayed publication status: {status_label}")
    detail = view[["program", "ucas_code", "entry_year", "domicile", "applications", "shortlisted_for_interview", "offers_made", "publication_status", "notes"]].sort_values(["entry_year", "domicile"], ascending=[False, True])
    st.dataframe(detail, width="stretch", hide_index=True)
    st.download_button("Download filtered published funnel CSV", csv_bytes(detail), "published_course_funnel.csv", "text/csv")
    st.info("The Dentistry pages state that historical figures are for information only and should not be used to predict future cycles or determine an individual applicant strategy.")


def strategy_builder(data: dict[str, pd.DataFrame]) -> None:
    page_intro(
        "Campaign Strategy Builder",
        "Translate public descriptive signals into testable communication plans. Editable actions are not claims of causal impact.",
        [("Official descriptive signal", "#0f766e"), ("Internal testing required", "#7c3aed")],
    )
    signals = data["signals"]
    fee = signals[signals.signal_id == "international_tuition_fee_decline"].copy()
    fig = px.bar(fee, x="period", y="value", text="value", title="International decliners citing tuition-fee cost as a main reason", labels={"period": "Survey year", "value": "Percent of international decliners"})
    years = sorted(fee.period.astype(int).unique())
    fig.update_xaxes(tickmode="array", tickvals=years, ticktext=[str(y) for y in years])
    fig.update_traces(texttemplate="%{text:.0f}%", textposition="outside")
    fig.update_yaxes(range=[0, 55])
    st.plotly_chart(fig, width="stretch")
    m1, m2, m3 = st.columns(3)
    m1.metric("International cost signal, 2024", "45%", "+9 pp vs 2023")
    m2.metric("Accommodation confidence", "+11%", "2024 vs 2023")
    m3.metric("FSE content signal", "Rankings + requirements", "Higher reported importance")
    audience = st.selectbox("Audience", ["International UG offer-holders", "FSE UG offer-holders", "Contextual admissions prospects", "All UG offer-holders"])
    c1, c2, c3, c4 = st.columns(4)
    fee_on = c1.checkbox("Fee-value guidance", value="International" in audience)
    accommodation = c2.checkbox("Accommodation reassurance", value=True)
    subject = c3.checkbox("Subject value and requirements", value="FSE" in audience)
    contextual = c4.checkbox("Contextual admissions signposting", value="Contextual" in audience)
    plan = campaign_plan(audience, fee_on, accommodation, subject, contextual)
    st.dataframe(plan, width="stretch", hide_index=True)
    st.download_button("Download communication plan CSV", csv_bytes(plan), "campaign_strategy_plan.csv", "text/csv")
    st.markdown("### Relevant support routes")
    funding = data["funding"][["name", "audience", "benefit", "scale", "use_in_v5", "notes"]].copy()
    st.dataframe(funding, width="stretch", hide_index=True)
    st.info("Signpost users to official eligibility guidance. Do not state that all members of an audience qualify for a bursary, scholarship or contextual offer.")


def offer_holder_planner(data: dict[str, pd.DataFrame]) -> None:
    page_intro(
        "Offer-holder Conversion Planner",
        "Adjust planning assumptions to size a trial and estimate delivery workload. These slider values are not measured University treatment effects.",
        [("Planning assumption", "#7c3aed")],
    )
    left, right = st.columns(2)
    with left:
        cohort = st.number_input("Offer-holder cohort size", 100, 50000, 5000, 100)
        rate = st.slider("Current firm-choice rate", 0.0, 1.0, .35, .01)
        targeted = st.slider("Share receiving targeted sequence", 0.0, 1.0, .60, .05)
        capacity = st.number_input("Weekly adviser-review capacity", 0, 5000, 120, 10)
    with right:
        fee = st.slider("Assumed uplift from fee-value guidance (percentage points)", 0.0, 10.0, 1.0, .5)
        accommodation = st.slider("Assumed uplift from accommodation reassurance (percentage points)", 0.0, 10.0, 1.5, .5)
        subject = st.slider("Assumed uplift from subject-value content (percentage points)", 0.0, 10.0, .5, .5)
    out = simulate_offer_holder(OfferHolderScenario(int(cohort), rate, targeted, fee, accommodation, subject, int(capacity)))
    cols = st.columns(5)
    cols[0].metric("Baseline firms", f"{out['baseline_firms']:.0f}")
    cols[1].metric("Scenario firms", f"{out['scenario_firms']:.0f}")
    cols[2].metric("Additional firms", f"{out['additional_firms']:.0f}")
    cols[3].metric("Scenario firm rate", fmt_pct(out["scenario_firm_rate"]))
    cols[4].metric("Estimated adviser reviews", f"{out['estimated_adviser_reviews']:,}")
    chart = pd.DataFrame({"Planning scenario": ["Baseline", "Targeted sequence"], "Firm choices": [out["baseline_firms"], out["scenario_firms"]]})
    st.plotly_chart(px.bar(chart, x="Planning scenario", y="Firm choices", text="Firm choices", title="Editable offer-holder planning scenario"), width="stretch")
    st.download_button("Download scenario CSV", csv_bytes(pd.DataFrame([out])), "offer_holder_conversion_scenario.csv", "text/csv")
    st.info("Recommended evaluation: randomised or phased message test using consent-aware internal records. Report delivered, opened, clicked, webinar registered, firm-choice conversion and opt-out rates by audience.")


def access_outreach(data: dict[str, pd.DataFrame]) -> None:
    page_intro(
        "Access and Outreach Planner",
        "Track published Access and Participation Plan milestone paths and build a signposting scenario. Milestones are planned paths, not measured current outcomes.",
        [("Official published targets", "#0f766e"), ("Planning assumption", "#7c3aed")],
    )
    targets = data["access_targets"].copy()
    target = st.selectbox("Access target", targets.reference.tolist(), format_func=lambda ref: f"{ref}: {targets.loc[targets.reference == ref, 'target_group'].iloc[0]}")
    row = targets[targets.reference == target].iloc[0]
    years = ["Baseline", "2025-26", "2026-27", "2027-28", "2028-29"]
    values = [row.baseline, row.milestone_2025_26, row.milestone_2026_27, row.milestone_2027_28, row.milestone_2028_29]
    path = pd.DataFrame({"Academic year": years, "Published target path": values})
    st.plotly_chart(px.line(path, x="Academic year", y="Published target path", markers=True, title=f"{target}: {row.target_group}", labels={"Published target path": row.unit.replace('_', ' ')}), width="stretch")
    st.caption("Published target path. This chart does not claim measured current performance.")
    with st.expander("Show all access and student-success milestone paths"):
        st.dataframe(targets, width="stretch", hide_index=True)
        st.dataframe(data["success_targets"], width="stretch", hide_index=True)
    st.markdown("### Open Day and outreach registration scenario")
    c1, c2, c3, c4 = st.columns(4)
    segment = c1.number_input("Eligible or prospective segment size", 100, 50000, 3000, 100)
    contacted = c2.slider("Contacted share", 0.0, 1.0, .70, .05)
    current = c3.slider("Current event-registration rate", 0.0, 1.0, .12, .01)
    uplift = c4.slider("Assumed uplift after clearer signposting (pp)", 0.0, 15.0, 2.0, .5)
    out = access_registration_scenario(int(segment), contacted, current, uplift)
    cols = st.columns(3)
    cols[0].metric("Baseline registrations", f"{out['baseline_registrations']:.0f}")
    cols[1].metric("Scenario registrations", f"{out['scenario_registrations']:.0f}")
    cols[2].metric("Additional registrations", f"{out['additional_registrations']:.0f}")
    st.markdown("### Support and pathway signposting")
    st.dataframe(data["funding"][["name", "audience", "benefit", "scale", "notes"]], width="stretch", hide_index=True)
    st.info("Use the official contextual-admissions eligibility checker. The public prototype must not classify an individual's eligibility from personal data.")


def crm_queue(data: dict[str, pd.DataFrame]) -> None:
    page_intro(
        "CRM Follow-up Queue",
        "Convert consent-aware synthetic or authorised CRM-style records into action queues. Uploaded files are processed for the current browser session and are not committed by the app.",
        [("Synthetic by default", "#6b7280"), ("Consent checks", "#9f1239")],
    )
    st.download_button("Download CRM upload template", (UPLOAD / "crm_upload_template.csv").read_bytes(), "crm_upload_template.csv", "text/csv")
    uploaded = st.file_uploader("Optional: upload a synthetic or authorised CRM CSV", type=["csv"], key="crm_upload")
    df = pd.read_csv(uploaded) if uploaded is not None else data["crm_demo"].copy()
    mode = "Authorised upload" if uploaded is not None else "Synthetic demonstration"
    missing = require_columns(df, CRM_REQUIRED)
    if missing:
        st.error("CRM file is missing required columns: " + ", ".join(missing))
        return
    st.markdown(mode_badge(mode), unsafe_allow_html=True)
    with st.expander("Edit records and workflow thresholds", expanded=False):
        edited = st.data_editor(df, num_rows="dynamic", width="stretch", hide_index=True)
        c1, c2, c3 = st.columns(3)
        threshold = c1.slider("High-score threshold", 30, 95, 65, 5)
        inactive = c2.slider("Inactive-days threshold", 7, 45, 21, 1)
        capacity = c3.number_input("Weekly adviser capacity", 1, 1000, 80, 5)
    if "edited" not in locals():
        edited = df
        threshold, inactive, capacity = 65, 21, 80
    triaged = triage_leads(edited, threshold, inactive, int(capacity))
    issues = crm_quality_issues(edited)
    cols = st.columns(5)
    cols[0].metric("Rows triaged", f"{len(triaged):,}")
    cols[1].metric("P1 leads", f"{(triaged.priority_level == 'P1').sum():,}")
    cols[2].metric("Selected this week", f"{triaged.selected_for_weekly_worklist.sum():,}")
    cols[3].metric("Data-check leads", f"{(triaged.priority_level == 'Data check').sum():,}")
    cols[4].metric("Quality issues", f"{len(issues):,}")
    tabs = st.tabs(["Action queue", "Weekly worklist", "Data-quality issues"])
    display_cols = ["lead_id", "population", "audience_stage", "subject_area", "course_interest", "campaign_source", "domicile_group", "consent_status", "lead_score", "priority_level", "recommended_action", "owner_team", "next_review_days", "selected_for_weekly_worklist"]
    with tabs[0]:
        st.dataframe(triaged[display_cols], width="stretch", hide_index=True)
        st.download_button("Download full action queue", csv_bytes(triaged), "crm_follow_up_queue.csv", "text/csv")
    with tabs[1]:
        weekly = triaged[triaged.selected_for_weekly_worklist]
        st.dataframe(weekly[display_cols], width="stretch", hide_index=True)
        st.download_button("Download weekly adviser worklist", csv_bytes(weekly), "weekly_adviser_worklist.csv", "text/csv")
    with tabs[2]:
        if issues.empty:
            st.success("No configured data-quality issues were found.")
        else:
            st.dataframe(issues, width="stretch", hide_index=True)
            st.download_button("Download records requiring correction", csv_bytes(issues), "crm_data_quality_issues.csv", "text/csv")
    source_footer("Do not upload personal data to a public deployment unless the organisation has approved the data-protection, access-control and retention process.")


def digital_journey(data: dict[str, pd.DataFrame]) -> None:
    page_intro(
        "Digital Journey Analytics Demo",
        "Explore a synthetic GA4-style campaign dataset from acquisition to form completion, event registration and application. This page demonstrates the measurement design, not University results.",
        [("Synthetic GA4-style data", "#6b7280"), ("UTM-aware", "#2563eb")],
    )
    st.download_button("Download digital analytics upload template", (UPLOAD / "digital_analytics_upload_template.csv").read_bytes(), "digital_analytics_upload_template.csv", "text/csv")
    uploaded = st.file_uploader("Optional: upload a schema-compatible campaign analytics CSV", type=["csv"], key="digital_upload")
    df = pd.read_csv(uploaded) if uploaded is not None else data["digital_demo"].copy()
    expected = ["date", "campaign", "audience", "channel", "impressions", "sessions", "landing_page_views", "form_starts", "form_completions", "event_registrations", "applications", "opt_outs"]
    missing = require_columns(df, expected)
    if missing:
        st.error("Digital analytics file is missing required columns: " + ", ".join(missing))
        return
    df["date"] = pd.to_datetime(df.date)
    f1, f2, f3 = st.columns(3)
    selected_campaigns = f1.multiselect("Campaign", sorted(df.campaign.unique()), default=sorted(df.campaign.unique()))
    selected_channels = f2.multiselect("Channel", sorted(df.channel.unique()), default=sorted(df.channel.unique()))
    selected_audiences = f3.multiselect("Audience", sorted(df.audience.unique()), default=sorted(df.audience.unique()))
    view = df[df.campaign.isin(selected_campaigns) & df.channel.isin(selected_channels) & df.audience.isin(selected_audiences)]
    totals = view[["impressions", "sessions", "landing_page_views", "form_starts", "form_completions", "event_registrations", "applications", "opt_outs"]].sum()
    cols = st.columns(5)
    cols[0].metric("Impressions", f"{totals.impressions:,.0f}")
    cols[1].metric("Sessions", f"{totals.sessions:,.0f}", fmt_pct(safe_div(totals.sessions, totals.impressions)) + " of impressions")
    cols[2].metric("Form completions", f"{totals.form_completions:,.0f}", fmt_pct(safe_div(totals.form_completions, totals.landing_page_views)) + " of landing views")
    cols[3].metric("Event registrations", f"{totals.event_registrations:,.0f}")
    cols[4].metric("Applications", f"{totals.applications:,.0f}")
    funnel = pd.DataFrame({"Journey stage": ["Impressions", "Sessions", "Landing-page views", "Form starts", "Form completions", "Event registrations", "Applications"], "Count": [totals.impressions, totals.sessions, totals.landing_page_views, totals.form_starts, totals.form_completions, totals.event_registrations, totals.applications]})
    st.plotly_chart(px.funnel(funnel, x="Count", y="Journey stage", title="Synthetic digital journey funnel"), width="stretch")
    campaign = view.groupby(["campaign", "audience", "channel"], as_index=False)[["impressions", "sessions", "landing_page_views", "form_starts", "form_completions", "event_registrations", "applications", "opt_outs"]].sum()
    campaign["form_completion_rate"] = campaign.apply(lambda r: fmt_pct(safe_div(r.form_completions, r.landing_page_views)), axis=1)
    campaign["application_rate"] = campaign.apply(lambda r: fmt_pct(safe_div(r.applications, r.sessions)), axis=1)
    st.dataframe(campaign, width="stretch", hide_index=True)
    st.download_button("Download filtered campaign-performance CSV", csv_bytes(campaign), "digital_campaign_performance.csv", "text/csv")
    source_footer("The University StaffNet Google Analytics guidance covers traffic acquisition, engagement, campaign tracking and responsible access. This page demonstrates a compatible reporting pattern with synthetic data.")


def governance(data: dict[str, pd.DataFrame]) -> None:
    page_intro(
        "Data Governance and Function Map",
        "Review source metadata, display rules, protected-data boundaries and the feature mapping from admissions reporting guidance to this public portfolio prototype.",
        [("Source-aware", "#0f766e"), ("Protected-data boundary", "#9f1239")],
    )
    st.markdown("### Public source registry")
    sources = data["sources"].copy()
    st.dataframe(sources[["source_id", "title", "publisher", "source_type", "source_as_of", "checked_at", "v5_use", "url", "notes"]], width="stretch", hide_index=True)
    st.download_button("Download source registry CSV", csv_bytes(sources), "source_registry.csv", "text/csv")
    st.markdown("### Display and governance rules")
    st.dataframe(data["quality_rules"], width="stretch", hide_index=True)
    st.markdown("### StaffNet-guide function mapping")
    mapping = pd.read_csv(REPORTS / "staffnet_function_mapping.csv")
    st.dataframe(mapping, width="stretch", hide_index=True)
    st.download_button("Download function mapping CSV", csv_bytes(mapping), "staffnet_function_mapping.csv", "text/csv")
    st.markdown("### Integration roadmap")
    st.dataframe(data["integration"], width="stretch", hide_index=True)
    c1, c2 = st.columns(2)
    c1.download_button("Download quick user guide", (REPORTS / "quick_user_guide.md").read_bytes(), "quick_user_guide.md", "text/markdown")
    c2.download_button("Download deployment guide", (REPORTS / "deployment_guide.md").read_bytes(), "deployment_guide.md", "text/markdown")
    st.warning("A production implementation would require data-protection review, role-based access, retention rules, audit logs, approved metric definitions, accessibility checks, user training and organisation-approved hosting.")


def main() -> None:
    data = load_data()
    with st.sidebar:
        st.markdown("## 🎓 Recruitment analytics V5")
        st.caption("Independent portfolio prototype")
        page = st.radio(
            "Page",
            [
                "Executive Overview",
                "Recruitment Campaign Calendar",
                "Admissions Operations Monitor",
                "International Market Monitor",
                "Published Course Funnel Explorer",
                "Campaign Strategy Builder",
                "Offer-holder Conversion Planner",
                "Access and Outreach Planner",
                "CRM Follow-up Queue",
                "Digital Journey Analytics Demo",
                "Data Governance and Function Map",
            ],
        )
        st.markdown("---")
        with st.expander("About this prototype", expanded=False):
            st.write("Official public data where available. Synthetic records for protected internal workflows. Uploaded files remain session-scoped in this app design.")
        if (REPORTS / "quick_user_guide.md").exists():
            st.download_button("Download quick user guide", (REPORTS / "quick_user_guide.md").read_bytes(), "quick_user_guide.md", "text/markdown", width="stretch")
        st.caption("Version 5 · public portfolio mode")

    if page == "Executive Overview":
        overview(data)
    elif page == "Recruitment Campaign Calendar":
        campaign_calendar(data)
    elif page == "Admissions Operations Monitor":
        admissions_operations(data)
    elif page == "International Market Monitor":
        international_markets(data)
    elif page == "Published Course Funnel Explorer":
        published_course_funnels(data)
    elif page == "Campaign Strategy Builder":
        strategy_builder(data)
    elif page == "Offer-holder Conversion Planner":
        offer_holder_planner(data)
    elif page == "Access and Outreach Planner":
        access_outreach(data)
    elif page == "CRM Follow-up Queue":
        crm_queue(data)
    elif page == "Digital Journey Analytics Demo":
        digital_journey(data)
    else:
        governance(data)


if __name__ == "__main__":
    main()
