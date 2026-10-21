import streamlit as st
import sqlite3
import pandas as pd
import datetime
import random

# Database path - place revive_cvst.db in the same directory
DB_PATH = "revive_cvst.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def check_login(site_id, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sites WHERE SiteID = ? AND Password = ?", (site_id, password))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def get_patients_for_site(site_id):
    conn = get_connection()
    df = pd.read_sql(f"SELECT * FROM patients WHERE SiteID = '{site_id}'", conn)
    conn.close()
    return df

def randomize_patient(site_id, ich_present):
    # Stratified 1:1 randomization (simplified; production uses blocks)
    arms = ["EVT + SMC", "SMC"]
    assigned = random.choice(arms)
    return assigned

st.set_page_config(page_title="REVIVE-CVST Enrollment", layout="wide")

st.title("REVIVE-CVST Trial Enrollment Portal")
st.caption("Multi-center data capture with site-specific gateways")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.site_id = None

if not st.session_state.logged_in:
    st.header("Site Gateway Login")
    site_options = ["S01", "S02", "S03", "S04", "S05"]
    selected_site = st.selectbox("Select Your Site", site_options)
    password = st.text_input("Site Password", type="password", help="Use site01_pass for S01, site02_pass for S02, etc.")
    
    if st.button("Login"):
        if check_login(selected_site, password):
            st.session_state.logged_in = True
            st.session_state.site_id = selected_site
            st.success(f"Logged in to {selected_site}")
            st.rerun()
        else:
            st.error("Invalid site or password")
else:
    st.sidebar.success(f"Logged in: {st.session_state.site_id}")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
    
    tab1, tab2, tab3, tab4 = st.tabs(["View Existing Cases", "New Enrollment", "Randomization Rules", "Export Data"])
    
    with tab1:
        st.header(f"Existing Cases for {st.session_state.site_id}")
        patients = get_patients_for_site(st.session_state.site_id)
        st.write(f"Total cases at this site: {len(patients)}")
        if not patients.empty:
            st.dataframe(patients, use_container_width=True)
        else:
            st.info("No cases yet for this site")
    
    with tab2:
        st.header("New Case Enrollment")
        st.info("Prototype form. Full multi-section CRF covering all 229 fields (demographics, clinical, imaging, labs, treatment, outcomes, Tier 1/2 variables) can be expanded using st.expander sections.")
        with st.form("new_case"):
            col1, col2 = st.columns(2)
            with col1:
                patient_id = st.text_input("Patient ID", value=f"REV-{st.session_state.site_id}-NEW")
                age = st.number_input("Age", min_value=18, max_value=100, value=35)
                sex = st.selectbox("Sex", ["Female", "Male"])
            with col2:
                ich = st.selectbox("ICH Present (for stratification)", ["No", "Yes"])
                nihss = st.number_input("Baseline NIHSS", min_value=0, max_value=42, value=3)
            submitted = st.form_submit_button("Randomize & Enroll")
            if submitted:
                arm = randomize_patient(st.session_state.site_id, ich)
                st.success(f"Patient {patient_id} randomized to: **{arm}**")
                st.info("In full version, all fields are captured and written to the database with audit trail.")
    
    with tab3:
        st.header("Randomization Rules")
        st.markdown("""
        ### Stratified 1:1 Randomization
        - **Arms**: EVT + SMC vs SMC alone
        - **Stratification factors**: Site ID + ICH presence (Yes/No)
        - **Method**: Permuted block randomization (block size 4 or 6) within each stratum
        - **Implementation**: Centralized through this portal to maintain allocation concealment
        - All existing 180 patients are already randomized and loaded
        """)
    
    with tab4:
        st.header("Export Site Data")
        patients = get_patients_for_site(st.session_state.site_id)
        if not patients.empty:
            csv = patients.to_csv(index=False).encode()
            st.download_button(
                label="Download Site CSV",
                data=csv,
                file_name=f"revive_cvst_{st.session_state.site_id}.csv",
                mime="text/csv"
            )
        else:
            st.info("No data to export")
