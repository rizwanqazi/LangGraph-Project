# PRD: Sample Logs Expansion & Live Folder Watcher

## 1. Introduction/Overview

This PRD covers two additions to the DevOps Incident Analysis Suite:

1. **10 New Sample Log Files** — Expand the test corpus from 5 to 15 realistic sample logs, covering diverse DevOps failure scenarios that exercise all 7 agents (including the new Root Cause Correlator and Predictive Risk agents).

2. **Live Logs Folder Watcher** — A background feature that monitors a `live_logs/` folder inside `devops_incident_suite/`. When a new log file appears, the pipeline runs automatically — no manual upload or button click required. Results are saved as JSON and a Slack notification is sent. Processed files are moved to `live_logs/processed/`. The existing Streamlit upload workflow remains unchanged.

**Problem it solves:** Currently the only way to analyze logs is through manual upload in the Streamlit UI. In real DevOps environments, log files arrive continuously from CI/CD systems, monitoring tools, or log aggregators. The live watcher bridges this gap by enabling drop-and-analyze automation. The additional sample logs also ensure thorough testing across a wider range of incident types.

## 2. Goals

1. Create 10 new sample log files covering scenarios not already represented (existing 5: microservices cascade, kubernetes, database outage, security incident, CI/CD pipeline).
2. Each new log file should be 20-40 lines with a realistic mix of log levels and failure patterns that produce meaningful output from all agents.
3. Implement a background folder watcher thread inside the Streamlit app that auto-processes new log files from `devops_incident_suite/live_logs/`.
4. Save pipeline results as a JSON file alongside the processed log.
5. Send Slack notifications automatically for live-processed logs.
6. Move processed logs to `live_logs/processed/` to avoid re-processing.
7. Provide a toggle in the Streamlit sidebar to enable/disable the watcher.
8. Display recent live-processed results in the Streamlit UI.

## 3. User Stories

- **As a DevOps engineer**, I want to drop a log file into a folder and have it automatically analyzed without opening the UI, so the pipeline integrates into my existing file-based workflows.
- **As an SRE**, I want to receive Slack alerts automatically when a new log file is processed, so my team is notified of incidents without manual intervention.
- **As a developer testing the suite**, I want 15 diverse sample logs so I can verify the pipeline handles a wide variety of real-world scenarios.
- **As a team lead**, I want to review past live-processed results in the UI, so I can audit what the system has analyzed.

## 4. Functional Requirements

### 4.1 New Sample Log Files

1. Create 10 new `.log` files in `devops_incident_suite/sample_logs/`, each 20-40 lines.
2. All files must use the standard log format: `YYYY-MM-DD HH:MM:SS LEVEL [service-name] Message`.
3. Each file must contain a mix of log levels (INFO, WARN, ERROR, CRITICAL) with at least one clear failure cascade.
4. New scenarios must not duplicate existing ones. Target scenarios:
   - **Cloud infrastructure** (AWS/GCP service failures, IAM issues, region failover)
   - **API gateway / rate limiting** (throttling, 429s cascading, DDoS mitigation)
   - **Message queue** (Kafka/RabbitMQ consumer lag, partition rebalancing, dead letter queue)
   - **DNS / networking** (DNS resolution failures, TLS certificate expiry, network partition)
   - **Storage / S3** (object storage failures, replication lag, bucket policy blocks)
   - **Monitoring / alerting** (Prometheus scrape failures, alert fatigue, metric gaps)
   - **Container registry** (image pull failures, tag mismatch, digest verification)
   - **Load balancer** (health check failures, backend draining, sticky session issues)
   - **Caching layer** (Redis/Memcached evictions, cache stampede, replication lag)
   - **Serverless / Lambda** (cold starts, timeout cascades, concurrency limits)
5. Each log should have enough WARN-level entries to trigger the Predictive Risk agent and enough cross-service references to trigger the Root Cause Correlator.

### 4.2 Live Folder Watcher

6. Create a `live_logs/` directory inside `devops_incident_suite/`.
7. Create a `live_logs/processed/` subdirectory for completed files.
8. Implement a **file watcher** that polls `live_logs/` for new `.log`, `.txt`, `.csv`, or `.json` files.
9. The watcher must run as a **background thread** inside the Streamlit app.
10. The Streamlit sidebar must have a **toggle** to enable/disable the watcher (default: disabled).
11. When a new file is detected:
    a. Run the full pipeline (`run_pipeline()`) on the file contents.
    b. Save the results as a JSON file: `live_logs/processed/<filename>.results.json`.
    c. Move the original log file to `live_logs/processed/<filename>`.
    d. Send a Slack notification (respecting the current Slack mode setting — live or dry-run).
12. The watcher must **not re-process** files that have already been handled (check against the processed folder).
13. The watcher must handle errors gracefully — a bad log file should not crash the watcher thread.
14. The polling interval should be configurable with a sensible default (e.g., 5 seconds).

### 4.3 UI Updates

15. Add a **"Live Watcher"** section in the Streamlit sidebar with:
    - On/Off toggle
    - Status indicator (watching / stopped)
    - Count of files processed in the current session
16. Add a **"Live Results"** tab (8th tab) in the main area that shows:
    - List of recently processed files from `live_logs/processed/`
    - Click/expand to view the summary results (issues count, risk predictions, causal chains)
    - Option to load a past result into the full 7-tab view

## 5. Non-Goals (Out of Scope)

- **Remote folder monitoring** — Only local filesystem watching, not S3/GCS/network shares.
- **Real-time streaming** — The watcher processes complete files, not streaming log lines.
- **Multi-file correlation** — Each log file is analyzed independently; no cross-file analysis.
- **Watcher persistence** — The watcher only runs while the Streamlit app is running. No system-level daemon or service.
- **File format auto-detection** — Files must have appropriate extensions (.log, .txt, .csv, .json).

## 6. Design Considerations

### Sidebar Layout (Live Watcher Section)
```
──────────────────
  Live Folder Watcher
  [Toggle: Off / On]
  Status: ● Watching live_logs/
  Files processed: 3
──────────────────
```

### Live Results Tab
- Table/list of processed files with timestamp, filename, issues count, risk count
- Expandable rows showing summary metrics
- "Load Full Results" button to populate the main 7 tabs with that file's analysis

### Folder Structure
```
devops_incident_suite/
├── live_logs/
│   ├── processed/
│   │   ├── some_log.log
│   │   └── some_log.log.results.json
│   └── (new files dropped here)
├── sample_logs/
│   ├── (existing 5 files)
│   └── (10 new files)
└── ...
```

## 7. Technical Considerations

- **Polling approach:** Use Python's `os.listdir()` polling in a background thread (via `threading.Thread`). Simpler and more cross-platform than `watchdog` or `inotify` libraries. No new dependencies needed.
- **Thread safety:** The watcher thread should not share mutable state with the Streamlit main thread. Use `st.session_state` carefully — write results to files and let the UI read from files.
- **Streamlit reruns:** Streamlit reruns the script on interaction. The watcher thread must be started once and persisted across reruns using `st.session_state` to track the thread reference.
- **JSON results format:** Save pipeline results using `json.dumps()` with `default=str` for non-serializable types. Include metadata (filename, timestamp, processing time).
- **Sample log format:** All new logs must follow the same `YYYY-MM-DD HH:MM:SS LEVEL [service] Message` format that the regex parser handles, ensuring no LLM fallback is needed for parsing.

## 8. Success Metrics

1. All 15 sample logs (5 existing + 10 new) run through the pipeline without errors.
2. Each new sample log produces at least 1 causal chain and 1 risk prediction.
3. The live watcher correctly detects and processes a file dropped into `live_logs/` within 10 seconds.
4. Processed files are moved to `live_logs/processed/` with a `.results.json` companion file.
5. Slack notifications fire automatically for live-processed files.
6. The watcher toggle works correctly — enabling starts watching, disabling stops.
7. The Live Results tab displays past results and allows loading them into the main view.

## 9. Open Questions

1. Should the polling interval be user-configurable in the sidebar, or is 5 seconds sufficient?
2. Should there be a maximum file size limit for auto-processing (to prevent accidental processing of huge files)?
3. Should the Live Results tab auto-refresh, or require a manual refresh button?
