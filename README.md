# REVIVE-CVST enrollment portal

Multicenter electronic data capture for [NCT07548346](https://clinicaltrials.gov/study/NCT07548346). Fourteen protocol sites, the full case-report form, 1:1 randomization stratified by site and intracranial hemorrhage, new-center IRB pre-registration, and trial-leadership desks.

The repository is preloaded with the 180 historical records (cutoff 30 September 2026).

## Run

```bash
pip install -r requirements.txt
streamlit run revive_cvst_app.py
```

On Streamlit Community Cloud, the main file may be `revive_cvst_app.py` or `streamlit_app.py`. Both run this portal. The public address is [https://revive-cvst-enrollment-app.streamlit.app](https://revive-cvst-enrollment-app.streamlit.app). A push to `main` rebuilds the app; if the old screen is still showing, open the app menu and choose Reboot.

## Who signs in

- A participating center uses its own site access code. Codes are not shown on the public page.
- A new center files pre-registration and an electronic IRB attestation. It cannot enroll until trial leadership activates it.
- Trial leadership (steering committee, DSMB, image core lab, IRB oversight, safety) uses the coordinating-center account. Alexandria (S01) can review the network. Every other site sees only its own cases.

New records are stored in `revive_protocol.db` beside the app. On Streamlit Community Cloud the disk resets when the app container is rebuilt, and the 180 historical records are loaded again from `data/seed.json`.
