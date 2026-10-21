# REVIVE-CVST Enrollment Application

Multi-center clinical trial enrollment portal for the REVIVE-CVST study.

## Features
- Site-specific entry gateways (S01–S05)
- Pre-loaded with all 180 existing patients from the expanded dataset
- Stratified randomization (by Site + ICH)
- View existing cases filtered by site
- New enrollment form (prototype – expandable to full 229-field CRF)
- Data export per site

## Site Passwords (prototype)
- S01: site01_pass
- S02: site02_pass
- S03: site03_pass
- S04: site04_pass
- S05: site05_pass

## How to Run Locally
1. Place `revive_cvst.db` (preloaded database) in the same folder as the app.
2. Install dependencies: `pip install streamlit pandas`
3. Run: `streamlit run revive_cvst_app.py`

## Database
The SQLite database contains:
- `patients` table: all 180 records with expanded fields
- `sites` table: center information and access
- `randomization_log` table: for tracking new randomizations

## Next Steps for Production
- Expand the New Enrollment form into multi-section CRFs covering every field (demographics, baseline clinical, imaging/sinuses, labs, treatment/EVT details, outcomes, Tier 1/2 variables)
- Implement proper block randomization with allocation concealment
- Add audit trail, data validation, and role-based permissions
- Deploy to a secure server or Vercel/Streamlit Cloud

All 180 records from the Excel have been loaded into the database.
