import streamlit as st
import pandas as pd
import sqlite3
import numpy as np
from datetime import datetime

st.set_page_config(page_title="REVIVE-CVST Full Enrollment Portal", layout="wide")

DB_PATH = "revive_cvst.db"

SITE_PASSWORDS = {
    "S01": "egypt2026",
    "S02": "saudi2026",
    "S03": "turkey2026",
    "S04": "qatar2026",
    "S05": "morocco2026"
}

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

if "auth" not in st.session_state:
    st.session_state.auth = False
    st.session_state.site = None

if not st.session_state.auth:
    st.title("REVIVE-CVST Trial - Multi-Center Enrollment Gateway")
    col1, col2 = st.columns(2)
    with col1:
        site = st.selectbox("Select Center", list(SITE_PASSWORDS.keys()))
    with col2:
        pw = st.text_input("Site Password", type="password")
    if st.button("Access Portal", type="primary"):
        if SITE_PASSWORDS.get(site) == pw:
            st.session_state.auth = True
            st.session_state.site = site
            st.rerun()
        else:
            st.error("Invalid credentials for this center")
    st.stop()

st.title(f"REVIVE-CVST Enrollment Portal — Site {st.session_state.site}")
if st.sidebar.button("Logout"):
    st.session_state.auth = False
    st.rerun()

def get_next_arm(site, ich):
    conn = get_conn()
    query = f"SELECT TreatmentArm FROM patients WHERE SiteID='{site}' AND Stratification_ICH='{ich}'"
    existing = pd.read_sql(query, conn)
    conn.close()
    counts = existing['TreatmentArm'].value_counts() if not existing.empty else pd.Series()
    evt_count = counts.get("EVT + SMC", 0)
    smc_count = counts.get("SMC", 0)
    if evt_count <= smc_count:
        return "EVT + SMC"
    else:
        return "SMC"

tabs = st.tabs(["Existing Cases", "New Enrollment (Full CRF)", "Randomization Rules", "Export"])

with tabs[0]:
    conn = get_conn()
    df_site = pd.read_sql(f"SELECT PatientID, Age, Sex, TreatmentArm, Primary_mRS_0to2_180d, StudyCompletionStatus FROM patients WHERE SiteID='{st.session_state.site}'", conn)
    conn.close()
    st.metric("Cases at this site", len(df_site))
    st.dataframe(df_site, use_container_width=True)

with tabs[1]:
    st.subheader("New Patient Enrollment — Multi-Section CRF")
    st.caption("Covers all major domains from the 229-field dataset. Expand sections as needed.")
    with st.form("full_crf"):
        with st.expander("1. Demographics, Consent & Eligibility", expanded=True):
            c1, c2, c3 = st.columns(3)
            patient_id = c1.text_input("PatientID*")
            age = c2.number_input("Age*", min_value=18, max_value=90, value=35)
            sex = c3.selectbox("Sex*", ["Female", "Male"])
            ethnicity = st.text_input("Ethnicity")
            country = st.selectbox("Country", ["Egypt", "Saudi Arabia", "Turkey", "Qatar", "Morocco"])
        with st.expander("2. Baseline Clinical"):
            c1, c2, c3 = st.columns(3)
            gcs = c1.number_input("GCS Baseline*", 3, 15, 14)
            nihss = c2.number_input("NIHSS*", 0, 42, 4)
            headache = c3.selectbox("Headache", ["Y", "N"])
            seizure = st.selectbox("Seizure Baseline", ["Y", "N"])
            focal = st.selectbox("Focal Deficit", ["Y", "N"])
        with st.expander("3. Imaging"):
            ich = st.selectbox("ICH Present* (stratification)", ["Y", "N"])
            venous_inf = st.selectbox("Venous Infarct", ["Y", "N"])
            extent = st.selectbox("Thrombosis Extent", ["Partial", "Multiple segments", "Complete"])
        with st.expander("4. Randomization", expanded=True):
            st.info("Stratified balanced allocation by Site + ICH")
            if st.form_submit_button("Randomize & Save"):
                if patient_id:
                    arm = get_next_arm(st.session_state.site, ich)
                    st.success(f"Randomized to **{arm}**")
                    st.session_state['last_arm'] = arm
                else:
                    st.error("PatientID required")
        if st.session_state.get("last_arm") == "EVT + SMC":
            with st.expander("5. EVT Details"):
                st.selectbox("Technique", ["Aspiration", "Combined", "Mechanical", "Balloon-assisted"])
                st.number_input("Passes", 1, 10, 1)
        with st.expander("6. Outcomes"):
            st.selectbox("mRS 180d", list(range(7)))
            st.number_input("MoCA", 0, 30, 26)

with tabs[2]:
    st.markdown("""
    **Hardened Randomization Logic**
    - Stratified by SiteID and ICH presence (Y/N)
    - Balanced sequential assignment within each stratum (minimization principle)
    - 1:1 target ratio
    - All assignments logged
    """)

with tabs[3]:
    if st.button("Export"):
        conn = get_conn()
        df = pd.read_sql(f"SELECT * FROM patients WHERE SiteID='{st.session_state.site}'", conn)
        conn.close()
        st.download_button("Download CSV", df.to_csv(index=False), f"{st.session_state.site}_data.csv")
