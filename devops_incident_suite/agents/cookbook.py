"""Cookbook Synthesizer Agent — creates a consolidated remediation runbook."""

from __future__ import annotations

import json
import re

from langchain_core.messages import SystemMessage, HumanMessage


SYSTEM_PROMPT = """\
You are a Cookbook Synthesizer Agent for a DevOps incident analysis pipeline.

You receive a list of detected issues with severity levels and recommended fixes.
Your job is to create a consolidated, actionable remediation cookbook/runbook.

Requirements:
1. Group related issues together.
2. Prioritize by severity (CRITICAL first, then HIGH, MEDIUM, LOW).
3. Format as a step-by-step markdown checklist.
4. Include severity badges, clear action items, and expected outcomes.

Output format — return ONLY markdown (no JSON wrapping), structured like this.
IMPORTANT spacing rules:
- NO blank line between the issue title line and its sub-items (Action, Expected outcome, Related log lines)
- Put a blank line AFTER the last sub-item (Related log lines) BEFORE the next issue title
- Keep each issue block compact with its details

Example:

# Incident Remediation Cookbook

## Priority: CRITICAL
- [ ] **Issue title** — Brief description
  - **Action:** Step-by-step fix
  - **Expected outcome:** What success looks like
  - **Related log lines:** line numbers

- [ ] **Next issue title** — Brief description
  - **Action:** Step-by-step fix
  - **Expected outcome:** What success looks like
  - **Related log lines:** line numbers

## Priority: HIGH
- [ ] **Issue title** — Brief description
  - **Action:** Step-by-step fix
  - **Expected outcome:** What success looks like
  - **Related log lines:** line numbers

## Summary
- Total issues: N
- Critical: N | High: N | Medium: N | Low: N
"""


def run(state: dict, llm) -> dict:
    """Synthesize a remediation cookbook from detected issues."""
    issues = state.get("issues", [])

    if not issues:
        cookbook = (
            "# Incident Remediation Cookbook\n\n"
            "No actionable issues detected. All systems appear healthy."
        )
        return {"cookbook": cookbook, "current_agent": "cookbook"}

    issues_text = json.dumps(issues, indent=2, default=str)

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(
            content=f"Create a remediation cookbook from these issues:\n\n{issues_text}"
        ),
    ])

    cookbook_md = _fix_spacing(response.content.strip())
    return {"cookbook": cookbook_md, "current_agent": "cookbook"}


def _fix_spacing(md: str) -> str:
    """Post-process markdown to fix spacing between issue titles and sub-items.

    Removes blank lines between a checkbox line and its sub-items,
    and ensures a blank line exists after the last sub-item before the next checkbox.
    """
    lines = md.split("\n")
    result = []
    for i, line in enumerate(lines):
        # Skip blank lines that sit between a checkbox title and its sub-item
        if (
            line.strip() == ""
            and i > 0
            and i < len(lines) - 1
            and re.match(r"^\s*- \[[ x]\] ", lines[i - 1])
            and re.match(r"^\s+- \*\*", lines[i + 1])
        ):
            continue
        result.append(line)

    # Ensure blank line between the last sub-item of one block and the next checkbox
    final = []
    for i, line in enumerate(result):
        final.append(line)
        if (
            i < len(result) - 1
            and re.match(r"^\s+- \*\*(Related log lines|Expected outcome)", line)
            and re.match(r"^\s*- \[[ x]\] ", result[i + 1])
        ):
            final.append("")
    return "\n".join(final)
