"""Streamlit frontend for the DevOps Incident Analysis Suite."""

from __future__ import annotations

import sys
import os
import json
import time

import streamlit as st

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from graph import run_pipeline
from models.schemas import Severity


# --- Page Config ---

st.set_page_config(
    page_title="DevOps Incident Analysis Suite",
    page_icon="🔍",
    layout="wide",
)

st.title("DevOps Incident Analysis Suite")
st.caption("Upload server/ops logs and let AI agents analyze, triage, and recommend fixes.")


# --- Sidebar: Config ---

with st.sidebar:
    st.header("Configuration")

    provider = st.selectbox(
        "LLM Provider",
        ["openrouter", "openai", "anthropic"],
        index=0,
    )
    os.environ["LLM_PROVIDER"] = provider

    if provider == "openrouter":
        model = st.text_input("Model", value=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"))
        os.environ["OPENROUTER_MODEL"] = model
    elif provider == "openai":
        model = st.text_input("Model", value=os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
        os.environ["OPENAI_MODEL"] = model
    elif provider == "anthropic":
        model = st.text_input("Model", value=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"))
        os.environ["ANTHROPIC_MODEL"] = model

    st.divider()

    slack_mode = st.radio(
        "Slack Notifications",
        ["Dry Run (mock)", "Live (send via webhook)"],
        index=0,
    )
    if slack_mode.startswith("Live"):
        webhook = st.text_input("Slack Webhook URL", type="password")
        if webhook:
            os.environ["SLACK_WEBHOOK_URL"] = webhook
    else:
        os.environ.pop("SLACK_WEBHOOK_URL", None)

    st.divider()

    # Load sample log
    sample_dir = os.path.join(os.path.dirname(__file__), "sample_logs")
    sample_files = sorted(f for f in os.listdir(sample_dir) if f.endswith(".log"))
    selected_sample = st.selectbox("Sample Logs", sample_files)
    if st.button("Load Sample Log"):
        with open(os.path.join(sample_dir, selected_sample)) as f:
            st.session_state["sample_content"] = f.read()
            st.session_state["sample_name"] = selected_sample


# --- File Upload ---

uploaded_file = st.file_uploader(
    "Upload a log file",
    type=["log", "txt", "csv", "json"],
    help="Supported formats: plain text logs, CSV, JSON",
)

# Determine which content to analyze
raw_logs = None
file_name = None

if uploaded_file is not None:
    raw_logs = uploaded_file.read().decode("utf-8", errors="replace")
    file_name = uploaded_file.name
elif "sample_content" in st.session_state:
    raw_logs = st.session_state["sample_content"]
    file_name = st.session_state.get("sample_name", "sample.log")
    st.info(f"Using sample log: {file_name}")


# --- Analysis ---

if raw_logs and st.button("Analyze Logs", type="primary"):
    # Show raw log preview
    with st.expander("Raw Log Preview", expanded=False):
        st.code(raw_logs[:3000] + ("..." if len(raw_logs) > 3000 else ""), language="log")

    # Run the pipeline with progress
    progress = st.progress(0, text="Starting analysis pipeline...")
    status_container = st.empty()

    start_time = time.time()

    progress.progress(10, text="Running Log Classifier Agent...")
    status_container.info("Agent 1/5: Log Reader/Classifier is parsing your logs...")

    try:
        result = run_pipeline(raw_logs, file_name)
    except Exception as e:
        st.error(f"Pipeline error: {e}")
        st.stop()

    elapsed = time.time() - start_time
    progress.progress(100, text="Analysis complete!")
    status_container.success(f"All agents completed in {elapsed:.1f}s")

    # Store results
    st.session_state["result"] = result

# --- Display Results ---

if "result" in st.session_state:
    result = st.session_state["result"]

    # Summary metrics
    log_entries = result.get("log_entries", [])
    issues = result.get("issues", [])
    jira_tickets = result.get("jira_tickets", [])
    notification = result.get("notification")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Log Entries Parsed", len(log_entries))
    col2.metric("Issues Detected", len(issues))
    col3.metric("JIRA Tickets", len(jira_tickets))
    notify_status = "Sent" if notification and notification.get("sent") else "Dry Run"
    col4.metric("Notification", notify_status)

    st.divider()

    # Tabbed output
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Log Entries",
        "Issues & Remediation",
        "Remediation Cookbook",
        "JIRA Tickets",
        "Slack Notification",
    ])

    # Tab 1: Log Entries
    with tab1:
        st.subheader("Parsed Log Entries")
        if log_entries:
            severity_filter = st.multiselect(
                "Filter by level",
                ["CRITICAL", "ERROR", "WARN", "WARNING", "INFO", "DEBUG"],
                default=["CRITICAL", "ERROR", "WARN", "WARNING"],
            )
            filtered = [e for e in log_entries if e.get("level") in severity_filter]
            for entry in filtered:
                level = entry.get("level", "UNKNOWN")
                color = {
                    "CRITICAL": "red", "ERROR": "red",
                    "WARN": "orange", "WARNING": "orange",
                    "INFO": "blue", "DEBUG": "gray",
                }.get(level, "gray")
                st.markdown(
                    f"**:{color}[{level}]** `{entry.get('timestamp', '')}` "
                    f"**[{entry.get('service', '')}]** {entry.get('message', '')}"
                )
        else:
            st.info("No log entries parsed.")

    # Tab 2: Issues & Remediation
    with tab2:
        st.subheader("Detected Issues")
        if issues:
            for i, issue in enumerate(issues, 1):
                sev = issue.get("severity", "MEDIUM")
                icon = {"CRITICAL": "🔴", "HIGH": "🟠", "MEDIUM": "🟡", "LOW": "🟢"}.get(sev, "⚪")
                with st.expander(f"{icon} [{sev}] {issue.get('issue', 'Unknown')}", expanded=(sev in ("CRITICAL", "HIGH"))):
                    st.markdown(f"**Recommended Fix:** {issue.get('recommended_fix', 'N/A')}")
                    st.markdown(f"**Rationale:** {issue.get('rationale', 'N/A')}")
                    if issue.get("source_entries"):
                        st.caption(f"Related log lines: {issue['source_entries']}")
        else:
            st.success("No actionable issues detected.")

    # Tab 3: Cookbook
    with tab3:
        st.subheader("Remediation Cookbook")
        cookbook = result.get("cookbook", "")
        if cookbook:
            st.markdown(cookbook)
        else:
            st.info("No cookbook generated.")

    # Tab 4: JIRA Tickets
    with tab4:
        st.subheader("Generated JIRA Tickets")
        if jira_tickets:
            for i, ticket in enumerate(jira_tickets, 1):
                with st.expander(f"Ticket {i}: {ticket.get('summary', 'Untitled')}", expanded=True):
                    st.markdown(f"**Priority:** {ticket.get('priority', 'N/A')}")
                    st.markdown(f"**Labels:** {', '.join(ticket.get('labels', []))}")
                    st.markdown(f"**Description:**\n\n{ticket.get('description', 'N/A')}")
                    if ticket.get("steps_to_reproduce"):
                        st.markdown(f"**Steps to Reproduce:**\n\n{ticket['steps_to_reproduce']}")
                    st.caption(f"Status: {ticket.get('status', 'CREATED (mock)')}")

                    # Show raw JSON payload
                    with st.expander("Raw JSON Payload"):
                        st.json(ticket)
        else:
            st.info("No tickets generated (only CRITICAL/HIGH issues produce tickets).")

    # Tab 5: Notification
    with tab5:
        st.subheader("Slack Notification")
        if notification:
            mode = notification.get("mode", "dry-run")
            sent = notification.get("sent", False)

            if sent:
                st.success(f"Message sent to {notification.get('channel', '#devops-alerts')} (mode: {mode})")
            else:
                st.warning(f"Dry run mode — message not sent (mode: {mode})")

            st.markdown("**Message Preview:**")
            st.markdown(notification.get("summary", "No summary"))

            with st.expander("Full Slack Payload"):
                st.json(notification.get("payload", {}))
        else:
            st.info("No notification generated.")

    # Error display
    if result.get("error"):
        st.error(f"Pipeline error: {result['error']}")
