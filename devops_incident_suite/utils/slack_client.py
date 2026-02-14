"""Slack webhook helper — supports live and dry-run modes."""

from __future__ import annotations

import os

import requests


def send_slack_message(payload: dict) -> tuple[bool, str]:
    """Send a Slack message via webhook.

    Returns:
        (sent: bool, mode: str) — whether the message was sent and which mode was used.
    """
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")

    if not webhook_url:
        return False, "dry-run"

    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        return True, "live"
    except Exception:
        return False, "dry-run (send failed)"
