# Tasks: Sample Logs Expansion & Live Folder Watcher

## Relevant Files

- `devops_incident_suite/sample_logs/cloud_infrastructure.log` - **NEW** — AWS/GCP failures, IAM, region failover
- `devops_incident_suite/sample_logs/api_gateway_ratelimit.log` - **NEW** — Throttling, 429 cascades, DDoS mitigation
- `devops_incident_suite/sample_logs/message_queue.log` - **NEW** — Kafka consumer lag, partition rebalancing, DLQ
- `devops_incident_suite/sample_logs/dns_networking.log` - **NEW** — DNS failures, TLS expiry, network partition
- `devops_incident_suite/sample_logs/storage_s3.log` - **NEW** — Object storage failures, replication lag
- `devops_incident_suite/sample_logs/monitoring_alerting.log` - **NEW** — Prometheus scrape failures, metric gaps
- `devops_incident_suite/sample_logs/container_registry.log` - **NEW** — Image pull failures, tag mismatch
- `devops_incident_suite/sample_logs/load_balancer.log` - **NEW** — Health check failures, backend draining
- `devops_incident_suite/sample_logs/caching_layer.log` - **NEW** — Redis evictions, cache stampede
- `devops_incident_suite/sample_logs/serverless_lambda.log` - **NEW** — Cold starts, timeout cascades, concurrency limits
- `devops_incident_suite/live_logs/` - **NEW** — Directory for auto-processing
- `devops_incident_suite/live_logs/processed/` - **NEW** — Subdirectory for completed files and JSON results
- `devops_incident_suite/utils/watcher.py` - **NEW** — File watcher background thread module
- `devops_incident_suite/app.py` - Add sidebar watcher toggle, Live Results tab, update tab count

### Notes

- All sample logs must use format: `YYYY-MM-DD HH:MM:SS LEVEL [service] Message` so the regex parser handles them (no LLM fallback)
- Each log should be 20-40 lines with cross-service references (for RCA) and WARN-level escalation patterns (for Predictive Risk)
- The watcher uses `threading.Thread` + `os.listdir()` polling — no new dependencies
- Run the app with `cd devops_incident_suite && streamlit run app.py` to test
- To test the watcher: enable it in the sidebar, then `cp sample_logs/microservices_mixed.log live_logs/` from another terminal

## Instructions for Completing Tasks

**IMPORTANT:** Check off each task by changing `- [ ]` to `- [x]` after completing.

## Tasks

- [x] 0.0 Create feature branch
  - [x] 0.1 SKIPPED — staying on `feature/new-agents` branch per user request

- [x] 1.0 Create sample log files (first 5 of 10)
  - [x] 1.1 Create `cloud_infrastructure.log` — Scenario: AWS EC2 instance health check failures cascade to auto-scaling group issues, IAM role assumption failures block recovery, region failover triggers. Services: ec2-monitor, auto-scaler, iam-service, route53, cloudwatch. ~30 lines.
  - [x] 1.2 Create `api_gateway_ratelimit.log` — Scenario: Mobile client surge hits rate limits, 429 responses cascade to retry storms, circuit breaker triggers, DDoS mitigation activates. Services: api-gateway, rate-limiter, waf-service, backend-api, cdn-edge. ~28 lines.
  - [x] 1.3 Create `message_queue.log` — Scenario: Kafka consumer lag spikes, partition rebalancing stalls, messages pile up in dead letter queue, producer backpressure triggers. Services: kafka-broker, consumer-group, producer-service, dlq-handler, zookeeper. ~30 lines.
  - [x] 1.4 Create `dns_networking.log` — Scenario: DNS resolution failures for internal services, TLS certificate approaching expiry, network partition between availability zones. Services: coredns, cert-manager, network-controller, service-mesh, health-checker. ~26 lines.
  - [x] 1.5 Create `storage_s3.log` — Scenario: S3 bucket replication lag increases, object PUT failures, bucket policy blocks cross-account access, storage costs spike alert. Services: s3-sync, storage-proxy, backup-service, cost-monitor, replication-agent. ~28 lines.

- [x] 2.0 Create sample log files (remaining 5 of 10)
  - [x] 2.1 Create `monitoring_alerting.log` — Scenario: Prometheus scrape targets go down, alert manager floods with duplicate alerts, metric gaps cause dashboard outage, Grafana query timeouts. Services: prometheus, alertmanager, grafana, node-exporter, thanos-query. ~28 lines.
  - [x] 2.2 Create `container_registry.log` — Scenario: Docker image pull failures during deployment, tag mismatch between staging/prod, digest verification fails, registry disk pressure. Services: registry-service, deployment-controller, image-scanner, garbage-collector, build-agent. ~26 lines.
  - [x] 2.3 Create `load_balancer.log` — Scenario: Backend health checks fail, servers drain but new connections keep arriving, sticky session mismatch, SSL termination overload. Services: nginx-lb, health-monitor, backend-pool, ssl-terminator, traffic-manager. ~28 lines.
  - [x] 2.4 Create `caching_layer.log` — Scenario: Redis memory pressure triggers evictions, cache stampede on popular keys after eviction, replication lag between primary and replica, client connection pool exhaustion. Services: redis-primary, redis-replica, cache-proxy, app-server, connection-pool. ~30 lines.
  - [x] 2.5 Create `serverless_lambda.log` — Scenario: Lambda cold starts spike latency, downstream API timeouts cascade, concurrency limit hit causes throttling, DLQ fills up. Services: lambda-handler, api-gateway, dynamodb-client, sqs-trigger, cloudwatch-logs. ~26 lines.

- [x] 3.0 Create the live_logs directory structure
  - [x] 3.1 Create `devops_incident_suite/live_logs/` directory
  - [x] 3.2 Create `devops_incident_suite/live_logs/processed/` subdirectory
  - [x] 3.3 Add a `.gitkeep` file in `live_logs/` (per vibe-check: skip `.gitkeep` in `processed/` — created at runtime)
  - [x] 3.4 Add `devops_incident_suite/live_logs/processed/` to `.gitignore` (per vibe-check: one line covers everything)

- [x] 4.0 Implement the file watcher module
  - [x] 4.1 Create `devops_incident_suite/utils/watcher.py` with the watcher class/functions
  - [x] 4.2 Implement `_get_pending_files(watch_dir, processed_dir)` — list files in `watch_dir` with valid extensions (.log, .txt, .csv, .json) that are not already in `processed_dir`
  - [x] 4.3 Implement `_process_file(file_path, processed_dir)` — read the file, call `run_pipeline()`, save results JSON to `processed_dir/<filename>.results.json`, move original file to `processed_dir/<filename>`
  - [x] 4.4 Wrap `_process_file` in try/except so a bad file doesn't crash the watcher
  - [x] 4.5 Implement `start_watcher(watch_dir, processed_dir, poll_interval=5)` — a function that runs in a loop: poll for pending files, process each, sleep for `poll_interval` seconds. Takes a `threading.Event` stop signal.
  - [x] 4.6 Implement `stop_watcher(stop_event)` — sets the stop event to gracefully terminate the loop
  - [x] 4.7 Include metadata in the results JSON: `filename`, `processed_at` (ISO timestamp), `processing_time_seconds`, plus all pipeline output fields

- [x] 5.0 Integrate watcher into Streamlit sidebar
  - [x] 5.1 Add a "Live Folder Watcher" section in the sidebar after the Slack config section
  - [x] 5.2 Add an on/off toggle (`st.toggle`) for the watcher (default: off)
  - [x] 5.3 When toggled on: start the watcher in a background `threading.Thread`, store thread + stop_event in `st.session_state` so it persists across Streamlit reruns
  - [x] 5.4 When toggled off: call `stop_watcher()` to set the stop event and join the thread
  - [x] 5.5 Display a status indicator: green "Watching live_logs/" when active, gray "Stopped" when inactive
  - [x] 5.6 Display count of `.results.json` files in `live_logs/processed/` as "Files processed" metric

- [x] 6.0 Add the "Live Results" tab (8th tab)
  - [x] 6.1 Add "Live Results" as the 8th tab in `st.tabs()`
  - [x] 6.2 Scan `live_logs/processed/` for `.results.json` files, sorted by modification time (newest first)
  - [x] 6.3 Display each result as an expandable row showing: filename, processed timestamp, issues count, causal chains count, risk predictions count
  - [x] 6.4 Add a "Load Full Results" button inside each expander that loads that file's results into `st.session_state["result"]` so the other 7 tabs populate with it
  - [x] 6.5 Handle empty state — show "No live-processed results yet" info message
  - [x] 6.6 Add a "Refresh" button at the top of the tab to re-scan the processed directory

- [x] 7.0 End-to-end testing
  - [x] 7.1 Verify all 15 sample logs run through the pipeline without errors (batch test)
  - [x] 7.2 Enable the watcher, copy a sample log to `live_logs/`, verify it's auto-processed within 10s
  - [x] 7.3 Verify the original file moves to `live_logs/processed/` and a `.results.json` is created
  - [x] 7.4 Verify the Live Results tab shows the processed file and "Load Full Results" populates the other tabs
  - [x] 7.5 Verify Slack notification fires for live-processed logs
  - [x] 7.6 Disable the watcher, copy another file, verify it's NOT processed (watcher is stopped)
  - [x] 7.7 Verify Streamlit sample log dropdown shows all 15 files
