# Recruitment Marketing Analytics Tool — V5.2 quick user guide

## Purpose

This independent portfolio prototype demonstrates how public University of Manchester evidence, time-sensitive campaign planning and protected internal workflows could be connected in a student recruitment marketing analytics service.

The tool is **not** an official University system. Official public snapshots, synthetic demonstration records, editable planning assumptions and authorised upload interfaces are labelled separately.

## Suggested five-minute demo route

1. Open **Recruitment Campaign Calendar** to show that activity is planned around deadlines, Open Days and Clearing rather than treated as a single reporting period.
2. Open **Marketing Action Centre** and choose one objective, such as `Improve international offer-holder conversion`.
3. Review the generated audience, trigger, timed actions, owner teams, KPIs and protected-data boundary.
4. Download the action-plan CSV or ICS calendar to show how an insight becomes an operational workflow.
5. Open **CRM Follow-up Queue** to show consent checks, data-quality checks and weekly adviser capacity.

## Marketing Action Centre

The new V5.2 page supports five objectives:

- international offer-holder conversion;
- Open Day attendance and application starts;
- incomplete-form recovery;
- Clearing rapid response;
- contextual-access outreach engagement.

For each objective, users can edit the anchor date, potential audience size, targeted share, weekly adviser capacity and evaluation design. The page then generates:

- decision brief;
- evidence basis and protected-data boundary;
- timed playbook;
- measurement-field specification;
- CRM workflow rule;
- chat-ready summary;
- CSV and ICS downloads.

## Other main pages

- **Executive Overview**: confirm scope and source-aware headline figures.
- **Recruitment Campaign Calendar**: filter official UG deadlines, Open Days and Clearing dates. Download CSV or ICS files. Build tagged external-campaign URLs with the UTM builder.
- **Admissions Operations Monitor**: explore cycle-week, hierarchy, fee-status, UG/PG and course-level filters. The default records are synthetic.
- **International Market Monitor**: review synthetic country-of-domicile and Top Markets patterns.
- **Published Course Funnel Explorer**: use official public Medicine and Dentistry examples for monitoring demonstrations, not individual prediction.
- **Campaign Strategy Builder**: translate descriptive signals into a communication-plan draft.
- **Offer-holder Conversion Planner**: size a campaign trial and estimate adviser workload using editable assumptions.
- **Access and Outreach Planner**: inspect published milestone paths and signposting scenarios.
- **CRM Follow-up Queue**: review action queues, data checks and weekly worklists.
- **Digital Journey Analytics Demo**: inspect the synthetic acquisition-to-application measurement design.
- **Data Governance and Function Map**: review source metadata, limits and reporting-function mapping.

## Data labels

- **Official public data**: committed snapshots from official public webpages or PDFs.
- **Published historical data**: official figures suitable for monitoring examples but not forecasting.
- **Provisional published figure**: official figure marked as provisional on the source page.
- **Planning assumption**: editable scenario input; not a measured effect.
- **Synthetic demonstration**: reproducible non-personal records generated for portfolio use.
- **Authorised upload**: optional session-scoped CSV processing for an approved environment.

## Protected-data boundary

Do not upload identifiable applicant, student or CRM records to a public Streamlit deployment. A production implementation would need an approved hosting environment, role-based access, retention rules, audit logs, data-protection review and staff training.
