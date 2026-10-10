"""Streamlit shell: triage a note, look at store charts, or open the eval stub."""

from __future__ import annotations

import json

import pandas as pd
import plotly.express as px
import streamlit as st

from copilot.config import EVAL_DIR, NOW, PREDICTIONS_PATH
from copilot.data import load_frames
from copilot.graph import run_turn

st.set_page_config(page_title="Retail Operations Copilot", layout="wide")
st.title("Punjab Sports Mart")
st.caption(f"Retail Operations Copilot. Business clock: {NOW:%Y-%m-%d %H:%M:%S} IST. Mode: rules only.")

triage_tab, analytics_tab, eval_tab = st.tabs(["Triage", "Analytics", "Eval"])

with triage_tab:
    prompt = st.text_area("Store issue", height=140, placeholder="Describe the register, stock, return, or safety issue.")
    persona = st.selectbox(
        "Persona",
        ["Cashier", "Store Manager", "Inventory Associate", "Regional Manager", "Customer Service Associate"],
    )
    if st.button("Run copilot", type="primary"):
        if not prompt.strip():
            st.warning("Enter an issue first.")
        else:
            response, steps = run_turn(prompt.strip(), persona=persona)
            st.subheader("Response")
            st.json(json.loads(response.model_dump_json()))
            st.subheader("Citations")
            for citation in response.citations:
                st.code(citation, language=None)
            if response.follow_up_question:
                st.info(response.follow_up_question)
            triage_step = next((step.get("output") or {} for step in steps if step.get("agent") == "triage"), {})
            st.write("Decision source:", triage_step.get("decision_source") or "")
            neighbours = triage_step.get("neighbours") or []
            if neighbours:
                st.write("Similar past cases")
                for item in neighbours[:3]:
                    st.write(
                        f"{item.get('case_id')} ({item.get('similarity')}) "
                        f"{item.get('category')} {item.get('priority')}: {item.get('text')}"
                    )
            st.subheader("Agent trace")
            st.dataframe(
                [
                    {
                        "agent": step.get("agent"),
                        "mode": step.get("mode"),
                        "latency_ms": step.get("latency_ms"),
                        "output": json.dumps(step.get("output"), ensure_ascii=True),
                    }
                    for step in steps
                ],
                width="stretch",
            )
            st.caption("The same steps are appended to logs/trace.jsonl.")

with analytics_tab:
    frames = load_frames()
    cases = frames["support_cases"]
    cases = cases[cases["created_ts"] <= NOW].copy()
    open_cases = cases[cases["status"].str.lower() != "closed"]
    stores = frames["store_master"][["store_id", "region"]]
    regional = open_cases.merge(stores, on="store_id", how="left")
    left, middle, right = st.columns(3)
    left.metric("Open cases", int(len(open_cases)))
    middle.metric("Open P1", int((open_cases["priority_label"] == "P1").sum()))
    right.metric("Open P2", int((open_cases["priority_label"] == "P2").sum()))
    priority_counts = open_cases["priority_label"].value_counts().rename_axis("priority").reset_index(name="cases")
    category_counts = open_cases["category_label"].value_counts().rename_axis("category").reset_index(name="cases")
    region_counts = regional["region"].fillna("Unknown").value_counts().rename_axis("region").reset_index(name="cases")
    st.plotly_chart(px.bar(priority_counts, x="priority", y="cases", title="Open cases by priority"), width="stretch")
    st.plotly_chart(px.bar(category_counts, x="category", y="cases", title="Open cases by category"), width="stretch")
    st.plotly_chart(px.bar(region_counts, x="region", y="cases", title="Open cases by region"), width="stretch")
    window_start = NOW - pd.Timedelta(days=30)
    recent = cases[cases["created_ts"] >= window_start].copy()
    recent["day"] = recent["created_ts"].dt.date.astype(str)
    daily = recent.groupby("day").size().rename("cases").reset_index()
    st.plotly_chart(px.line(daily, x="day", y="cases", title="Case volume, last 30 days"), width="stretch")
    st.caption("Employee names from employee_master.csv are loaded with the other files and are not shown.")

with eval_tab:
    report_path = EVAL_DIR / "results" / "report.md"
    if report_path.exists():
        st.markdown(report_path.read_text(encoding="utf-8"))
    else:
        st.info("Run `make eval` to write evaluation/results/report.md.")
    if PREDICTIONS_PATH.exists():
        with st.expander("Public predictions.csv"):
            st.dataframe(pd.read_csv(PREDICTIONS_PATH), width="stretch")
