"""
Streamlit UI for the compliance checker.

This is a thin *client*: it uploads the PDFs to the FastAPI `/check` service and
renders the report. UI and API are separate processes (a microservices split),
so either can be scaled or deployed independently.

Run (with the API already running on :8000):
  streamlit run ui/streamlit_app.py
"""

from __future__ import annotations

import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Trade-Finance Compliance Checker", page_icon="📄", layout="centered"
)

st.title("📄 Trade-Finance Document Compliance Checker")
st.caption(
    "Upload a Letter of Credit, Commercial Invoice and Bill of Lading. "
    "The documents are checked against each other and against UCP 600."
)

uploaded = st.file_uploader(
    "Upload the case PDFs", type=["pdf"], accept_multiple_files=True
)

if st.button("Check compliance", type="primary", disabled=not uploaded):
    files = [("files", (f.name, f.getvalue(), "application/pdf")) for f in uploaded]
    try:
        with st.spinner("Running the pipeline (ingest → extract → compliance)…"):
            resp = requests.post(f"{API_URL}/check", files=files, timeout=600)
    except requests.exceptions.RequestException as e:
        st.error(f"Could not reach the API at {API_URL}. Is it running?\n\n{e}")
        st.stop()

    if resp.status_code != 200:
        st.error(f"API error {resp.status_code}: {resp.text}")
        st.stop()

    data = resp.json()

    if data["is_compliant"]:
        st.success("✅ COMPLIANT — no discrepancies found")
    else:
        st.error(f"❌ {len(data['findings'])} discrepancy(ies) found")

    if data["documents_detected"]:
        st.write("**Documents detected:** " + ", ".join(data["documents_detected"]))

    for i, finding in enumerate(data["findings"], 1):
        with st.expander(f"[{i}] {finding['title']}  ·  {finding['code']}"):
            st.write(finding["detail"])
            st.caption(f"Cited: {finding['ucp_article']} — {finding['ucp_summary']}")

    if data["errors"]:
        st.warning("Extraction issues:\n\n- " + "\n- ".join(data["errors"]))
