# DevOps Incident Analysis Suite

A multi-agent pipeline that analyzes server/ops log files using LangGraph orchestration and LLM-powered agents.

## Architecture

```
Upload → Log Classifier → Remediation → ┬─ Cookbook Synthesizer
                                         ├─ JIRA Ticket Agent
                                         └─ Notification Agent
```

**Agents:**

| Agent | Role |
|---|---|
| Log Reader/Classifier | Parses raw logs into structured entries with level, service, timestamp |
| Remediation | Analyzes errors/warnings and recommends fixes with severity |
| Cookbook Synthesizer | Creates a prioritized remediation runbook |
| JIRA Ticket Agent | Generates ticket payloads for CRITICAL/HIGH issues (mock API) |
| Notification Agent | Formats and sends Slack alerts (live or dry-run) |

## Setup

```bash
cd devops_incident_suite
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
```

## Run

```bash
streamlit run app.py
```

## Configuration

Set `LLM_PROVIDER` in `.env` to one of:
- `openrouter` (default) — uses `OPENROUTER_API_KEY`
- `openai` — uses `OPENAI_API_KEY`
- `anthropic` — uses `ANTHROPIC_API_KEY`

For Slack notifications, set `SLACK_WEBHOOK_URL`. Leave it empty for dry-run mode.

## Project Structure

```
devops_incident_suite/
├── app.py                  # Streamlit frontend
├── graph.py                # LangGraph orchestrator
├── agents/
│   ├── log_classifier.py   # Parses and classifies log entries
│   ├── remediation.py      # Recommends fixes for issues
│   ├── cookbook.py          # Generates remediation runbook
│   ├── jira_ticket.py      # Creates JIRA ticket payloads
│   └── notification.py     # Formats Slack notifications
├── models/
│   └── schemas.py          # Pydantic models for pipeline state
├── utils/
│   └── slack_client.py     # Slack webhook helper
├── sample_logs/
│   └── sample.log          # Example log file for testing
├── requirements.txt
└── .env.example
```
