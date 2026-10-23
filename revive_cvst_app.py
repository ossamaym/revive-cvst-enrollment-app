"""REVIVE-CVST enrollment portal for Streamlit Community Cloud.

NCT07548346. Fourteen protocol sites, full CRF, stratified randomization,
new-center IRB pre-registration, and trial-leadership desks.
"""

from __future__ import annotations

import json
import random
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "revive_protocol.db"
SCHEMA = json.loads((ROOT / "data" / "schema.json").read_text())
SEED = json.loads((ROOT / "data" / "seed.json").read_text())

SITES = [
    {"id": "S01", "name": "Alexandria University, Smouha Comprehensive Stroke Center", "city": "Alexandria", "country": "Egypt", "status": "Recruiting", "password": "smouha2026", "contact": "Ossama Mansour, MD, PhD"},
    {"id": "S02", "name": "Ain Shams University", "city": "Cairo", "country": "Egypt", "status": "Recruiting", "password": "ainshams2026", "contact": "Amr Mahmoud, MD"},
    {"id": "S03", "name": "Cairo University", "city": "Cairo", "country": "Egypt", "status": "Recruiting", "password": "cairouniv2026", "contact": "Farouk Hassan, MD"},
    {"id": "S04", "name": "Neurology Department, Al-Azhar University", "city": "Cairo", "country": "Egypt", "status": "Recruiting", "password": "azhar2026", "contact": "Khaled Sobh, MD"},
    {"id": "S05", "name": "Amman Specialized IR Center", "city": "Amman", "country": "Jordan", "status": "Not yet recruiting", "password": "amman2026", "contact": ""},
    {"id": "S06", "name": "Centre Hospitalier Universitaire Ibn Sina de Rabat", "city": "Rabat", "country": "Morocco", "status": "Not yet recruiting", "password": "rabat2026", "contact": ""},
    {"id": "S07", "name": "Aga Khan University", "city": "Karachi", "country": "Pakistan", "status": "Not yet recruiting", "password": "karachi2026", "contact": ""},
    {"id": "S08", "name": "Weill Cornell Medicine-Qatar", "city": "Doha", "country": "Qatar", "status": "Not yet recruiting", "password": "doha2026", "contact": ""},
    {"id": "S09", "name": "King Khalid University", "city": "Abha", "country": "Saudi Arabia", "status": "Recruiting", "password": "abha2026", "contact": "Ibrahim Alnaami, MD"},
    {"id": "S10", "name": "King Abdulaziz Medical City", "city": "Jeddah", "country": "Saudi Arabia", "status": "Not yet recruiting", "password": "jeddah2026", "contact": ""},
    {"id": "S11", "name": "King Abdullah Medical City", "city": "Mecca", "country": "Saudi Arabia", "status": "Not yet recruiting", "password": "mecca2026", "contact": ""},
    {"id": "S12", "name": "Institut National de Neurologie", "city": "Tunis", "country": "Tunisia", "status": "Not yet recruiting", "password": "tunis2026", "contact": ""},
    {"id": "S13", "name": "Department of Neurology, Eskisehir Osmangazi University", "city": "Eskisehir", "country": "Türkiye", "status": "Not yet recruiting", "password": "eskisehir2026", "contact": ""},
    {"id": "S14", "name": "Neurology Department, Dr. Lutfi Kirdar City Hospital", "city": "Istanbul", "country": "Türkiye", "status": "Not yet recruiting", "password": "istanbul2026", "contact": ""},
]
LEAD_EMAIL = "yassinossa@yahoo.com"
LEAD_PASSWORD = "wael25407M" + "@&#"
PRE_REG = [
    ("pi", "Local principal investigator named and available"),
    ("protocol", "Current protocol and consent reviewed for local feasibility"),
    ("irb", "IRB/ethics submission filed, or approval letter uploaded by reference number"),
    ("consent", "Consent will be used only after local ethics approval and in the local language"),
    ("imaging", "CTV, MRV, or DSA is available for diagnosis and follow-up imaging"),
    ("ac", "Anticoagulation pathway (UFH, LMWH, then oral agent) is in place"),
    ("evt", "EVT team can treat within 24 hours of randomization when assigned"),
    ("delegation", "Delegation of duties will be kept before the first enrollment"),
    ("privacy", "Site agrees to the trial confidentiality and data-protection terms"),
    ("safety", "A safety contact is named for SAE and DSMB reporting"),
]
MAJOR = ["Sinus_SSS", "Sinus_Transverse_L", "Sinus_Transverse_R", "Sinus_Sigmoid_L", "Sinus_Sigmoid_R", "Sinus_Straight", "Sinus_DeepSystem"]
SEVERITY = ["Severity_GCS_9to14", "Severity_ICH", "Severity_VenousInfarct", "Severity_DeepSystem", "Severity_Seizures", "Severity_FocalDeficit", "Severity_ICP"]
LOCKED = {"BMI", "SymptomDuration_hours", "TreatmentArm", "Stratification_ICH", "Stratification_Site", "Primary_mRS_0to2_180d", "Primary_mRS_0to2_12m"}
DOMAINS = []
for field in SCHEMA:
    if field["domain"] not in DOMAINS:
        DOMAINS.append(field["domain"])


def connect():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("CREATE TABLE IF NOT EXISTS kv (bucket TEXT, key TEXT, payload TEXT, PRIMARY KEY (bucket, key))")
    return conn


def load_bucket(bucket: str) -> dict:
    with connect() as conn:
        rows = conn.execute("SELECT key, payload FROM kv WHERE bucket = ?", (bucket,)).fetchall()
    return {key: json.loads(payload) for key, payload in rows}


def save_item(bucket: str, key: str, value) -> None:
    with connect() as conn:
        conn.execute(
            "INSERT INTO kv (bucket, key, payload) VALUES (?, ?, ?) ON CONFLICT(bucket, key) DO UPDATE SET payload = excluded.payload",
            (bucket, key, json.dumps(value)),
        )


def ensure_seed() -> None:
    if load_bucket("patient"):
        return
    for row in SEED:
        if row.get("PatientID"):
            save_item("patient", row["PatientID"], {k: "" if v is None else str(v) for k, v in row.items()})


def patients() -> list[dict]:
    return list(load_bucket("patient").values())


def sites() -> list[dict]:
    extra = list(load_bucket("site").values())
    return SITES + extra


def site_by_id(site_id: str) -> dict | None:
    return next((site for site in sites() if site["id"] == site_id), None)


def num(value) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number == number else None


def parse_when(value: str) -> float | None:
    if not value:
        return None
    text = value.strip().replace(" ", "T")
    try:
        return datetime.fromisoformat(text).timestamp()
    except ValueError:
        return None


def derive(record: dict) -> dict:
    rec = dict(record)
    weight, height = num(rec.get("Weight_kg")), num(rec.get("Height_cm"))
    if weight and height and height > 0:
        rec["BMI"] = f"{weight / (height / 100) ** 2:.1f}"
    onset, rand, admit = parse_when(rec.get("SymptomOnsetDateTime", "")), parse_when(rec.get("RandomizationDateTime", "")), parse_when(rec.get("AdmissionDateTime", ""))
    if onset is not None and rand is not None and rand >= onset:
        hours = (rand - onset) / 3600
        rec["SymptomDuration_hours"] = f"{hours:.1f}"
        rec["OnsetToRandomization_days"] = f"{hours / 24:.2f}"
    elif onset is not None and admit is not None and not rec.get("SymptomDuration_hours"):
        rec["SymptomDuration_hours"] = f"{(admit - onset) / 3600:.1f}"
    m180 = num(rec.get("FU180_mRS"))
    if rec.get("FU180_mRS") not in (None, "") and m180 is not None:
        rec["Primary_mRS_0to2_180d"] = "Y" if m180 <= 2 else "N"
    m12 = num(rec.get("FU12m_mRS"))
    if rec.get("FU12m_mRS") not in (None, "") and m12 is not None:
        rec["Primary_mRS_0to2_12m"] = "Y" if m12 <= 2 else "N"
    if rec.get("Hemorrhage_Present") in ("Y", "N"):
        rec["Stratification_ICH"] = rec["Hemorrhage_Present"]
        rec["Severity_ICH"] = rec["Hemorrhage_Present"]
    return rec


def eligibility(rec: dict) -> list[str]:
    issues = []
    if not str(rec.get("PatientID", "")).strip():
        issues.append("Patient ID is required.")
    age = num(rec.get("Age"))
    if age is None or age < 18 or age > 65:
        issues.append("Age must be 18–65 years.")
    if rec.get("Sex") not in ("Male", "Female"):
        issues.append("Sex is required.")
    if not rec.get("ConsentDate"):
        issues.append("Consent date is required and must precede randomization.")
    if rec.get("ConsentType") not in ("Patient", "LAR"):
        issues.append("Consent type must be Patient or LAR.")
    if rec.get("Eligible") != "Y":
        issues.append("Eligible must be Y before randomization.")
    if not str(rec.get("Country", "")).strip():
        issues.append("Country is required.")
    if not rec.get("SymptomOnsetDateTime"):
        issues.append("Symptom onset date/time is required.")
    days = num(rec.get("OnsetToRandomization_days"))
    if rec.get("RandomizationDateTime") and days is not None and days > 21:
        issues.append("Symptom onset must be ≤21 days before randomization.")
    premorbid = num(rec.get("Premorbid_mRS"))
    if premorbid is None or premorbid > 2:
        issues.append("Premorbid mRS must be 0–2.")
    gcs = num(rec.get("GCS_Baseline"))
    if gcs is None or gcs < 9 or gcs > 15:
        issues.append("Baseline GCS must be 9–15 (GCS <9 is excluded).")
    if num(rec.get("NIHSS_Baseline")) is None:
        issues.append("Baseline NIHSS is required.")
    if not any(rec.get(key) == "Y" for key in SEVERITY):
        issues.append("At least one protocol severity marker must be Y.")
    if not rec.get("Imaging_Modality"):
        issues.append("Imaging modality (CTV, MRV, DSA, or Multiple) is required.")
    if not rec.get("Imaging_Date"):
        issues.append("Diagnostic imaging date is required.")
    if rec.get("MRI_Phase") not in ("Acute", "Subacute"):
        issues.append("MRI phase must be Acute or Subacute (chronic phase is excluded).")
    if rec.get("SignificantOutflowObstruction") != "Y":
        issues.append("Significant outflow obstruction is an inclusion criterion.")
    if rec.get("Hemorrhage_Present") not in ("Y", "N"):
        issues.append("Intracranial hemorrhage (Y/N) is required — it is a stratification factor.")
    if rec.get("MidlineShift_gt10") == "Y":
        issues.append("Midline shift >10 mm requiring surgery is an exclusion.")
    if rec.get("Risk_Pregnancy") == "Y":
        issues.append("Current pregnancy is an exclusion.")
    major = any(rec.get(key) == "Y" for key in MAJOR)
    if not major and rec.get("Sinus_CorticalVeins") == "Y":
        issues.append("Isolated cortical-vein thrombosis is excluded.")
    if not major and rec.get("Sinus_CorticalVeins") != "Y":
        issues.append("At least one major dural sinus must be involved.")
    return issues


def take_arm(site: str, ich: str) -> str:
    blocks = load_bucket("block")
    key = f"{site}|{'Y' if ich == 'Y' else 'N'}"
    queue = list(blocks.get(key, []))
    if not queue:
        queue = ["EVT_plus_AC", "EVT_plus_AC", "AC_alone", "AC_alone"]
        random.shuffle(queue)
    arm = queue.pop(0)
    save_item("block", key, queue)
    return arm


def arm_label(arm: str) -> str:
    return {"EVT_plus_AC": "EVT + anticoagulation", "AC_alone": "Anticoagulation alone"}.get(arm, arm or "Not randomized")


def stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def widget(field: dict, current: str) -> str:
    label = field["label"] + (" *" if field.get("required") else "")
    key = f"f_{field['name']}"
    if field["name"] in LOCKED:
        st.text_input(label, value=current, disabled=True, key=key)
        return current
    options = field.get("options") or []
    if field["type"] == "Categorical" and options:
        choices = [""] + options
        index = choices.index(current) if current in choices else 0
        return st.selectbox(label, choices, index=index, key=key)
    if field["type"] == "Date":
        return st.text_input(label, value=current, placeholder="YYYY-MM-DD", key=key)
    return st.text_input(label, value=current, key=key)


ensure_seed()
st.set_page_config(page_title="REVIVE-CVST", page_icon="🩺", layout="wide")
auth = st.session_state.setdefault("auth", None)

if auth is None:
    st.title("REVIVE-CVST")
    st.caption("NCT07548346 · MENASINO-REVIVE-2026-01 · target 440 · mRS shift at 180 days")
    left, right = st.columns(2)
    with left:
        st.subheader("Participating center")
        roster = sites()
        labels = {f"{site['id']} · {site['city']} — {site['name']}": site["id"] for site in roster}
        with st.form("site-gate"):
            choice = st.selectbox("Center", list(labels))
            code = st.text_input("Site access code", type="password")
            open_site = st.form_submit_button("Open center gateway", type="primary")
        if open_site:
            site = site_by_id(labels[choice])
            if site and code.strip() == site["password"]:
                st.session_state.auth = {"role": "site", "site": site["id"]}
                st.rerun()
            st.error("That access code does not match this center.")
        with st.expander("Prototype access codes for the 14 protocol sites"):
            for site in SITES:
                st.write(f"{site['id']} {site['city']}: {site['password']}")
    with right:
        st.subheader("Trial leadership")
        st.caption("Use yassinossa@yahoo.com. The password ends with the three symbols @ & #")
        with st.form("lead-gate"):
            email = st.text_input("Email", value=LEAD_EMAIL)
            password = st.text_input("Password", type="password")
            open_lead = st.form_submit_button("Open leadership desks")
        if open_lead:
            if email.strip().lower() == LEAD_EMAIL and password.strip() == LEAD_PASSWORD:
                st.session_state.auth = {"role": "lead"}
                st.rerun()
            st.error("Those leadership credentials were not accepted. The password is case-sensitive and ends with @&#")
    st.subheader("New center")
    st.caption("Pre-registration and electronic IRB attestation. Enrollment stays closed until leadership activates the site.")
    with st.form("join"):
        c1, c2, c3 = st.columns(3)
        center = c1.text_input("Center name")
        city = c2.text_input("City")
        country = c3.text_input("Country")
        pi = c1.text_input("Principal investigator")
        pi_email = c2.text_input("PI email")
        phone = c3.text_input("PI phone")
        annual = c1.text_input("Estimated CVST cases per year")
        evt = c2.selectbox("EVT within 24 hours", ["", "Y", "N"])
        imaging = c3.selectbox("Diagnostic imaging", ["", "CTV", "MRV", "DSA", "Multiple"])
        irb_status = c1.selectbox("IRB / ethics status", ["Submitted", "Approved"])
        irb_number = c2.text_input("IRB reference number")
        irb_date = c3.text_input("IRB date", placeholder="YYYY-MM-DD")
        checks = {key: st.checkbox(label) for key, label in PRE_REG}
        signature = st.text_input("Electronic signature (full name)")
        title = st.text_input("Title", value="Principal investigator")
        attest = st.checkbox("I sign this pre-registration and IRB attestation electronically.")
        if st.form_submit_button("Sign and submit pre-registration", type="primary"):
            missing = [label for key, label in PRE_REG if not checks[key]]
            if not all([center.strip(), city.strip(), country.strip(), pi.strip()]) or "@" not in pi_email:
                st.error("Center, city, country, investigator, and a valid email are required.")
            elif missing or not irb_number.strip() or not attest or len(signature.strip()) < 3:
                st.error("Complete every checklist item, the IRB reference, and the signature.")
            else:
                app_id = "APP-" + str(int(datetime.now().timestamp()))[-6:]
                save_item("application", app_id, {
                    "id": app_id, "submittedAt": stamp(), "status": "Pending review",
                    "centerName": center, "city": city, "country": country, "piName": pi,
                    "piEmail": pi_email, "piPhone": phone, "annualCvst": annual, "evtCapable": evt,
                    "imaging": imaging, "irbStatus": irb_status, "irbNumber": irb_number, "irbDate": irb_date,
                    "checklist": checks, "signatureName": signature, "signatureTitle": title,
                    "signatureDate": stamp()[:10], "issuedSiteId": "", "issuedPassword": "",
                })
                st.success(f"Application {app_id} is with the coordinating center.")
    st.stop()

if st.button("Leave"):
    st.session_state.auth = None
    st.session_state.pop("edit_id", None)
    st.rerun()

if auth["role"] == "lead":
    st.title("REVIVE-CVST leadership")
    st.caption(LEAD_EMAIL)
    desk = st.radio("Desk", ["Steering committee", "DSMB", "Image core lab", "IRB oversight", "Safety"], horizontal=True)
    rows = patients()
    if desk == "Steering committee":
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Enrolled", f"{len(rows)} / 440")
        c2.metric("EVT + AC", sum(r.get("TreatmentArm") == "EVT_plus_AC" for r in rows))
        c3.metric("AC alone", sum(r.get("TreatmentArm") == "AC_alone" for r in rows))
        c4.metric("Center files", len(load_bucket("application")))
        table = []
        for site in sites():
            table.append({"Site": site["id"], "City": site["city"], "Name": site["name"], "Status": site["status"], "Cases": sum(r.get("SiteID") == site["id"] for r in rows)})
        st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)
    elif desk == "DSMB":
        flags = ["sICH_72h", "MajorBleeding", "Death_30d", "Death_180d", "Death_12m", "SAE_Any", "EVT_Complication_Perforation", "EVT_Complication_NewICH"]
        st.dataframe(pd.DataFrame([{"Signal": flag, "Count": sum(r.get(flag) == "Y" for r in rows)} for flag in flags]), hide_index=True)
    elif desk == "Image core lab":
        queue = [r for r in rows if r.get("Day7_ImagingDone") == "Y" or r.get("FU90_ImagingDone") == "Y"]
        if not queue:
            st.info("No imaging packages are waiting.")
        else:
            pick = st.selectbox("Package", [r["PatientID"] for r in queue])
            current = next(r for r in queue if r["PatientID"] == pick)
            st.write(f"Site grade, day 7: {current.get('Day7_Recanalization') or '—'} · day 90: {current.get('FU90_Recanalization') or '—'}")
            reader = st.text_input("Reader", "Core lab")
            day7 = st.selectbox("Core-lab recanalization, day 7", ["", "None", "Partial", "Complete"])
            day90 = st.selectbox("Core-lab recanalization, day 90", ["", "None", "Partial", "Complete"])
            note = st.text_area("Note")
            if st.button("Save core-lab read"):
                save_item("core", pick, {"patientId": pick, "reader": reader, "day7": day7, "day90": day90, "note": note, "at": stamp()})
                st.success("Core-lab read saved.")
    elif desk == "IRB oversight":
        apps = list(load_bucket("application").values())
        if not apps:
            st.info("No center has filed yet.")
        else:
            pick = st.selectbox("Application", [f"{item['id']} · {item['centerName']} · {item['status']}" for item in apps])
            item = next(item for item in apps if pick.startswith(item["id"]))
            st.write(f"{item['city']}, {item['country']} · {item['piName']} · {item['piEmail']}")
            st.write(f"IRB {item['irbStatus']} {item['irbNumber']} · signed by {item['signatureName']} on {item['signatureDate']}")
            for key, label in PRE_REG:
                st.write(("Confirmed" if item["checklist"].get(key) else "Missing") + " — " + label)
            note = st.text_area("Review note")
            if item.get("issuedSiteId"):
                st.success(f"Activated as {item['issuedSiteId']}. Access code: {item['issuedPassword']}")
            else:
                a, b, c = st.columns(3)
                if a.button("Activate site", type="primary"):
                    numbers = [int("".join(ch for ch in site["id"] if ch.isdigit()) or 0) for site in sites()]
                    new_id = f"S{max(numbers) + 1:02d}"
                    new_password = "revive" + stamp()[-4:].replace(":", "")
                    save_item("site", new_id, {"id": new_id, "name": item["centerName"], "city": item["city"], "country": item["country"], "status": "Recruiting", "password": new_password, "contact": item["piName"]})
                    item.update({"status": "Activated", "issuedSiteId": new_id, "issuedPassword": new_password, "reviewNote": note})
                    save_item("application", item["id"], item)
                    st.rerun()
                if b.button("Return"):
                    item.update({"status": "Returned", "reviewNote": note})
                    save_item("application", item["id"], item)
                    st.rerun()
                if c.button("Decline"):
                    item.update({"status": "Declined", "reviewNote": note})
                    save_item("application", item["id"], item)
                    st.rerun()
    else:
        flags = ["sICH_72h", "MajorBleeding", "Death_30d", "SAE_Any", "EVT_Complication_NewICH"]
        flagged = [r for r in rows if any(r.get(flag) == "Y" for flag in flags)]
        st.dataframe(pd.DataFrame([{
            "Patient": r.get("PatientID"), "Site": r.get("SiteID"), "Arm": arm_label(r.get("TreatmentArm", "")),
            "sICH 72h": r.get("sICH_72h", ""), "Major bleed": r.get("MajorBleeding", ""), "Death 30d": r.get("Death_30d", ""), "SAE": r.get("SAE_Any", ""),
        } for r in flagged]), use_container_width=True, hide_index=True)
    st.stop()

site = site_by_id(auth["site"])
st.title(f"{site['id']} · {site['city']}")
st.caption(site["name"])
visible = patients() if site["id"] == "S01" else [row for row in patients() if row.get("SiteID") == site["id"]]
tab_reg, tab_case = st.tabs(["Registry", "Case record"])
with tab_reg:
    st.metric("Cases in this view", len(visible))
    frame = pd.DataFrame([{
        "Patient": row.get("PatientID"), "Site": row.get("SiteID"), "Age": row.get("Age"), "Sex": row.get("Sex"),
        "ICH": row.get("Stratification_ICH") or row.get("Hemorrhage_Present"), "Arm": arm_label(row.get("TreatmentArm", "")),
        "NIHSS": row.get("NIHSS_Baseline"), "mRS 180d": row.get("FU180_mRS"), "Status": row.get("StudyCompletionStatus") or "Open",
    } for row in visible])
    st.dataframe(frame, use_container_width=True, hide_index=True)
    st.download_button("Export this view", frame.to_csv(index=False), file_name=f"{site['id']}-revive-cvst.csv")
    ids = ["New enrollment"] + [row["PatientID"] for row in visible]
    st.session_state.edit_id = st.selectbox("Open a record", ids, index=0 if st.session_state.get("edit_id") in (None, "") else max(ids.index(st.session_state.edit_id) if st.session_state.get("edit_id") in ids else 0, 0))

with tab_case:
    editing = st.session_state.get("edit_id")
    existing = next((row for row in patients() if row.get("PatientID") == editing), None) if editing and editing != "New enrollment" else None
    draft = dict(existing or {"SiteID": site["id"], "Country": site["country"]})
    st.write("Blank fields stay blank. Derived fields and the assigned arm are locked.")
    domain = st.selectbox("CRF section", DOMAINS)
    collected = dict(draft)
    for field in SCHEMA:
        if field["domain"] != domain:
            continue
        if field["domain"] == "EVT Procedure" and draft.get("TreatmentArm") != "EVT_plus_AC" and field["name"] != "EVT_Performed":
            continue
        if field["name"] == "SiteID":
            collected["SiteID"] = site["id"] if site["id"] != "S01" else widget(field, draft.get("SiteID", site["id"]))
            continue
        collected[field["name"]] = widget(field, str(draft.get(field["name"], "") or ""))
    collected = derive(collected)
    issues = eligibility(collected) if collected.get("TreatmentArm") or st.session_state.get("want_randomize") else []
    if collected.get("TreatmentArm"):
        st.info("Arm: " + arm_label(collected["TreatmentArm"]) + " · ICH stratum " + (collected.get("Stratification_ICH") or "—"))
    if issues and collected.get("Eligible") == "Y":
        st.warning("Not ready to randomize:\n\n- " + "\n- ".join(issues))
    save_col, rand_col = st.columns(2)
    if save_col.button("Save section", type="primary"):
        merged = derive({**draft, **collected, "SiteID": collected.get("SiteID") or site["id"]})
        if not merged.get("PatientID"):
            st.error("Patient ID is required before saving.")
        else:
            save_item("patient", merged["PatientID"], merged)
            st.session_state.edit_id = merged["PatientID"]
            st.success("Saved " + merged["PatientID"])
    if rand_col.button("Randomize 1:1"):
        merged = derive({**draft, **collected, "SiteID": collected.get("SiteID") or site["id"]})
        problems = eligibility(merged)
        if merged.get("TreatmentArm"):
            st.error("This record already has an arm.")
        elif problems:
            st.error("Fix eligibility before randomization:\n\n- " + "\n- ".join(problems))
        else:
            ich = merged.get("Hemorrhage_Present") or "N"
            merged["TreatmentArm"] = take_arm(merged["SiteID"], ich)
            merged["Stratification_Site"] = merged["SiteID"]
            merged["Stratification_ICH"] = "Y" if ich == "Y" else "N"
            if not merged.get("RandomizationDateTime"):
                merged["RandomizationDateTime"] = stamp()
            save_item("patient", merged["PatientID"], derive(merged))
            st.session_state.edit_id = merged["PatientID"]
            st.success("Assigned " + arm_label(merged["TreatmentArm"]))
            st.rerun()
