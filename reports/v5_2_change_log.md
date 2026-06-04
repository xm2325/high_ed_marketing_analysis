# V5.2 change log

## Main improvement

Added a dynamic **Marketing Action Centre** so the portfolio prototype supports the full path:

```text
public evidence
→ marketing objective
→ audience and trigger
→ timed playbook
→ named owners
→ CRM workflow rule
→ measurement fields
→ evaluation design
→ downloadable action plan
```

## Included playbooks

1. International offer-holder conversion
2. Open Day attendance and application starts
3. Incomplete-form recovery
4. Clearing rapid response
5. Contextual-access outreach engagement

## Validation

- `python -m py_compile dashboard/streamlit_app.py src/*.py`
- `pytest -q`: 7 tests passed
- Streamlit AppTest: 12 pages opened without exceptions
