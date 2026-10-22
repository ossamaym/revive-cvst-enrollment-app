# REVIVE-CVST Enrollment Portal

Multi-center electronic data capture and enrollment application for the REVIVE-CVST trial.

## Features
- Site-specific login gateways (S01–S05)
- Pre-loaded with 180 historical records
- Multi-section CRF data entry
- Stratified balanced randomization (by Site + ICH)
- Export capability

## Local Run
```bash
pip install -r requirements.txt
streamlit run revive_cvst_app.py
```

## Site Passwords (prototype)
- S01: egypt2026
- S02: saudi2026
- S03: turkey2026
- S04: qatar2026
- S05: morocco2026

## Database
The SQLite database (`revive_cvst.db`) containing the 180 pre-loaded patients must be placed in the same directory as the app for full functionality. For Streamlit Community Cloud deployment, include the DB in the repository (note: large binary files may require Git LFS).

## Deployment
Recommended: Streamlit Community Cloud (share.streamlit.io). Connect the GitHub repo and set main file to `revive_cvst_app.py`.
