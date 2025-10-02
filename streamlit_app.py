
import io
import requests
import streamlit as st

st.set_page_config(page_title="Project O.A — Runner", layout="wide")
st.title("Project O.A — Baseline Runner")

API_BASE = st.secrets.get("API_BASE", "").rstrip("/") + "/"
API_KEY = st.secrets.get("API_KEY", "")

if not API_BASE or not API_KEY:
    st.warning("API_BASE and/or API_KEY not set in Streamlit secrets. Go to App settings → Secrets.")
HEADERS = {"x-api-key": API_KEY} if API_KEY else {}

tabs = st.tabs(["Run Checkpoint", "Finalize (Boost→Uplift)", "OA_FACINGS Admin"])

with tabs[0]:
    st.subheader("Checkpoint: Store Fill (MSQ-rounded, no extras)")
    master = st.file_uploader("Master workbook (.xlsx)", type=["xlsx"], key="master_chk")
    pogzip = st.file_uploader("Planograms (.zip)", type=["zip"], key="pog_chk")
    acfile = st.file_uploader("A–C file (.xlsx)", type=["xlsx"], key="ac_chk")
    if st.button("Run Checkpoint"):
        if not (master and pogzip and acfile):
            st.warning("Upload all three files.")
        else:
            with st.spinner("Running checkpoint…"):
                files = {
                    "master": (master.name, master.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                    "planograms_zip": (pogzip.name, pogzip.getvalue(), "application/zip"),
                    "ac_file": (acfile.name, acfile.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
                }
                resp = requests.post(API_BASE + "baseline/checkpoint", files=files, headers={"x-api-key": API_KEY})
            if resp.ok:
                st.success("Checkpoint ready.")
                st.download_button("Download checkpoint.xlsx", resp.content, "checkpoint.xlsx")
            else:
                st.error(f"Failed: {resp.status_code} — {resp.text}")

with tabs[1]:
    st.subheader("Finalize: Boost first, then A–C uplift (+20%, skip if boosted)")
    chk = st.file_uploader("Checkpoint workbook (.xlsx)", type=["xlsx"], key="chk_fin")
    if st.button("Apply Boost + Uplift"):
        if not chk:
            st.warning("Upload the checkpoint workbook.")
        else:
            with st.spinner("Finalizing…"):
                files = {"master_checkpoint": (chk.name, chk.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                resp = requests.post(API_BASE + "baseline/finalize", files=files, headers={"x-api-key": API_KEY})
            if resp.ok:
                st.success("Final workbook ready.")
                st.download_button("Download final.xlsx", resp.content, "final.xlsx")
            else:
                st.error(f"Failed: {resp.status_code} — {resp.text}")

with tabs[2]:
    st.subheader("OA_FACINGS — Versioned Source of Truth")
    up = st.file_uploader("OA_FACINGS (.xlsx)", type=["xlsx"], key="oaf_up")
    who = st.text_input("Your name or email (for audit)", value="unknown")
    if st.button("Upload & Activate"):
        if not up:
            st.warning("Upload OA_FACINGS first.")
        else:
            files = {"file": (up.name, up.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            data = {"uploaded_by": (None, who)}
            resp = requests.post(API_BASE + "oafacings/upload", files=files, data=data, headers={"x-api-key": API_KEY})
            if resp.ok:
                st.success(f"Uploaded. {resp.json().get('count',0)} SKUs activated.")
            else:
                st.error(f"Failed: {resp.status_code} — {resp.text}")
    if st.button("Refresh Versions"):
        pass
    resp = requests.get(API_BASE + "oafacings/active", headers={"x-api-key": API_KEY})
    if resp.ok:
        versions = resp.json().get("versions", [])
        if versions:
            st.write("Versions (latest first):")
            for v in versions:
                st.write(f"• #{v['id']} — {v['uploaded_by']} @ {v['uploaded_at']} — {'ACTIVE' if v['is_active'] else ''}")
        else:
            st.info("No versions yet.")
    else:
        st.error("Can't fetch versions list.")
