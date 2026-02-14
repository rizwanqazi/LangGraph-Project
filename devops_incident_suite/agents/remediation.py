"""Remediation Agent — analyzes classified log entries and recommends fixes."""

from __future__ import annotations

import json
import re

from langchain_core.messages import SystemMessage, HumanMessage

from models.schemas import LogEntry, Severity


SYSTEM_PROMPT = """\
You are a Remediation Agent for a DevOps incident analysis pipeline.

You receive a list of classified log entries (especially ERRORs, WARNINGs, and CRITICALs).
For each detected issue, you must:
1. Identify the issue from the log context.
2. Assign a severity: CRITICAL, HIGH, MEDIUM, or LOW.
3. Recommend an actionable fix.
4. Provide a brief rationale explaining why this fix is appropriate.

Severity guidelines:
- CRITICAL: System down, data loss, security breach (e.g., OOM killer, disk full, auth bypass)
- HIGH: Service degradation, repeated failures (e.g., connection timeouts, repeated auth failures)
- MEDIUM: Warnings that may escalate (e.g., disk space warnings, deprecated API usage)
- LOW: Informational issues (e.g., slow queries, minor config warnings)

Group related log entries into a single issue when they share the same root cause.

Return your output as a JSON array of objects with these exact keys:
  issue, severity, recommended_fix, rationale, source_entries

where source_entries is a list of line_number integers from the input entries.
Do NOT wrap the JSON in markdown code fences. Return ONLY valid JSON.
"""


def run(state: dict, llm) -> dict:
    """Analyze log entries and produce remediation recommendations."""
    log_entries = state.get("log_entries", [])

    # Filter to only actionable entries
    actionable_levels = {"CRITICAL", "ERROR", "WARN", "WARNING"}
    actionable = [e for e in log_entries if e.get("level", "") in actionable_levels]

    if not actionable:
        return {"issues": [], "current_agent": "remediation"}

    entries_text = json.dumps(actionable, indent=2, default=str)

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"Analyze these log entries and recommend fixes:\n\n{entries_text}"
        ),
    ])

    # Parse LLM response
    text = response.content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {
            "issues": [],
            "error": f"Remediation agent returned invalid JSON: {text[:200]}",
            "current_agent": "remediation",
        }

    issues = []
    for item in parsed:
        severity_raw = item.get("severity", "MEDIUM").upper()
        severity = severity_raw if severity_raw in {s.value for s in Severity} else "MEDIUM"
        issues.append({
            "issue": item.get("issue", ""),
            "severity": severity,
            "recommended_fix": item.get("recommended_fix", ""),
            "rationale": item.get("rationale", ""),
            "source_entries": item.get("source_entries", []),
        })

    return {"issues": issues, "current_agent": "remediation"}
