"""Log Reader/Classifier Agent — parses raw logs into structured LogEntry records."""

from __future__ import annotations

import json
import re

from langchain_core.messages import SystemMessage, HumanMessage

from models.schemas import LogEntry, LogLevel, PipelineState


SYSTEM_PROMPT = """\
You are a Log Classifier Agent for a DevOps incident analysis pipeline.

Your job:
1. Parse each raw log line into structured fields: timestamp, level, service, message.
2. Classify the log level (CRITICAL, ERROR, WARN/WARNING, INFO, DEBUG).
3. Extract the service/component name when present.

Return your output as a JSON array of objects with these exact keys:
  line_number, timestamp, level, service, message

Rules:
- Use uppercase log levels: CRITICAL, ERROR, WARN, INFO, DEBUG, UNKNOWN.
- If a field is missing, use empty string for timestamp, "unknown" for service.
- Preserve the original message text.
- Do NOT wrap the JSON in markdown code fences. Return ONLY valid JSON.
"""

# Common log patterns for fast regex-based parsing before LLM fallback
LOG_PATTERNS = [
    # Standard syslog / app format: 2024-01-15 10:23:45 ERROR [auth-service] Message
    re.compile(
        r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}[.\d]*\s*[A-Z]*)\s+"
        r"(?P<level>CRITICAL|ERROR|WARN(?:ING)?|INFO|DEBUG)\s+"
        r"(?:\[(?P<service>[^\]]+)\]\s*)?"
        r"(?P<message>.+)$",
        re.IGNORECASE,
    ),
    # Apache / nginx style: [Tue Jan 15 10:23:45 2024] [error] [client 1.2.3.4] msg
    re.compile(
        r"^\[(?P<timestamp>[^\]]+)\]\s+"
        r"\[(?P<level>\w+)\]\s+"
        r"(?:\[(?P<service>[^\]]*)\]\s*)?"
        r"(?P<message>.+)$",
        re.IGNORECASE,
    ),
]

LEVEL_MAP = {
    "critical": LogLevel.CRITICAL,
    "error": LogLevel.ERROR,
    "err": LogLevel.ERROR,
    "warn": LogLevel.WARN,
    "warning": LogLevel.WARNING,
    "info": LogLevel.INFO,
    "debug": LogLevel.DEBUG,
}


def _parse_level(raw: str) -> LogLevel:
    return LEVEL_MAP.get(raw.strip().lower(), LogLevel.UNKNOWN)


def _try_regex_parse(lines: list[str]) -> list[LogEntry] | None:
    """Try to parse all lines with regex. Returns None if any line fails."""
    entries = []
    for i, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        matched = False
        for pattern in LOG_PATTERNS:
            m = pattern.match(line)
            if m:
                entries.append(
                    LogEntry(
                        line_number=i,
                        timestamp=m.group("timestamp").strip(),
                        level=_parse_level(m.group("level")),
                        service=m.group("service") or "unknown",
                        message=m.group("message").strip(),
                        raw=line,
                    )
                )
                matched = True
                break
        if not matched:
            return None  # Fall back to LLM
    return entries


def _parse_llm_response(response_text: str, raw_lines: list[str]) -> list[LogEntry]:
    """Parse the LLM JSON response into LogEntry objects."""
    # Strip markdown code fences if present
    text = response_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    parsed = json.loads(text)
    entries = []
    for item in parsed:
        line_num = item.get("line_number", 0)
        raw = ""
        if 1 <= line_num <= len(raw_lines):
            raw = raw_lines[line_num - 1].strip()
        entries.append(
            LogEntry(
                line_number=line_num,
                timestamp=item.get("timestamp", ""),
                level=_parse_level(item.get("level", "UNKNOWN")),
                service=item.get("service", "unknown"),
                message=item.get("message", ""),
                raw=raw or item.get("message", ""),
            )
        )
    return entries


def run(state: dict, llm) -> dict:
    """Classify raw logs into structured entries."""
    raw_logs: str = state["raw_logs"]
    lines = raw_logs.splitlines()
    non_empty = [l for l in lines if l.strip()]

    if not non_empty:
        return {"log_entries": [], "current_agent": "log_classifier"}

    # Try fast regex parsing first
    entries = _try_regex_parse(non_empty)
    if entries is not None:
        return {"log_entries": [e.model_dump() for e in entries], "current_agent": "log_classifier"}

    # Fall back to LLM for non-standard formats
    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Parse these log lines:\n\n{raw_logs}"),
    ])
    entries = _parse_llm_response(response.content, lines)
    return {"log_entries": [e.model_dump() for e in entries], "current_agent": "log_classifier"}
