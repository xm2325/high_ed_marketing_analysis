# University of Manchester Recruitment Marketing Strategy Tool — V4

A dynamic Streamlit portfolio prototype for a **Data Marketing and Analytics Officer** application. The app turns public University of Manchester and UCAS profile data into concrete student recruitment marketing questions, editable planning scenarios, and downloadable action plans.

## What is real and what is synthetic?

The following committed CSV snapshots use public data from official University of Manchester webpages and a UCAS profile whose student statistics are supplied by HESA:

- `uom_institution_profile.csv`
- `uom_decliner_signals.csv`
- `uom_admissions_funnel.csv`
- `uom_access_support.csv`
- `source_registry.csv`

The **CRM Workflow Sandbox** is synthetic. It demonstrates how authorised internal CRM records could be converted into a follow-up queue without claiming access to private Manchester data.

Scenario sliders are planning assumptions. They are not estimated causal effects.

## Interactive pages

1. **Manchester Snapshot** — institution and student-profile cards.
2. **Evidence-to-Strategy** — offer-holder decline signals converted into downloadable communication plans.
3. **Admissions Funnel Explorer** — dynamic Medicine and Dentistry application/interview/offer charts using Manchester-published counts.
4. **Offer-holder Conversion Scenario** — editable cohort, contact-rate, and uplift assumptions.
5. **Contextual Access Planner** — public access priorities, contextual admissions support, and outreach registration scenario.
6. **CRM Workflow Sandbox** — upload/edit synthetic or authorised CRM-style records and download a triaged queue.
7. **Data Sources & Limits** — source registry and production limits.

## Run locally

```bash
python -m pip install -r requirements.txt
streamlit run dashboard/streamlit_app.py
```

## Deploy from GitHub to Streamlit Community Cloud

1. Create a public GitHub repository and upload the contents of this folder.
2. Open Streamlit Community Cloud and create a new app from that repository.
3. Set the main file path to `dashboard/streamlit_app.py`.
4. Deploy. Later GitHub pushes update the app.

## Marketing strategy supported by the public data

The public evidence suggests three practical workstreams to test with internal data:

- **International offer-holder conversion:** test fee-value and accommodation information before firm-choice deadlines.
- **FSE subject-level offer-holder content:** test entry-requirement clarification, subject quality, and rankings content.
- **Contextual access communications:** improve signposting for eligibility, bursaries, eligible travel support, Open Days, online sessions, and outreach routes.

The app is designed to show how a marketing team can move from public evidence to testable actions while keeping descriptive evidence separate from internal causal evaluation.
