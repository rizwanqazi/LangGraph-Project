# PRD: Multi-Agent DevOps Incident Analysis Suite

## 1. Introduction/Overview

The DevOps Incident Analysis Suite is a training/demo application that showcases how multiple AI agents can collaborate through a LangGraph-orchestrated pipeline to analyze server and operations log files. Users upload log files through a Streamlit web interface, and the system automatically parses, classifies, triages, and generates actionable outputs — including remediation recommendations, a prioritized runbook, mock JIRA tickets, and real Slack notifications.

**Problem it solves:** Manually reviewing large log files during incidents is slow, error-prone, and requires deep expertise. This project demonstrates how a multi-agent architecture can automate that workflow end-to-end, producing structured outputs ready to plug into real DevOps toolchains.

## 2. Goals

1. Demonstrate a working multi-agent LangGraph pipeline with 5 specialized agents running in a directed graph (sequential + parallel fan-out).
2. Produce structured, actionable output from each agent that could integrate with real tools (JIRA, Slack, runbook systems).
3. Support real Slack webhook notifications and mock JIRA ticket creation.
4. Accept plain text (.log, .txt), CSV, and JSON log file formats.
5. Make the LLM provider configurable (OpenRouter, OpenAI, Anthropic) via environment variables and UI.
6. Serve as a reference implementation for LangGraph multi-agent patterns with Pydantic-validated state.

## 3. User Stories

- **As a DevOps engineer**, I want to upload a log file and get an instant breakdown of all errors, warnings, and critical issues so I don't have to read thousands of lines manually.
- **As an SRE team lead**, I want a prioritized remediation cookbook generated from the log analysis so my team knows what to fix first during an incident.
- **As an on-call engineer**, I want JIRA ticket payloads auto-generated for critical issues so I can create tickets quickly without writing descriptions from scratch.
- **As a team**, I want a Slack notification sent to our channel summarizing the top issues so the whole team is aware without checking the dashboard.
- **As a developer learning LangGraph**, I want to see a clear example of multi-agent orchestration with parallel fan-out, typed state, and reducers so I can apply the pattern to my own projects.

## 4. Functional Requirements

### 4.1 File Upload & Input
1. The system must accept file uploads in .log, .txt, .csv, and .json formats via the Streamlit UI.
2. The system must provide a sidebar dropdown to select and load any of the bundled sample log files for quick testing.
3. The system must display a collapsible raw log preview after upload.

### 4.2 Log Reader/Classifier Agent
4. The agent must parse raw log lines into structured records with fields: line_number, timestamp, level, service, message, raw.
5. The agent must classify each entry into log levels: CRITICAL, ERROR, WARN, WARNING, INFO, DEBUG, or UNKNOWN.
6. The agent must attempt fast regex-based parsing first, falling back to the LLM only for non-standard formats.

### 4.3 Remediation Agent
7. The agent must analyze all ERROR, WARN, WARNING, and CRITICAL log entries.
8. The agent must produce a list of issues, each with: issue description, severity (CRITICAL/HIGH/MEDIUM/LOW), recommended fix, rationale, and source log line numbers.
9. The agent must group related log entries into a single issue when they share a root cause.

### 4.4 Cookbook Synthesizer Agent
10. The agent must generate a markdown-formatted remediation runbook from the issue list.
11. The runbook must be organized by severity (CRITICAL first, then HIGH, MEDIUM, LOW).
12. Each issue block must include a checkbox title, action steps, expected outcome, and related log lines — with no blank line between the title and its sub-items.

### 4.5 JIRA Ticket Agent
13. The agent must generate structured JIRA ticket payloads only for CRITICAL and HIGH severity issues.
14. Each ticket payload must include: summary, description, priority, labels, and steps_to_reproduce.
15. The agent must simulate ticket creation (mock) with a status field, structured for real JIRA API integration.

### 4.6 Notification Agent
16. The agent must format a Slack-compatible summary message with the top issues (max 5).
17. The agent must send the notification via Slack Incoming Webhook when a URL is configured.
18. The agent must support a dry-run mode (no webhook configured) that displays the payload in the UI without sending.

### 4.7 LangGraph Orchestrator
19. The pipeline must run agents in this order: Log Classifier -> Remediation -> [Cookbook, JIRA, Notification] in parallel.
20. The orchestrator must use a TypedDict state with Annotated reducers to handle concurrent writes from parallel agents.
21. The orchestrator must support configurable LLM providers (OpenRouter, OpenAI, Anthropic) via environment variable.

### 4.8 Streamlit Dashboard
22. The UI must display summary metrics: log entries parsed, issues detected, JIRA tickets created, notification status.
23. The UI must provide 5 tabs: Log Entries, Issues & Remediation, Remediation Cookbook, JIRA Tickets, Slack Notification.
24. The Log Entries tab must support filtering by log level via multiselect.
25. The Issues tab must show expandable sections per issue, auto-expanded for CRITICAL/HIGH severity.
26. The JIRA Tickets tab must display both formatted content and raw JSON payload.
27. The sidebar must allow selecting the LLM provider, model, and Slack notification mode.

### 4.9 Data Validation
28. All data flowing between agents must be validated using Pydantic models (LogEntry, Issue, JiraTicket, SlackNotification).

## 5. Non-Goals (Out of Scope)

- **Real JIRA API integration** — tickets are mock/simulated only, not created in an actual JIRA instance.
- **User authentication** — no login or access control on the Streamlit app.
- **Log streaming / real-time monitoring** — this is batch analysis of uploaded files only.
- **Binary log formats** — Windows Event Log, systemd journal, and other binary formats are not supported.
- **Persistent storage** — analysis results are not saved to a database; they exist only in the session.
- **Multi-file analysis** — each analysis run processes a single uploaded file.
- **Custom agent configuration** — agent system prompts and behavior are not user-configurable via the UI.

## 6. Design Considerations

### UI Layout
- **Sidebar:** LLM provider selector, model input, Slack mode toggle, sample log dropdown + load button.
- **Main area:** File uploader, Analyze button, progress bar, summary metrics row, 5-tab output display.
- Color-coded log levels: red for CRITICAL/ERROR, orange for WARN, blue for INFO, gray for DEBUG.
- Severity icons in Issues tab: red circle (CRITICAL), orange circle (HIGH), yellow circle (MEDIUM), green circle (LOW).

### Architecture Diagram
```
Upload -> Log Classifier -> Remediation -> +-- Cookbook Synthesizer
                                           +-- JIRA Ticket Agent
                                           +-- Notification Agent
```

## 7. Technical Considerations

- **Python 3.11+** required.
- **LangGraph** for agent orchestration with `StateGraph`, `Annotated` reducers for parallel fan-out.
- **LangChain + ChatOpenAI** for LLM calls (OpenRouter-compatible via base_url override).
- **Pydantic v2** for schema validation between agents.
- **python-dotenv** for environment configuration.
- **Regex-first parsing** in the Log Classifier to minimize unnecessary LLM API calls.
- **Post-processing** in the Cookbook agent to fix markdown spacing deterministically (not relying on LLM formatting).
- The `.env` file at the project root is shared across all modules via `load_dotenv()`.

### Project Structure
```
devops_incident_suite/
├── app.py                  # Streamlit frontend
├── graph.py                # LangGraph orchestrator
├── agents/
│   ├── log_classifier.py   # Regex + LLM log parser
│   ├── remediation.py      # Issue detection and fix recommendations
│   ├── cookbook.py          # Prioritized runbook generator
│   ├── jira_ticket.py      # Mock JIRA ticket creator
│   └── notification.py     # Slack notification sender
├── models/
│   └── schemas.py          # Pydantic models for pipeline state
├── utils/
│   └── slack_client.py     # Slack webhook helper
├── sample_logs/            # 5 sample log files for testing
├── requirements.txt
└── .env.example
```

## 8. Success Metrics

1. **Pipeline completes end-to-end** for all 5 sample log files without errors.
2. **Log Classifier** correctly identifies and categorizes all CRITICAL, ERROR, and WARN entries from sample logs.
3. **Remediation Agent** groups related issues (e.g., multiple connection timeout lines = one issue) and assigns appropriate severity.
4. **Cookbook** output is a well-formatted, prioritized markdown checklist with correct spacing.
5. **JIRA tickets** are generated only for CRITICAL/HIGH issues with valid structured payloads.
6. **Slack notification** sends successfully to the configured webhook in live mode.
7. **All agent outputs** are structured via Pydantic models and could be consumed by downstream real tools.

## 9. Open Questions

1. Should v2 add real JIRA API integration (requires JIRA Cloud API token and project configuration)?
2. Should the app support comparing analysis results across multiple log files?
3. Would it be valuable to add an "Export Report" feature (PDF/HTML) for the combined analysis?
4. Should the Notification Agent support additional channels beyond Slack (e.g., Microsoft Teams, PagerDuty)?
5. Is there a need for custom severity mapping rules configurable per organization?
