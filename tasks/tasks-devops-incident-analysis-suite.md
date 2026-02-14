# Tasks: Multi-Agent DevOps Incident Analysis Suite

## Relevant Files

- `devops_incident_suite/models/__init__.py` - Package init for models
- `devops_incident_suite/models/schemas.py` - Pydantic models for pipeline state (LogEntry, Issue, JiraTicket, SlackNotification, PipelineState)
- `devops_incident_suite/agents/__init__.py` - Package init for agents
- `devops_incident_suite/agents/log_classifier.py` - Log Reader/Classifier agent with regex + LLM fallback
- `devops_incident_suite/agents/remediation.py` - Remediation agent for issue detection and fix recommendations
- `devops_incident_suite/agents/cookbook.py` - Cookbook Synthesizer agent for runbook generation with markdown post-processing
- `devops_incident_suite/agents/jira_ticket.py` - JIRA Ticket agent for mock ticket creation
- `devops_incident_suite/agents/notification.py` - Notification agent for Slack alerts (live + dry-run)
- `devops_incident_suite/utils/__init__.py` - Package init for utils
- `devops_incident_suite/utils/slack_client.py` - Slack webhook helper with live/dry-run modes
- `devops_incident_suite/graph.py` - LangGraph orchestrator with PipelineState TypedDict and parallel fan-out
- `devops_incident_suite/app.py` - Streamlit frontend with tabs, metrics, sidebar config
- `devops_incident_suite/sample_logs/microservices_mixed.log` - Sample: mixed microservices incidents
- `devops_incident_suite/sample_logs/kubernetes_cluster.log` - Sample: Kubernetes cluster instability
- `devops_incident_suite/sample_logs/database_outage.log` - Sample: PostgreSQL outage cascade
- `devops_incident_suite/sample_logs/security_incident.log` - Sample: Security breach scenario
- `devops_incident_suite/sample_logs/ci_cd_pipeline.log` - Sample: CI/CD pipeline failures
- `devops_incident_suite/requirements.txt` - Python dependencies for the suite
- `devops_incident_suite/.env.example` - Environment variable template
- `.env` - Actual environment config (API keys, Slack webhook, LLM provider)
- `tasks/prd-devops-incident-analysis-suite.md` - Product Requirements Document

### Notes

- Run the app with: `cd devops_incident_suite && streamlit run app.py`
- The `.env` file lives at the project root (`LangGraph_Project/.env`), not inside `devops_incident_suite/`
- LLM calls go through OpenRouter by default using `OPENROUTER_API_KEY`
- Slack webhook sends to `#all-langgraphprojectfeb2026` channel

## Instructions for Completing Tasks

**IMPORTANT:** Check off each task by changing `- [ ]` to `- [x]` after completing.

## Tasks

- [x] 0.0 Create project directory structure
  - [x] 0.1 Create `devops_incident_suite/` root directory
  - [x] 0.2 Create `agents/`, `models/`, `utils/`, `sample_logs/` subdirectories
  - [x] 0.3 Create `__init__.py` files for `agents/`, `models/`, `utils/` packages

- [x] 1.0 Define Pydantic schemas and pipeline state models
  - [x] 1.1 Create `LogLevel` and `Severity` enums for log classification and issue severity
  - [x] 1.2 Create `TicketPriority` enum for JIRA ticket priorities
  - [x] 1.3 Define `LogEntry` model with fields: line_number, timestamp, level, service, message, raw
  - [x] 1.4 Define `Issue` model with fields: issue, severity, recommended_fix, rationale, source_entries
  - [x] 1.5 Define `JiraTicket` model with fields: summary, description, priority, labels, steps_to_reproduce, status
  - [x] 1.6 Define `SlackNotification` model with fields: channel, summary, payload, sent, mode
  - [x] 1.7 Define `PipelineState` model with all fields needed across the pipeline

- [x] 2.0 Build the Log Reader/Classifier Agent
  - [x] 2.1 Write `SYSTEM_PROMPT` defining the agent's role and expected JSON output format
  - [x] 2.2 Implement regex patterns for common log formats (syslog-style, Apache/nginx-style)
  - [x] 2.3 Create `_parse_level()` helper to map raw level strings to `LogLevel` enum
  - [x] 2.4 Implement `_try_regex_parse()` for fast regex-based parsing (returns None on any miss)
  - [x] 2.5 Implement `_parse_llm_response()` to handle LLM JSON output (strip code fences, parse, validate)
  - [x] 2.6 Implement `run()` function: try regex first, fall back to LLM, return structured log entries

- [x] 3.0 Build the Remediation Agent
  - [x] 3.1 Write `SYSTEM_PROMPT` with severity guidelines (CRITICAL/HIGH/MEDIUM/LOW criteria)
  - [x] 3.2 Implement `run()` function: filter to actionable entries (ERROR/WARN/CRITICAL), send to LLM
  - [x] 3.3 Parse LLM JSON response and validate severity values against the Severity enum
  - [x] 3.4 Return structured issue list with source_entries linking back to log line numbers

- [x] 4.0 Build the Cookbook Synthesizer Agent
  - [x] 4.1 Write `SYSTEM_PROMPT` with explicit markdown format and spacing rules
  - [x] 4.2 Implement `run()` function: send issues to LLM, get markdown cookbook
  - [x] 4.3 Implement `_fix_spacing()` post-processor to deterministically fix blank lines between checkbox titles and sub-items
  - [x] 4.4 Ensure blank line separation between issue blocks, not within them

- [x] 5.0 Build the JIRA Ticket Agent
  - [x] 5.1 Write `SYSTEM_PROMPT` specifying JSON output with summary, description, priority, labels, steps_to_reproduce
  - [x] 5.2 Implement `run()` function: filter to CRITICAL/HIGH issues only, send to LLM
  - [x] 5.3 Parse LLM JSON response, validate priority against `TicketPriority` enum
  - [x] 5.4 Add mock `status: "CREATED (mock)"` to each ticket payload

- [x] 6.0 Build the Notification Agent and Slack client
  - [x] 6.1 Create `utils/slack_client.py` with `send_slack_message()` — check for webhook URL, POST to Slack, return (sent, mode)
  - [x] 6.2 Write notification `SYSTEM_PROMPT` for concise Slack-formatted summaries
  - [x] 6.3 Implement `_get_channel()` to read channel from `SLACK_CHANNEL` env var
  - [x] 6.4 Implement `run()` function: generate Slack message via LLM, build payload with blocks, call `send_slack_message()`
  - [x] 6.5 Return notification dict with channel, summary, payload, sent status, and mode

- [x] 7.0 Build the LangGraph orchestrator with parallel fan-out
  - [x] 7.1 Create `get_llm()` factory supporting OpenRouter, OpenAI, and Anthropic providers via env var
  - [x] 7.2 Create node wrapper functions for each agent (pass shared LLM instance)
  - [x] 7.3 Define `PipelineState` TypedDict with `Annotated` reducers (`_last_value` for scalars, `_merge_lists` for lists)
  - [x] 7.4 Build `StateGraph` with 5 nodes: log_classifier, remediation, cookbook, jira_ticket, notification
  - [x] 7.5 Wire edges: log_classifier -> remediation -> [cookbook, jira_ticket, notification] (fan-out) -> END
  - [x] 7.6 Implement `run_pipeline()` entry point that initializes state and invokes the compiled graph

- [x] 8.0 Build the Streamlit frontend dashboard
  - [x] 8.1 Set up page config (title, icon, wide layout)
  - [x] 8.2 Build sidebar: LLM provider selector, model input, Slack mode toggle, sample log dropdown + load button
  - [x] 8.3 Build file upload widget accepting .log, .txt, .csv, .json
  - [x] 8.4 Add "Analyze Logs" button with progress bar and status messages
  - [x] 8.5 Display summary metrics row: log entries, issues, JIRA tickets, notification status
  - [x] 8.6 Build Tab 1 (Log Entries): multiselect level filter, color-coded entries
  - [x] 8.7 Build Tab 2 (Issues & Remediation): expandable sections with severity icons, auto-expand CRITICAL/HIGH
  - [x] 8.8 Build Tab 3 (Remediation Cookbook): render markdown cookbook
  - [x] 8.9 Build Tab 4 (JIRA Tickets): expandable tickets with formatted content + raw JSON payload
  - [x] 8.10 Build Tab 5 (Slack Notification): sent/dry-run status, message preview, full payload expander

- [x] 9.0 Create sample log files and configuration
  - [x] 9.1 Create `microservices_mixed.log` — 33 entries across 8 services (OOM, timeouts, auth failures, disk space, bad deployment)
  - [x] 9.2 Create `kubernetes_cluster.log` — etcd quorum loss, pod evictions, CrashLoopBackOff, DNS failures, 502s
  - [x] 9.3 Create `database_outage.log` — table bloat, slow queries, connection pool exhaustion, WAL disk full, failover
  - [x] 9.4 Create `security_incident.log` — brute force, SQL injection/XSS, IAM privilege escalation, CVEs, cert expiry
  - [x] 9.5 Create `ci_cd_pipeline.log` — unit test failures, integration test OOM, Docker image bloat, security scan block
  - [x] 9.6 Create `requirements.txt` with all Python dependencies
  - [x] 9.7 Create `.env.example` with documented env var template
  - [x] 9.8 Configure `.env` with OpenRouter API key, Slack webhook URL, and channel

- [x] 10.0 Integration testing and bug fixes
  - [x] 10.1 Verify all imports resolve correctly (sys.path, package structure)
  - [x] 10.2 Verify LangGraph graph compiles with `PipelineState`
  - [x] 10.3 Test regex log classifier against `microservices_mixed.log` (33 entries: 4 CRITICAL, 10 ERROR, 8 WARN)
  - [x] 10.4 Fix `INVALID_CONCURRENT_GRAPH_UPDATE` error — add Annotated reducers for parallel fan-out state keys
  - [x] 10.5 Verify Streamlit app starts without errors on localhost:8502
  - [x] 10.6 Test end-to-end pipeline with sample log upload — all 5 tabs populate correctly
  - [x] 10.7 Verify Slack notification sends successfully to `#all-langgraphprojectfeb2026`
  - [x] 10.8 Fix cookbook markdown spacing — add `_fix_spacing()` post-processor
  - [x] 10.9 Update agent system prompts for compact formatting across cookbook, JIRA, and notification outputs
