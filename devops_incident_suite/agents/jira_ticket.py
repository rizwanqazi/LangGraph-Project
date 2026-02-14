"""JIRA Ticket Agent — generates structured JIRA ticket payloads for critical issues."""

from __future__ import annotations

import json
import re

from langchain_core.messages import SystemMessage, HumanMessage

from models.schemas import TicketPriority


SYSTEM_PROMPT = """\
You are a JIRA Ticket Agent for a DevOps incident analysis pipeline.

You receive issues with severity CRITICAL or HIGH. For each one, generate a
structured JIRA ticket payload with:
- summary: A concise ticket title (max 100 chars)
- description: Detailed description with no blank lines between heading and its content. Use compact formatting: issue, impact, and recommended fix grouped tightly together with blank lines only between sections
- priority: "Highest" for CRITICAL, "High" for HIGH severity
- labels: Relevant labels like ["incident", "auto-detected", service-name]
- steps_to_reproduce: How to observe the issue from the logs

Return a JSON array of ticket objects with keys:
  summary, description, priority, labels, steps_to_reproduce

Do NOT wrap the JSON in markdown code fences. Return ONLY valid JSON.
"""


def run(state: dict, llm) -> dict:
    """Generate JIRA ticket payloads for CRITICAL and HIGH severity issues."""
    issues = state.get("issues", [])

    # Filter to CRITICAL and HIGH only
    ticketable = [i for i in issues if i.get("severity") in ("CRITICAL", "HIGH")]

    if not ticketable:
        return {"jira_tickets": [], "current_agent": "jira_ticket"}

    issues_text = json.dumps(ticketable, indent=2, default=str)

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"Generate JIRA tickets for these issues:\n\n{issues_text}"
        ),
    ])

    text = response.content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {
            "jira_tickets": [],
            "error": f"JIRA agent returned invalid JSON: {text[:200]}",
            "current_agent": "jira_ticket",
        }

    tickets = []
    for item in parsed:
        priority = item.get("priority", "High")
        if priority not in {p.value for p in TicketPriority}:
            priority = "High"
        tickets.append({
            "summary": item.get("summary", ""),
            "description": item.get("description", ""),
            "priority": priority,
            "labels": item.get("labels", ["incident", "auto-detected"]),
            "steps_to_reproduce": item.get("steps_to_reproduce", ""),
            "status": "CREATED (mock)",
        })

    return {"jira_tickets": tickets, "current_agent": "jira_ticket"}
