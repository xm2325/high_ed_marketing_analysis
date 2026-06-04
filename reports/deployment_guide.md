# Deploy V5.2 to GitHub and Streamlit Community Cloud

## Replace the existing repository contents

1. Download and unzip `higher_ed_marketing_analytics_v5_2.zip`.
2. Replace the existing GitHub repository files with the V5.2 files. Upload the contents of the unzipped folder, not the zip file itself.
3. Confirm that the `reports/` and `data/public_snapshots/` folders are included.
4. Commit the update with a message such as:

```text
Deploy V5.2 marketing action centre
```

5. Keep the Streamlit entry point as:

```text
dashboard/streamlit_app.py
```

Streamlit Community Cloud should redeploy after the GitHub commit. If the deployed app does not refresh immediately, open app settings and reboot the app.

## Local check

```bash
python -m pip install -r requirements.txt
python src/generate_demo_data.py
python -m py_compile dashboard/streamlit_app.py src/*.py
pytest -q
streamlit run dashboard/streamlit_app.py
```

## File checklist

The `Data Governance and Function Map` page uses a robust fallback, but the repository should still include:

```text
reports/staffnet_function_mapping.csv
reports/quick_user_guide.md
reports/deployment_guide.md
data/public_snapshots/staffnet_function_mapping.csv
```

## Public deployment rule

The committed repository contains only official public snapshots and deterministic synthetic records. Do not commit internal admissions, CRM or GA4 exports. Do not upload personal data to a public deployment.
