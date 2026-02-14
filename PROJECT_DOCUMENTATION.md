# DevOps Incident Analysis Suite — Complete Project Documentation

---

## Table of Contents

1. [Purpose — High-Level Overview](#1-purpose--high-level-overview)
2. [Steps to Achieve the Purpose](#2-steps-to-achieve-the-purpose)
3. [How the Code Achieves That Purpose](#3-how-the-code-achieves-that-purpose)
4. [Tools and External Services](#4-tools-and-external-services)
5. [Libraries and Function Calls Explained](#5-libraries-and-function-calls-explained)
6. [Detailed Code Walkthrough — All Files](#6-detailed-code-walkthrough--all-files)
7. [Code Flow Chart](#7-code-flow-chart)
8. [Deep Dive Q&A — Key Concepts Explained](#8-deep-dive-qa--key-concepts-explained)
   - [8.1 `invoke()` vs `run()` — What's the difference?](#81-invoke-vs-run--whats-the-difference)
   - [8.2 Why are there two `PipelineState` definitions?](#82-why-are-there-two-pipelinestate-definitions)
   - [8.3 What are reducers and why do we need them?](#83-what-are-reducers-and-why-do-we-need-them)
   - [8.4 Why don't `raw_logs` and `file_name` need reducers?](#84-why-dont-raw_logs-and-file_name-need-reducers)
   - [8.5 How does the shared state get created, updated, and merged?](#85-how-does-the-shared-state-get-created-updated-and-merged)

---

## 1. Purpose — High-Level Overview

### What does this project do?

Imagine you are an engineer responsible for keeping a company's servers running 24/7. Every second, these servers produce **log files** — plain text records of everything that happens, like:

```
2026-02-13 10:23:45 ERROR [auth-service] Login failed for user admin after 5 attempts
2026-02-13 10:23:46 CRITICAL [payment-service] Out of memory - process killed by OOM killer
2026-02-13 10:23:47 WARN [storage-service] Disk usage at 92%, approaching critical threshold
```

When things go wrong, there can be **hundreds or thousands** of these log lines. Reading through them manually is slow and error-prone. This project solves that problem.

### The Big Picture — Start to End

Here is what happens from the moment a user opens the app to the moment they get results:

1. **The user opens a web dashboard** (built with Streamlit) in their browser.
2. **They upload a log file** (or pick a sample one) — this is a `.log`, `.txt`, `.csv`, or `.json` file containing server logs.
3. **They click "Analyze Logs"** — this triggers a pipeline of 5 AI agents.
4. **Agent 1 (Log Classifier)** reads the raw text and converts each line into a structured record with fields like `timestamp`, `level`, `service`, and `message`. It tries fast regex (pattern matching) first, and only calls the AI if needed.
5. **Agent 2 (Remediation)** looks at all the ERROR, WARN, and CRITICAL entries, groups related ones together, assigns severity levels (CRITICAL / HIGH / MEDIUM / LOW), and recommends specific fixes.
6. **Agents 3, 4, and 5 run in parallel** (at the same time):
   - **Agent 3 (Cookbook)** creates a prioritized, step-by-step remediation runbook in markdown.
   - **Agent 4 (JIRA Ticket)** generates structured JIRA ticket payloads for the most serious issues.
   - **Agent 5 (Notification)** formats a Slack message summarizing the top issues and sends it (or simulates sending it).
7. **The results are displayed** across 5 tabs in the dashboard: parsed logs, issues, cookbook, JIRA tickets, and Slack notification.

Think of it as an **assembly line in a factory**: raw logs go in on one end, and actionable intelligence comes out on the other end, with each station (agent) adding value along the way.

### Why is this useful?

- **Speed**: What takes a human engineer 30–60 minutes to analyze, this pipeline does in seconds.
- **Consistency**: The AI agents follow the same analysis rules every time.
- **Actionability**: Instead of just finding problems, the pipeline tells you exactly what to do about them.
- **Integration**: It can send Slack notifications and generate JIRA tickets automatically.

---

## 2. Steps to Achieve the Purpose

The project achieves its purpose in **7 major steps**. Each step builds on the previous one:

### Step 1: User Interface Setup
The Streamlit web app provides a dashboard where users can upload logs, configure settings (like which AI model to use), and view results. This is the entry point — everything starts when the user clicks "Analyze Logs."

### Step 2: Log Parsing and Classification
The first AI agent reads the raw log text line by line. It converts messy, unstructured text into clean, structured data — like turning a handwritten grocery list into a neatly organized spreadsheet. Each log line gets a `timestamp`, `level` (ERROR, WARN, etc.), `service` name, and `message`.

### Step 3: Issue Detection and Remediation
The second AI agent acts like a doctor examining symptoms. It looks at all the "bad" log entries (errors, warnings, critical messages), groups related symptoms together into diagnoses (issues), rates how severe each issue is, and prescribes treatment (recommended fixes).

### Step 4: Cookbook / Runbook Generation
The third AI agent takes all the diagnosed issues and creates a single, organized document — a remediation cookbook. Think of it like a recipe book: for each problem, it lists the exact steps to fix it, what you should expect after applying the fix, and which log lines are related.

### Step 5: JIRA Ticket Creation
The fourth AI agent creates structured ticket payloads for the most critical issues (CRITICAL and HIGH severity only). These are formatted exactly like real JIRA tickets would be, with a title, description, priority, labels, and steps to reproduce — ready to be submitted to a bug-tracking system.

### Step 6: Slack Notification
The fifth AI agent creates a concise summary of the top 5 issues and formats it for Slack (a messaging platform used by engineering teams). If a Slack webhook URL is configured, it actually sends the message to a real Slack channel. Otherwise, it does a "dry run" — it prepares the message but doesn't send it.

### Step 7: Results Display
All results from the 5 agents are collected and displayed across 5 tabs in the web dashboard. The user can filter, expand, and explore each result in detail.

---

## 3. How the Code Achieves That Purpose

### Architecture — The Multi-Agent Pipeline

The code uses a design pattern called a **directed acyclic graph (DAG)**, managed by a library called **LangGraph**. Here's how it works:

```
                        ┌──────────────────────┐
                        │   User uploads logs   │
                        └──────────┬───────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │  Log Classifier Agent │  (Agent 1 — sequential)
                        │  Parse raw text into  │
                        │  structured entries   │
                        └──────────┬───────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │  Remediation Agent    │  (Agent 2 — sequential)
                        │  Detect issues and    │
                        │  recommend fixes      │
                        └──────────┬───────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
             ┌────────────┐ ┌───────────┐ ┌──────────────┐
             │  Cookbook   │ │   JIRA    │ │ Notification │  (Agents 3,4,5 — parallel)
             │  Agent     │ │  Ticket   │ │    Agent     │
             │            │ │  Agent    │ │              │
             └─────┬──────┘ └─────┬─────┘ └──────┬───────┘
                   │              │              │
                   └──────────────┼──────────────┘
                                  │
                                  ▼
                        ┌──────────────────────┐
                        │    Display Results    │
                        │   (5 tabs in the UI)  │
                        └──────────────────────┘
```

### Key Design Decisions

1. **Regex-First Parsing**: The log classifier first tries to match logs with fast regex patterns. Only if that fails does it call the AI model. This saves time and money (AI API calls cost money).

2. **Shared State**: All agents read from and write to a single shared state dictionary. Think of it as a shared whiteboard — Agent 1 writes parsed logs on it, Agent 2 reads those logs and writes issues, etc.

3. **Parallel Fan-Out**: After the remediation agent finishes, three agents run simultaneously. This is faster than running them one after another. LangGraph manages this automatically using "reducers" (functions that merge results from parallel agents).

4. **LLM Provider Flexibility**: The code supports three AI providers (OpenRouter, OpenAI, Anthropic) and can switch between them by changing a single environment variable.

5. **Deterministic Post-Processing**: Instead of relying on the AI to format markdown perfectly every time, the cookbook agent uses Python code to fix formatting after the AI generates content. This makes the output consistent.

---

## 4. Tools and External Services

### Tools Used in Development

| Tool | What It Is | How It's Used |
|------|-----------|---------------|
| **Python 3.11+** | The programming language | All code is written in Python |
| **Streamlit** | A web app framework for Python | Creates the interactive dashboard UI |
| **LangGraph** | An AI agent orchestration library | Manages the pipeline flow (which agent runs when, parallel execution, shared state) |
| **LangChain** | An AI/LLM framework | Provides the interface to talk to AI models (sending prompts, getting responses) |
| **Pydantic** | A data validation library | Defines the structure of data (LogEntry, Issue, JiraTicket, etc.) with validation |
| **Git** | Version control | Tracks code changes |
| **pip / venv** | Python package management | Installs and manages dependencies |

### External Services (APIs)

| Service | What It Does | How It's Used |
|---------|-------------|---------------|
| **OpenRouter** | An AI model aggregator API | Default AI provider — sends prompts to models like GPT-4o-mini through a single API endpoint |
| **OpenAI API** | OpenAI's direct API | Alternative AI provider — can use GPT models directly |
| **Anthropic API** | Anthropic's API for Claude models | Alternative AI provider — can use Claude models |
| **Slack Incoming Webhooks** | A Slack integration for sending messages | Sends notification summaries to a Slack channel when configured |

### What is NOT used (mock/simulated)

| Service | Status |
|---------|--------|
| **JIRA API** | Mock — tickets are generated as JSON payloads but NOT actually submitted to JIRA |
| **PagerDuty** | Not integrated — mentioned in PRD as a future enhancement |

---

## 5. Libraries and Function Calls Explained

### Core Libraries

#### 1. `streamlit` — Web Dashboard Framework

Streamlit turns Python scripts into interactive web apps. You write Python code, and Streamlit renders it as a web page with widgets.

```python
import streamlit as st

# This creates a title on the web page
st.title("My App")

# This creates a file upload button
uploaded_file = st.file_uploader("Upload a file", type=["txt"])

# This creates a button
if st.button("Click me"):
    st.write("You clicked the button!")
```

**Key functions used in the project:**

| Function | What It Does | Example |
|----------|-------------|---------|
| `st.set_page_config()` | Sets the page title, icon, and layout | `st.set_page_config(page_title="My App", layout="wide")` |
| `st.title()` | Displays a large heading | `st.title("DevOps Suite")` |
| `st.caption()` | Displays small gray text | `st.caption("A subtitle")` |
| `st.sidebar` | Creates a sidebar section | `with st.sidebar: st.header("Settings")` |
| `st.selectbox()` | Creates a dropdown menu | `choice = st.selectbox("Pick one", ["A", "B", "C"])` |
| `st.text_input()` | Creates a text input field | `name = st.text_input("Your name")` |
| `st.radio()` | Creates radio buttons | `mode = st.radio("Mode", ["Live", "Dry Run"])` |
| `st.file_uploader()` | Creates a file upload widget | `file = st.file_uploader("Upload", type=["log"])` |
| `st.button()` | Creates a clickable button | `if st.button("Go"): do_something()` |
| `st.progress()` | Creates a progress bar | `bar = st.progress(0); bar.progress(50)` |
| `st.tabs()` | Creates tabbed sections | `tab1, tab2 = st.tabs(["Tab A", "Tab B"])` |
| `st.columns()` | Creates side-by-side columns | `col1, col2 = st.columns(2)` |
| `st.metric()` | Displays a big number with label | `st.metric("Users", 42)` |
| `st.expander()` | Creates a collapsible section | `with st.expander("Details"): st.write("...")` |
| `st.markdown()` | Renders markdown text | `st.markdown("**bold** text")` |
| `st.code()` | Displays code with syntax highlighting | `st.code("print('hi')", language="python")` |
| `st.json()` | Displays JSON data nicely formatted | `st.json({"key": "value"})` |
| `st.info()` / `st.success()` / `st.warning()` / `st.error()` | Colored alert boxes | `st.error("Something went wrong!")` |
| `st.session_state` | Persistent storage across reruns | `st.session_state["data"] = result` |
| `st.stop()` | Stops the script execution | `st.stop()` (after an error) |
| `st.divider()` | Draws a horizontal line | `st.divider()` |

---

#### 2. `langgraph` — AI Agent Orchestration

LangGraph lets you define a pipeline of AI agents as a directed graph. Each agent is a "node," and "edges" connect them to define the execution order.

```python
from langgraph.graph import StateGraph, END

# Create a graph with a shared state
graph = StateGraph(MyStateType)

# Add agent functions as nodes
graph.add_node("step1", my_first_function)
graph.add_node("step2", my_second_function)

# Define the order: step1 → step2 → END
graph.set_entry_point("step1")
graph.add_edge("step1", "step2")
graph.add_edge("step2", END)

# Compile and run
compiled = graph.compile()
result = compiled.invoke({"input": "data"})
```

**Key functions used:**

| Function | What It Does | Example |
|----------|-------------|---------|
| `StateGraph(state_type)` | Creates a new graph with a typed state | `graph = StateGraph(PipelineState)` — creates a graph where the shared state follows the `PipelineState` structure |
| `graph.add_node(name, fn)` | Adds an agent function as a node | `graph.add_node("classifier", classify_fn)` — registers a function that will process state |
| `graph.set_entry_point(name)` | Sets which node runs first | `graph.set_entry_point("classifier")` — the classifier runs first when the graph starts |
| `graph.add_edge(from, to)` | Connects two nodes (from runs before to) | `graph.add_edge("step1", "step2")` — after step1 finishes, step2 starts |
| `graph.add_edge(from, END)` | Marks a node as a terminal node | `graph.add_edge("step2", END)` — the pipeline ends after step2 |
| `graph.compile()` | Finalizes the graph for execution | `compiled = graph.compile()` — prepares the graph to accept input and run |
| `compiled.invoke(state)` | Runs the entire pipeline with initial state | `result = compiled.invoke({"raw_logs": "..."})` — executes all nodes in order and returns the final state |

**Parallel Fan-Out**: When one node has edges to multiple nodes, LangGraph runs them in parallel:

```python
# remediation → cookbook (parallel)
# remediation → jira_ticket (parallel)
# remediation → notification (parallel)
graph.add_edge("remediation", "cookbook")
graph.add_edge("remediation", "jira_ticket")
graph.add_edge("remediation", "notification")
```

---

#### 3. `langchain` / `langchain-openai` / `langchain-anthropic` — LLM Communication

LangChain provides a unified way to talk to different AI models. No matter which provider you use, the code looks the same.

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Create an AI model connection
llm = ChatOpenAI(model="gpt-4o-mini", api_key="sk-...", temperature=0.2)

# Send a message and get a response
response = llm.invoke([
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="What is 2+2?"),
])

print(response.content)  # "4"
```

**Key classes and functions:**

| Class / Function | What It Does | Example |
|-----------------|-------------|---------|
| `ChatOpenAI(model, api_key, ...)` | Creates a connection to OpenAI or OpenAI-compatible APIs | `llm = ChatOpenAI(model="gpt-4o-mini")` — creates a connection to GPT-4o-mini |
| `ChatAnthropic(model, api_key, ...)` | Creates a connection to Anthropic's Claude | `llm = ChatAnthropic(model="claude-sonnet-4-20250514")` |
| `SystemMessage(content=...)` | A message that tells the AI what role to play | `SystemMessage(content="You are a log parser.")` — sets the AI's behavior |
| `HumanMessage(content=...)` | A message from the user to the AI | `HumanMessage(content="Parse these logs: ...")` — sends the actual task |
| `llm.invoke(messages)` | Sends messages to the AI and gets a response | `response = llm.invoke([sys_msg, human_msg])` — returns an AI response object |
| `response.content` | The text response from the AI | `text = response.content` — gets the AI's text output |
| `temperature=0.2` | Controls randomness (0 = deterministic, 1 = creative) | Low temperature makes output more consistent and predictable |
| `base_url="..."` | Overrides the API endpoint | Used for OpenRouter: `base_url="https://openrouter.ai/api/v1"` |

---

#### 4. `pydantic` — Data Validation and Schemas

Pydantic lets you define the exact shape and rules for your data. If data doesn't match the rules, it raises an error.

```python
from pydantic import BaseModel, Field

class Student(BaseModel):
    name: str = Field(description="Student's full name")
    age: int = Field(description="Age in years")
    grade: str = Field(default="A", description="Letter grade")

# This works:
s = Student(name="Alice", age=17)
print(s.grade)  # "A" (uses default)

# This fails — age must be an integer:
s = Student(name="Bob", age="not a number")  # ValidationError!
```

**Key concepts used:**

| Concept | What It Does | Example |
|---------|-------------|---------|
| `BaseModel` | Base class for defining data structures | `class LogEntry(BaseModel): ...` — creates a data template |
| `Field(description=...)` | Adds metadata and defaults to a field | `name: str = Field(description="The name")` |
| `Field(default_factory=list)` | Sets a default value using a factory function | `labels: list[str] = Field(default_factory=list)` — default is `[]` |
| `str, Enum` | An enum that also works as a string | `class LogLevel(str, Enum): ERROR = "ERROR"` |
| `model.model_dump()` | Converts the model to a plain dictionary | `entry.model_dump()` → `{"line_number": 1, "level": "ERROR", ...}` |

---

#### 5. `python-dotenv` — Environment Variable Loading

Loads secret configuration values (like API keys) from a `.env` file so they don't have to be hardcoded in the source code.

```python
from dotenv import load_dotenv
import os

# Load variables from .env file into environment
load_dotenv()

# Now you can read them
api_key = os.getenv("OPENROUTER_API_KEY")
```

| Function | What It Does |
|----------|-------------|
| `load_dotenv()` | Reads the `.env` file and loads its variables into the system environment |
| `os.getenv("KEY", "default")` | Reads an environment variable with an optional default value |
| `os.environ["KEY"] = "value"` | Sets an environment variable at runtime |
| `os.environ.pop("KEY", None)` | Removes an environment variable (returns `None` if it doesn't exist) |

---

#### 6. `requests` — HTTP Client

A simple library for making HTTP requests (like calling APIs or sending data to a URL).

```python
import requests

# Send a POST request with JSON data
response = requests.post(
    "https://hooks.slack.com/services/...",
    json={"text": "Hello from Python!"},
    timeout=10,
)
response.raise_for_status()  # Raises an error if the request failed
```

| Function | What It Does |
|----------|-------------|
| `requests.post(url, json=data, timeout=10)` | Sends a POST request with JSON payload and a 10-second timeout |
| `response.raise_for_status()` | Raises an exception if the HTTP status code indicates an error (4xx or 5xx) |

---

#### 7. Python Standard Library — `re` (Regular Expressions)

Regex is a pattern-matching language used to find and extract parts of text.

```python
import re

# This pattern matches a date followed by a log level
pattern = re.compile(r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<level>ERROR|WARN|INFO)")

line = "2026-02-13 ERROR Something broke"
match = pattern.match(line)

if match:
    print(match.group("date"))   # "2026-02-13"
    print(match.group("level"))  # "ERROR"
```

| Function | What It Does |
|----------|-------------|
| `re.compile(pattern)` | Compiles a regex pattern into a reusable object (faster for repeated use) |
| `pattern.match(text)` | Tries to match the pattern at the beginning of the text |
| `match.group("name")` | Extracts the part of the text that matched a named group `(?P<name>...)` |
| `re.sub(pattern, replacement, text)` | Replaces all matches of the pattern with the replacement text |
| `re.match(pattern, text)` | Quick one-off match (without pre-compiling) |

---

#### 8. Python Standard Library — `json`

Used for converting between Python dictionaries/lists and JSON text (a standard data format used by APIs).

```python
import json

# Python dict → JSON string
text = json.dumps({"name": "Alice", "age": 17}, indent=2)
# Output:
# {
#   "name": "Alice",
#   "age": 17
# }

# JSON string → Python dict
data = json.loads('{"name": "Alice", "age": 17}')
print(data["name"])  # "Alice"
```

| Function | What It Does |
|----------|-------------|
| `json.dumps(obj, indent=2, default=str)` | Converts a Python object to a JSON string. `indent=2` makes it readable. `default=str` handles non-serializable objects by converting them to strings. |
| `json.loads(text)` | Converts a JSON string back to a Python object (dict/list) |

---

#### 9. Python Standard Library — `typing`

Provides type hints that make code more readable and help catch bugs.

```python
from typing import TypedDict, Annotated, Any

class MyState(TypedDict):
    name: str              # must be a string
    scores: list           # must be a list
    data: Any              # can be anything
    value: Annotated[str, some_function]  # string with metadata
```

| Type | What It Does |
|------|-------------|
| `TypedDict` | A dictionary with fixed, typed keys — like a blueprint for a dictionary |
| `Annotated[type, metadata]` | Attaches extra information to a type hint. LangGraph uses this for "reducers" |
| `Any` | Means any type is allowed |

---

## 6. Detailed Code Walkthrough — All Files

---

### File 1: `models/schemas.py` — Data Blueprints

**Location:** `devops_incident_suite/models/schemas.py`
**Lines:** 98
**Purpose:** Defines all the data structures (blueprints) that data follows as it flows between agents.

Think of this file as the "dictionary" for the project — it tells everyone what a "LogEntry" looks like, what a "JiraTicket" contains, etc.

#### Enums (Lines 13–34)

```python
class LogLevel(str, Enum):
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    WARN = "WARN"
    WARNING = "WARNING"
    INFO = "INFO"
    DEBUG = "DEBUG"
    UNKNOWN = "UNKNOWN"
```

**What this does:** Defines all possible log levels. `str, Enum` means each value is both a string and an enum member. This prevents typos — you can only use valid log levels.

```python
class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
```

**What this does:** Defines severity levels for detected issues.

```python
class TicketPriority(str, Enum):
    HIGHEST = "Highest"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
```

**What this does:** Defines JIRA ticket priority levels (note the different casing from Severity — JIRA uses "Highest" not "CRITICAL").

#### Data Models (Lines 39–77)

```python
class LogEntry(BaseModel):
    line_number: int = Field(description="Original line number in the log file")
    timestamp: str = Field(default="", description="Timestamp from the log entry")
    level: LogLevel = Field(description="Log level classification")
    service: str = Field(default="unknown", description="Service or component name")
    message: str = Field(description="Log message content")
    raw: str = Field(description="Original raw log line")
```

**What this does:** Defines the structure of a single parsed log entry. When Agent 1 parses a raw log line like `2026-02-13 10:23:45 ERROR [auth-service] Login failed`, it creates a `LogEntry` with:
- `line_number = 1`
- `timestamp = "2026-02-13 10:23:45"`
- `level = LogLevel.ERROR`
- `service = "auth-service"`
- `message = "Login failed"`
- `raw = "2026-02-13 10:23:45 ERROR [auth-service] Login failed"`

```python
class Issue(BaseModel):
    issue: str = Field(description="Description of the detected issue")
    severity: Severity = Field(description="Issue severity level")
    recommended_fix: str = Field(description="Actionable remediation step")
    rationale: str = Field(description="Reasoning behind the recommendation")
    source_entries: list[int] = Field(default_factory=list, description="Line numbers of related log entries")
```

**What this does:** Defines a detected issue. For example: "The auth-service has multiple failed login attempts from the same IP, indicating a brute force attack. Severity: HIGH. Recommended Fix: Block the IP address and enable rate limiting."

```python
class JiraTicket(BaseModel):
    summary: str = Field(description="Ticket summary/title")
    description: str = Field(description="Detailed ticket description")
    priority: TicketPriority = Field(description="Ticket priority")
    labels: list[str] = Field(default_factory=list)
    steps_to_reproduce: str = Field(default="", description="Steps to reproduce from logs")
    status: str = Field(default="CREATED (mock)", description="Simulated creation status")
```

**What this does:** Defines the structure of a JIRA ticket. Note `status` defaults to `"CREATED (mock)"` because this project doesn't actually submit tickets to JIRA.

```python
class SlackNotification(BaseModel):
    channel: str = Field(default="#devops-alerts")
    summary: str = Field(description="Notification summary text")
    payload: dict = Field(default_factory=dict, description="Full Slack message payload")
    sent: bool = Field(default=False, description="Whether the message was actually sent")
    mode: str = Field(default="dry-run", description="'live' or 'dry-run'")
```

**What this does:** Defines the Slack notification output. The `sent` field tells us whether the message was actually delivered, and `mode` tells us if it was live or a dry run.

#### Pipeline State Model (Lines 82–98)

```python
class PipelineState(BaseModel):
    raw_logs: str = ""
    file_name: str = ""
    log_entries: list[LogEntry] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)
    cookbook: str = ""
    jira_tickets: list[JiraTicket] = Field(default_factory=list)
    notification: SlackNotification | None = None
    current_agent: str = ""
    error: str = ""
```

**What this does:** Defines the complete state that flows through the pipeline. This model is defined here for documentation purposes, but the actual pipeline uses a `TypedDict` version in `graph.py` (because LangGraph requires `TypedDict` for its reducer annotations).

---

### File 2: `graph.py` — The Orchestrator (Brain of the Pipeline)

**Location:** `devops_incident_suite/graph.py`
**Lines:** 165
**Purpose:** This is the central file that connects all agents together and defines the order of execution.

#### Imports and Setup (Lines 1–15)

```python
from __future__ import annotations
import operator
import os
from typing import Annotated, Any, TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from agents import log_classifier, remediation, cookbook, jira_ticket, notification

load_dotenv()
```

**What this does:**
- Imports all 5 agent modules from the `agents/` folder.
- Imports `StateGraph` and `END` from LangGraph (the graph builder and the terminal marker).
- Calls `load_dotenv()` to load API keys from the `.env` file.

#### Reducer Functions (Lines 20–27)

```python
def _last_value(a, b):
    """Reducer that keeps the latest non-empty value."""
    return b if b else a

def _merge_lists(a: list, b: list) -> list:
    """Reducer that merges two lists."""
    return (a or []) + (b or [])
```

**What this does:** When 3 agents run in parallel and all try to update the same state field, there's a conflict — whose value wins? Reducers solve this:

- `_last_value`: For fields like `cookbook` (a string), the most recent non-empty value wins. Only one agent writes to `cookbook`, so there's no real conflict.
- `_merge_lists`: For fields like `jira_tickets` (a list), results from all agents are combined into one list.

**Example:** If Agent 3 returns `jira_tickets = [ticket1]` and Agent 4 returns `jira_tickets = [ticket2]`, the reducer merges them into `[ticket1, ticket2]`.

#### Pipeline State Definition (Lines 30–39)

```python
class PipelineState(TypedDict):
    raw_logs: str
    file_name: str
    log_entries: Annotated[list, _merge_lists]
    issues: Annotated[list, _merge_lists]
    cookbook: Annotated[str, _last_value]
    jira_tickets: Annotated[list, _merge_lists]
    notification: Annotated[Any, _last_value]
    current_agent: Annotated[str, _last_value]
    error: Annotated[str, _last_value]
```

**What this does:** This is the shared whiteboard that all agents read from and write to. The `Annotated` type tells LangGraph which reducer function to use for each field when parallel agents return results.

For example, `log_entries: Annotated[list, _merge_lists]` means: "The `log_entries` field is a list, and when multiple agents update it simultaneously, merge all their lists together."

#### LLM Factory — `get_llm()` (Lines 44–74)

```python
def get_llm():
    provider = os.getenv("LLM_PROVIDER", "openrouter").lower()

    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), ...)

    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"), ...)

    # Default: OpenRouter
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        base_url="https://openrouter.ai/api/v1",
        ...
    )
```

**What this does:** This is a "factory function" — it creates the right AI model connection based on configuration. Think of it like a universal TV remote that works with different brands:

- If `LLM_PROVIDER=openai`, it creates an OpenAI connection.
- If `LLM_PROVIDER=anthropic`, it creates an Anthropic (Claude) connection.
- If `LLM_PROVIDER=openrouter` (or anything else), it creates an OpenRouter connection. OpenRouter uses the same API format as OpenAI but routes to many different models, so it reuses `ChatOpenAI` with a custom `base_url`.

#### Shared LLM Instance (Lines 79–86)

```python
_llm = None

def _get_shared_llm():
    global _llm
    if _llm is None:
        _llm = get_llm()
    return _llm
```

**What this does:** This is the "singleton pattern" — it ensures only one LLM connection is created and shared across all agents. Without this, each agent would create its own connection, wasting resources.

The `global _llm` keyword lets the function modify the module-level `_llm` variable. The first time `_get_shared_llm()` is called, it creates the LLM. Every subsequent call returns the same instance.

#### Node Wrapper Functions (Lines 91–108)

```python
def log_classifier_node(state: dict) -> dict:
    return log_classifier.run(state, _get_shared_llm())

def remediation_node(state: dict) -> dict:
    return remediation.run(state, _get_shared_llm())

def cookbook_node(state: dict) -> dict:
    return cookbook.run(state, _get_shared_llm())

def jira_ticket_node(state: dict) -> dict:
    return jira_ticket.run(state, _get_shared_llm())

def notification_node(state: dict) -> dict:
    return notification.run(state, _get_shared_llm())
```

**What this does:** LangGraph nodes must be functions that take a `state` dict and return a `state` dict. These wrapper functions simply call each agent's `run()` function with the shared LLM instance. They act as adapters between the LangGraph interface and the agent modules.

#### Graph Building — `build_graph()` (Lines 113–142)

```python
def build_graph() -> StateGraph:
    graph = StateGraph(PipelineState)

    # Add nodes
    graph.add_node("log_classifier", log_classifier_node)
    graph.add_node("remediation", remediation_node)
    graph.add_node("cookbook", cookbook_node)
    graph.add_node("jira_ticket", jira_ticket_node)
    graph.add_node("notification", notification_node)

    # Sequential: log_classifier → remediation
    graph.set_entry_point("log_classifier")
    graph.add_edge("log_classifier", "remediation")

    # Fan-out: remediation → three parallel agents
    graph.add_edge("remediation", "cookbook")
    graph.add_edge("remediation", "jira_ticket")
    graph.add_edge("remediation", "notification")

    # All three converge to END
    graph.add_edge("cookbook", END)
    graph.add_edge("jira_ticket", END)
    graph.add_edge("notification", END)

    return graph.compile()
```

**What this does:** This is where the pipeline is assembled, step by step:

1. Create a new graph with the `PipelineState` definition.
2. Register all 5 agent functions as nodes.
3. Set `log_classifier` as the entry point (runs first).
4. Connect `log_classifier` → `remediation` (sequential).
5. Connect `remediation` → `cookbook`, `jira_ticket`, and `notification` (fan-out — all three run in parallel after remediation finishes).
6. Connect all three downstream agents to `END` (the pipeline is done once all three finish).
7. Compile the graph — this finalizes it and makes it ready to execute.

#### Pipeline Execution — `run_pipeline()` (Lines 145–164)

```python
def run_pipeline(raw_logs: str, file_name: str = "upload") -> dict:
    global _llm
    _llm = None  # Reset to pick up any env changes

    compiled = build_graph()
    initial_state = {
        "raw_logs": raw_logs,
        "file_name": file_name,
        "log_entries": [],
        "issues": [],
        "cookbook": "",
        "jira_tickets": [],
        "notification": None,
        "current_agent": "",
        "error": "",
    }
    result = compiled.invoke(initial_state)
    return result
```

**What this does:** This is the main entry point that the UI calls. It:

1. Resets the LLM instance (in case the user changed settings in the sidebar).
2. Builds the graph.
3. Creates the initial state with the raw logs and empty result fields.
4. Invokes the graph — this runs all agents in the correct order and returns the final state with all results populated.

---

### File 3: `agents/log_classifier.py` — Agent 1: Log Parser

**Location:** `devops_incident_suite/agents/log_classifier.py`
**Lines:** 143
**Purpose:** Takes raw log text and converts each line into a structured `LogEntry` record.

#### System Prompt (Lines 13–29)

```python
SYSTEM_PROMPT = """\
You are a Log Classifier Agent for a DevOps incident analysis pipeline.

Your job:
1. Parse each raw log line into structured fields: timestamp, level, service, message.
2. Classify the log level (CRITICAL, ERROR, WARN/WARNING, INFO, DEBUG).
3. Extract the service/component name when present.

Return your output as a JSON array of objects with these exact keys:
  line_number, timestamp, level, service, message
...
"""
```

**What this does:** This is the instruction given to the AI model when the regex parser fails. It tells the AI exactly what to do and what format to return. Think of it as the "job description" for Agent 1.

#### Regex Patterns (Lines 32–49)

```python
LOG_PATTERNS = [
    # Standard syslog: 2024-01-15 10:23:45 ERROR [auth-service] Message
    re.compile(
        r"^(?P<timestamp>\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}[.\d]*\s*[A-Z]*)\s+"
        r"(?P<level>CRITICAL|ERROR|WARN(?:ING)?|INFO|DEBUG)\s+"
        r"(?:\[(?P<service>[^\]]+)\]\s*)?"
        r"(?P<message>.+)$",
        re.IGNORECASE,
    ),
    # Apache/nginx style: [timestamp] [error] [client] msg
    re.compile(
        r"^\[(?P<timestamp>[^\]]+)\]\s+"
        r"\[(?P<level>\w+)\]\s+"
        r"(?:\[(?P<service>[^\]]*)\]\s*)?"
        r"(?P<message>.+)$",
        re.IGNORECASE,
    ),
]
```

**What this does:** These are two regex patterns that cover the most common log formats:

- **Pattern 1 (Syslog)**: Matches lines like `2026-02-13 10:23:45 ERROR [auth-service] Login failed`. It uses named groups (`?P<timestamp>`, `?P<level>`, etc.) to extract each part.
- **Pattern 2 (Apache)**: Matches lines like `[Tue Jan 15] [error] [client 1.2.3.4] Access denied`.

The `?:` prefix means "match but don't capture" — used for the brackets themselves. The `?` after `(?:\[(?P<service>...)\]\s*)?` makes the service part optional.

#### Level Mapping (Lines 51–63)

```python
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
```

**What this does:** Maps various level strings (including abbreviations like "err") to the standard `LogLevel` enum. The `.lower()` makes it case-insensitive — "ERROR", "Error", and "error" all map to `LogLevel.ERROR`.

#### Regex Parsing — `_try_regex_parse()` (Lines 66–91)

```python
def _try_regex_parse(lines: list[str]) -> list[LogEntry] | None:
    entries = []
    for i, line in enumerate(lines, start=1):
        line = line.strip()
        if not line:
            continue
        matched = False
        for pattern in LOG_PATTERNS:
            m = pattern.match(line)
            if m:
                entries.append(LogEntry(
                    line_number=i,
                    timestamp=m.group("timestamp").strip(),
                    level=_parse_level(m.group("level")),
                    service=m.group("service") or "unknown",
                    message=m.group("message").strip(),
                    raw=line,
                ))
                matched = True
                break
        if not matched:
            return None  # Fall back to LLM
    return entries
```

**What this does:** Tries to parse ALL lines using regex. If even ONE line doesn't match any pattern, the entire function returns `None`, signaling that the LLM should be used instead. This is an "all-or-nothing" approach — either regex handles everything, or the LLM handles everything.

**Why this approach?** Mixing regex-parsed and LLM-parsed results could lead to inconsistencies. It's simpler and more reliable to use one method for the entire file.

#### LLM Response Parsing — `_parse_llm_response()` (Lines 94–119)

```python
def _parse_llm_response(response_text: str, raw_lines: list[str]) -> list[LogEntry]:
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
        entries.append(LogEntry(
            line_number=line_num,
            timestamp=item.get("timestamp", ""),
            level=_parse_level(item.get("level", "UNKNOWN")),
            service=item.get("service", "unknown"),
            message=item.get("message", ""),
            raw=raw or item.get("message", ""),
        ))
    return entries
```

**What this does:** Parses the AI's JSON response into `LogEntry` objects. It also handles a common AI quirk — sometimes the AI wraps its JSON output in markdown code fences (` ```json ... ``` `), even though we told it not to. The `re.sub` lines strip those fences.

#### Main Run Function (Lines 122–142)

```python
def run(state: dict, llm) -> dict:
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
```

**What this does:** This is the main function called by the graph. The strategy is:

1. Split the raw log text into individual lines.
2. Try regex parsing first (fast, free, deterministic).
3. If regex succeeds, convert entries to dictionaries and return.
4. If regex fails (returns `None`), fall back to the LLM — send all logs to the AI with the system prompt, then parse the AI's JSON response.

The `e.model_dump()` converts each `LogEntry` Pydantic object into a plain Python dictionary, which is what LangGraph expects in its state.

---

### File 4: `agents/remediation.py` — Agent 2: Issue Detector

**Location:** `devops_incident_suite/agents/remediation.py`
**Lines:** 87
**Purpose:** Analyzes classified log entries (especially errors and warnings) to detect issues, assign severity, and recommend fixes.

#### System Prompt (Lines 13–36)

The system prompt gives the AI clear severity guidelines:
- **CRITICAL**: System down, data loss, security breach
- **HIGH**: Service degradation, repeated failures
- **MEDIUM**: Warnings that may escalate
- **LOW**: Informational issues

It also instructs the AI to group related log entries by root cause (e.g., 10 "connection timeout" errors from the same service should become ONE issue, not 10 separate issues).

#### Main Run Function (Lines 39–86)

```python
def run(state: dict, llm) -> dict:
    log_entries = state.get("log_entries", [])

    # Filter to only actionable entries
    actionable_levels = {"CRITICAL", "ERROR", "WARN", "WARNING"}
    actionable = [e for e in log_entries if e.get("level", "") in actionable_levels]

    if not actionable:
        return {"issues": [], "current_agent": "remediation"}

    entries_text = json.dumps(actionable, indent=2, default=str)

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Analyze these log entries and recommend fixes:\n\n{entries_text}"),
    ])

    # Parse and validate
    text = response.content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"issues": [], "error": f"Remediation agent returned invalid JSON: {text[:200]}", "current_agent": "remediation"}

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
```

**What this does step by step:**

1. **Filter**: Only look at log entries with level CRITICAL, ERROR, WARN, or WARNING. INFO and DEBUG entries are ignored.
2. **Convert to JSON**: Turn the filtered entries into a JSON string for the AI to analyze.
3. **AI Analysis**: Send the entries to the AI with the system prompt. The AI identifies issues, assigns severities, and recommends fixes.
4. **Parse Response**: Convert the AI's JSON response into Python dictionaries.
5. **Validate Severity**: If the AI returns an invalid severity (e.g., "URGENT"), default to "MEDIUM".
6. **Error Handling**: If the AI returns invalid JSON, return an empty list and record the error.

---

### File 5: `agents/cookbook.py` — Agent 3: Runbook Generator

**Location:** `devops_incident_suite/agents/cookbook.py`
**Lines:** 111
**Purpose:** Creates a consolidated, prioritized remediation runbook in markdown format from the detected issues.

#### System Prompt (Lines 11–53)

The system prompt is very specific about formatting:
- No blank line between the issue title and its sub-items (Action, Expected outcome, Related log lines).
- A blank line between separate issue blocks.
- Organized by severity priority: CRITICAL first, then HIGH, MEDIUM, LOW.
- Checkbox format for each issue so engineers can track progress.

#### Run Function (Lines 56–77)

```python
def run(state: dict, llm) -> dict:
    issues = state.get("issues", [])

    if not issues:
        cookbook = "# Incident Remediation Cookbook\n\nNo actionable issues detected. All systems appear healthy."
        return {"cookbook": cookbook, "current_agent": "cookbook"}

    issues_text = json.dumps(issues, indent=2, default=str)

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Create a remediation cookbook from these issues:\n\n{issues_text}"),
    ])

    cookbook_md = _fix_spacing(response.content.strip())
    return {"cookbook": cookbook_md, "current_agent": "cookbook"}
```

**What this does:** Sends the issues to the AI, gets a markdown runbook back, then applies deterministic post-processing (`_fix_spacing`) to ensure consistent formatting.

#### Post-Processing — `_fix_spacing()` (Lines 80–110)

```python
def _fix_spacing(md: str) -> str:
    lines = md.split("\n")
    result = []
    for i, line in enumerate(lines):
        # Skip blank lines between checkbox and sub-items
        if (
            line.strip() == ""
            and i > 0 and i < len(lines) - 1
            and re.match(r"^\s*- \[[ x]\] ", lines[i - 1])
            and re.match(r"^\s+- \*\*", lines[i + 1])
        ):
            continue
        result.append(line)

    # Ensure blank line between last sub-item and next checkbox
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
```

**What this does:** This function fixes the markdown spacing deterministically (without relying on the AI to get it right):

1. **First pass**: Removes unwanted blank lines between a checkbox title and its sub-items. For example, removes the blank line between `- [ ] **OOM Kill**` and `  - **Action:** Increase memory limits`.

2. **Second pass**: Ensures there IS a blank line between the last sub-item of one block and the checkbox of the next block. This keeps issues visually separated.

**Why not just let the AI handle formatting?** AI models are inconsistent with whitespace. Sometimes they add extra blank lines, sometimes they don't. By using code to fix spacing, the output looks perfect every time.

---

### File 6: `agents/jira_ticket.py` — Agent 4: Ticket Generator

**Location:** `devops_incident_suite/agents/jira_ticket.py`
**Lines:** 79
**Purpose:** Generates structured JIRA ticket payloads for CRITICAL and HIGH severity issues only.

#### Run Function (Lines 31–78)

```python
def run(state: dict, llm) -> dict:
    issues = state.get("issues", [])

    # Only create tickets for CRITICAL and HIGH
    ticketable = [i for i in issues if i.get("severity") in ("CRITICAL", "HIGH")]

    if not ticketable:
        return {"jira_tickets": [], "current_agent": "jira_ticket"}

    issues_text = json.dumps(ticketable, indent=2, default=str)

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Generate JIRA tickets for these issues:\n\n{issues_text}"),
    ])

    # Parse and validate
    text = response.content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {"jira_tickets": [], "error": f"JIRA agent returned invalid JSON: {text[:200]}", "current_agent": "jira_ticket"}

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
```

**What this does step by step:**

1. **Filter**: Only process CRITICAL and HIGH severity issues. MEDIUM and LOW issues don't get tickets.
2. **AI Generation**: Send the filtered issues to the AI, which generates ticket payloads with summary, description, priority, labels, and steps to reproduce.
3. **Validate Priority**: If the AI returns an invalid priority (e.g., "Urgent"), default to "High".
4. **Mock Status**: Every ticket gets `status: "CREATED (mock)"` because no real JIRA API call is made.

---

### File 7: `agents/notification.py` — Agent 5: Slack Notifier

**Location:** `devops_incident_suite/agents/notification.py`
**Lines:** 91
**Purpose:** Formats a concise Slack notification summary and optionally sends it via webhook.

#### Channel Helper (Lines 13–14)

```python
def _get_channel() -> str:
    return os.getenv("SLACK_CHANNEL", "#new-channel")
```

**What this does:** Reads the Slack channel name from the environment. Defaults to `#new-channel` if not set.

#### Run Function (Lines 35–90)

```python
def run(state: dict, llm) -> dict:
    issues = state.get("issues", [])
    cookbook = state.get("cookbook", "")

    if not issues:
        return {
            "notification": {
                "channel": _get_channel(),
                "summary": "No actionable issues detected.",
                "payload": {},
                "sent": False,
                "mode": "dry-run",
            },
            "current_agent": "notification",
        }

    context = json.dumps(
        {"issues": issues, "cookbook_preview": cookbook[:500]},
        indent=2, default=str,
    )

    response = llm.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=f"Create a Slack notification for these findings:\n\n{context}"),
    ])

    summary_text = response.content.strip()

    payload = {
        "channel": _get_channel(),
        "text": summary_text,
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": summary_text}},
        ],
    }

    sent, mode = send_slack_message(payload)

    return {
        "notification": {
            "channel": _get_channel(),
            "summary": summary_text,
            "payload": payload,
            "sent": sent,
            "mode": mode,
        },
        "current_agent": "notification",
    }
```

**What this does step by step:**

1. **Check for issues**: If no issues exist, return a "no issues" notification without sending anything.
2. **Build context**: Combine the issues list and the first 500 characters of the cookbook into a JSON context for the AI.
3. **AI Formatting**: Send the context to the AI, which formats it into a scannable Slack message with severity indicators and recommended actions.
4. **Build Slack Payload**: Wrap the AI's text in a Slack-compatible payload structure with `blocks` (Slack's rich message format).
5. **Send or Dry Run**: Call `send_slack_message()` which attempts to send via webhook. If no webhook URL is configured, it's a dry run.

---

### File 8: `utils/slack_client.py` — Slack Webhook Helper

**Location:** `devops_incident_suite/utils/slack_client.py`
**Lines:** 27
**Purpose:** Handles the actual HTTP request to send a message to Slack.

```python
def send_slack_message(payload: dict) -> tuple[bool, str]:
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")

    if not webhook_url:
        return False, "dry-run"

    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        resp.raise_for_status()
        return True, "live"
    except Exception:
        return False, "dry-run (send failed)"
```

**What this does:**

1. Read the webhook URL from the environment.
2. If no URL is configured → return `(False, "dry-run")`. The notification agent will record that the message was NOT sent.
3. If a URL IS configured → attempt to POST the payload to Slack with a 10-second timeout.
4. If the POST succeeds → return `(True, "live")`. The message was delivered.
5. If the POST fails (network error, invalid URL, etc.) → return `(False, "dry-run (send failed)")`. The message was prepared but couldn't be delivered.

This is an elegant pattern: no configuration flags, no if/else in the notification agent — the behavior changes automatically based on whether the environment variable exists.

---

### File 9: `app.py` — The Streamlit Frontend

**Location:** `devops_incident_suite/app.py`
**Lines:** 248
**Purpose:** Creates the interactive web dashboard that users interact with.

#### Page Config (Lines 19–28)

```python
st.set_page_config(
    page_title="DevOps Incident Analysis Suite",
    page_icon="🔍",
    layout="wide",
)
st.title("DevOps Incident Analysis Suite")
st.caption("Upload server/ops logs and let AI agents analyze, triage, and recommend fixes.")
```

**What this does:** Sets up the browser tab title, favicon, and uses wide layout. Displays the main heading and subtitle.

#### Sidebar Configuration (Lines 33–76)

```python
with st.sidebar:
    st.header("Configuration")
    provider = st.selectbox("LLM Provider", ["openrouter", "openai", "anthropic"], index=0)
    os.environ["LLM_PROVIDER"] = provider

    # Model name input (changes based on provider)
    if provider == "openrouter":
        model = st.text_input("Model", value=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"))
        os.environ["OPENROUTER_MODEL"] = model
    # ... similar for openai and anthropic

    # Slack mode toggle
    slack_mode = st.radio("Slack Notifications", ["Dry Run (mock)", "Live (send via webhook)"])
    if slack_mode.startswith("Live"):
        webhook = st.text_input("Slack Webhook URL", type="password")
        if webhook:
            os.environ["SLACK_WEBHOOK_URL"] = webhook
    else:
        os.environ.pop("SLACK_WEBHOOK_URL", None)

    # Sample log loader
    sample_files = sorted(f for f in os.listdir(sample_dir) if f.endswith(".log"))
    selected_sample = st.selectbox("Sample Logs", sample_files)
    if st.button("Load Sample Log"):
        with open(os.path.join(sample_dir, selected_sample)) as f:
            st.session_state["sample_content"] = f.read()
```

**What this does:** The sidebar lets users:
- Switch AI providers and models on the fly.
- Toggle between dry-run and live Slack notifications.
- Load one of the 5 included sample log files.

Note how the sidebar directly modifies `os.environ` — this means the graph's `get_llm()` function will pick up these changes without needing to pass parameters around.

#### File Upload and Analysis (Lines 81–127)

```python
uploaded_file = st.file_uploader("Upload a log file", type=["log", "txt", "csv", "json"])

raw_logs = None
if uploaded_file is not None:
    raw_logs = uploaded_file.read().decode("utf-8", errors="replace")
    file_name = uploaded_file.name
elif "sample_content" in st.session_state:
    raw_logs = st.session_state["sample_content"]
    file_name = st.session_state.get("sample_name", "sample.log")

if raw_logs and st.button("Analyze Logs", type="primary"):
    progress = st.progress(0, text="Starting analysis pipeline...")
    try:
        result = run_pipeline(raw_logs, file_name)
    except Exception as e:
        st.error(f"Pipeline error: {e}")
        st.stop()
    progress.progress(100, text="Analysis complete!")
    st.session_state["result"] = result
```

**What this does:**
- Provides a file upload widget that accepts .log, .txt, .csv, and .json files.
- If no file is uploaded, falls back to a sample log (if loaded from the sidebar).
- When "Analyze Logs" is clicked, runs the full pipeline and stores the result in session state.
- Shows a progress bar during analysis.

#### Results Display — 5 Tabs (Lines 131–247)

**Tab 1 — Log Entries (Lines 159–180):**
Displays each parsed log entry with color-coded severity levels. Users can filter by level using a multiselect dropdown. Colors: CRITICAL/ERROR = red, WARN = orange, INFO = blue, DEBUG = gray.

**Tab 2 — Issues & Remediation (Lines 183–195):**
Displays detected issues in expandable sections. CRITICAL and HIGH issues are expanded by default. Each section shows the issue description, recommended fix, rationale, and related log line numbers.

**Tab 3 — Remediation Cookbook (Lines 198–204):**
Renders the markdown cookbook directly. This shows the prioritized checklist with checkboxes, action steps, and expected outcomes.

**Tab 4 — JIRA Tickets (Lines 207–222):**
Displays each JIRA ticket in an expandable section with its details (priority, labels, description, steps to reproduce). Also shows the raw JSON payload in a nested expander.

**Tab 5 — Slack Notification (Lines 225–243):**
Shows whether the notification was sent or dry-run, a preview of the Slack message, and the full Slack payload JSON.

---

## 7. Code Flow Chart

Below is the complete flow of data through the system, from user interaction to final output.

```
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                              USER INTERACTION                                    ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
                                      │
                         ┌────────────┴────────────┐
                         │  User opens Streamlit    │
                         │  dashboard (app.py)      │
                         └────────────┬────────────┘
                                      │
                    ┌─────────────────┴──────────────────┐
                    │                                    │
           ┌────────┴─────────┐              ┌──────────┴──────────┐
           │  Upload .log     │      OR      │  Load sample log    │
           │  file via UI     │              │  from sidebar       │
           └────────┬─────────┘              └──────────┬──────────┘
                    │                                    │
                    └─────────────────┬──────────────────┘
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │  raw_logs = string of   │
                         │  the entire log file    │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │  User clicks            │
                         │  "Analyze Logs" button   │
                         └────────────┬────────────┘
                                      │
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                          PIPELINE EXECUTION (graph.py)                            ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │  run_pipeline()         │
                         │  - Reset LLM instance   │
                         │  - Build graph           │
                         │  - Create initial state  │
                         │  - compiled.invoke()     │
                         └────────────┬────────────┘
                                      │
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                 AGENT 1: LOG CLASSIFIER (log_classifier.py)                      ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │  Split raw_logs into     │
                         │  individual lines        │
                         └────────────┬────────────┘
                                      │
                              ┌───────┴───────┐
                              │               │
                              ▼               ▼
                    ┌─────────────────┐  ┌─────────────────┐
                    │ Try regex parse │  │ If regex fails   │
                    │ (fast, free)    │  │ → LLM fallback   │
                    │                 │  │ (slower, costs $) │
                    └────────┬────────┘  └────────┬────────┘
                              │               │
                              └───────┬───────┘
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │  Output: list of        │
                         │  LogEntry dicts          │
                         │  {line_number, timestamp,│
                         │   level, service,        │
                         │   message, raw}          │
                         └────────────┬────────────┘
                                      │
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                 AGENT 2: REMEDIATION (remediation.py)                            ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │  Filter: keep only       │
                         │  CRITICAL, ERROR,        │
                         │  WARN, WARNING entries    │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │  Send filtered entries   │
                         │  to LLM for analysis     │
                         └────────────┬────────────┘
                                      │
                                      ▼
                         ┌────────────────────────┐
                         │  Output: list of Issue   │
                         │  dicts {issue, severity,  │
                         │  recommended_fix,         │
                         │  rationale,               │
                         │  source_entries}          │
                         └────────────┬────────────┘
                                      │
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                    PARALLEL FAN-OUT (3 agents run simultaneously)                 ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                 │
                    ▼                 ▼                 ▼
    ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
    │  AGENT 3: COOKBOOK │ │  AGENT 4: JIRA    │ │  AGENT 5: NOTIFY  │
    │  (cookbook.py)     │ │  (jira_ticket.py) │ │  (notification.py)│
    │                   │ │                   │ │                   │
    │ • Receives all    │ │ • Filters to      │ │ • Receives issues │
    │   issues          │ │   CRITICAL + HIGH │ │   + cookbook       │
    │ • Sends to LLM    │ │   issues only     │ │ • Sends to LLM    │
    │ • Gets markdown   │ │ • Sends to LLM    │ │ • Gets Slack      │
    │   runbook         │ │ • Gets JSON       │ │   formatted text  │
    │ • Post-processes  │ │   ticket payloads │ │ • Builds payload  │
    │   spacing         │ │ • Validates       │ │ • Calls           │
    │                   │ │   priority        │ │   send_slack_     │
    │                   │ │ • Adds mock       │ │   message()       │
    │                   │ │   status          │ │                   │
    └────────┬──────────┘ └────────┬──────────┘ └────────┬──────────┘
             │                     │                     │
             │                     │                     ▼
             │                     │           ┌───────────────────┐
             │                     │           │  slack_client.py  │
             │                     │           │                   │
             │                     │           │ Webhook URL set?  │
             │                     │           │ ├── YES → POST    │
             │                     │           │ │   to Slack      │
             │                     │           │ │   (sent=True,   │
             │                     │           │ │    mode="live")  │
             │                     │           │ └── NO → skip     │
             │                     │           │     (sent=False,  │
             │                     │           │      mode=        │
             │                     │           │      "dry-run")   │
             │                     │           └────────┬──────────┘
             │                     │                     │
             ▼                     ▼                     ▼
    ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
    │ Output:         │  │ Output:         │  │ Output:         │
    │ cookbook (str)   │  │ jira_tickets    │  │ notification    │
    │ — markdown      │  │ (list of dicts) │  │ (dict with      │
    │   runbook       │  │ — ticket        │  │  summary,       │
    │                 │  │   payloads      │  │  payload, sent, │
    │                 │  │                 │  │  mode)          │
    └────────┬────────┘  └────────┬────────┘  └────────┬────────┘
             │                     │                     │
             └─────────────────────┼─────────────────────┘
                                   │
                                   ▼
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                  STATE MERGING (LangGraph Reducers)                               ║
║                                                                                   ║
║  _merge_lists → combines jira_tickets from all agents                            ║
║  _last_value  → keeps latest cookbook, notification, current_agent                ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
                                   │
                                   ▼
╔═══════════════════════════════════════════════════════════════════════════════════╗
║                       RESULTS DISPLAY (app.py)                                    ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
                                   │
                    ┌──────────────┴──────────────┐
                    │      Summary Metrics         │
                    │ ┌──────┬──────┬──────┬─────┐ │
                    │ │ Logs │Issues│Tickets│Notif│ │
                    │ │  33  │  8   │  4   │Sent │ │
                    │ └──────┴──────┴──────┴─────┘ │
                    └──────────────┬──────────────┘
                                   │
       ┌──────────┬──────────┬─────┴────┬──────────┐
       ▼          ▼          ▼          ▼          ▼
  ┌─────────┐┌─────────┐┌─────────┐┌─────────┐┌─────────┐
  │  Tab 1  ││  Tab 2  ││  Tab 3  ││  Tab 4  ││  Tab 5  │
  │  Log    ││ Issues  ││Cookbook  ││  JIRA   ││  Slack  │
  │ Entries ││  &      ││Runbook  ││ Tickets ││ Notif   │
  │         ││Remediate││         ││         ││         │
  │ Color   ││Expandable│ Markdown││Expandable│ Sent/   │
  │ coded   ││sections ││ render  ││+ JSON   ││ Dry Run │
  │ + filter││+ icons  ││         ││ payload ││+ payload│
  └─────────┘└─────────┘└─────────┘└─────────┘└─────────┘
```

### Simplified Flow Summary

```
User uploads log file
        │
        ▼
  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
  │ 1. CLASSIFY  │ ──▶ │ 2. DIAGNOSE  │ ──▶ │ 3,4,5.      │
  │ Parse logs   │     │ Find issues  │     │ PARALLEL:    │
  │ into records │     │ & recommend  │     │ • Cookbook    │
  │              │     │ fixes        │     │ • JIRA       │
  └─────────────┘     └─────────────┘     │ • Slack      │
                                           └──────┬──────┘
                                                  │
                                                  ▼
                                           ┌─────────────┐
                                           │ DISPLAY      │
                                           │ 5 tabs with  │
                                           │ all results  │
                                           └─────────────┘
```

---

## Project File Map

```
LangGraph_Project/
├── CLAUDE.md                               # Project instructions for Claude Code
├── PROJECT_DOCUMENTATION.md                # This file — complete project explanation
├── requirements.txt                        # Root-level Python dependencies (56 packages)
├── .env                                    # API keys and configuration (DO NOT SHARE)
│
├── devops_incident_suite/                  # Main application code
│   ├── app.py                              # Streamlit web dashboard (248 lines)
│   ├── graph.py                            # LangGraph orchestrator (165 lines)
│   ├── requirements.txt                    # App-specific dependencies (9 packages)
│   ├── .env.example                        # Template for .env configuration
│   ├── README.md                           # Quick start guide
│   │
│   ├── agents/                             # AI agent modules
│   │   ├── __init__.py                     # Package marker (empty)
│   │   ├── log_classifier.py              # Agent 1: Parse logs (143 lines)
│   │   ├── remediation.py                 # Agent 2: Detect issues (87 lines)
│   │   ├── cookbook.py                     # Agent 3: Generate runbook (111 lines)
│   │   ├── jira_ticket.py                 # Agent 4: Create tickets (79 lines)
│   │   └── notification.py               # Agent 5: Slack notification (91 lines)
│   │
│   ├── models/                             # Data schema definitions
│   │   ├── __init__.py                     # Package marker (empty)
│   │   └── schemas.py                     # Pydantic models (98 lines)
│   │
│   ├── utils/                              # Utility helpers
│   │   ├── __init__.py                     # Package marker (empty)
│   │   └── slack_client.py               # Slack webhook sender (27 lines)
│   │
│   └── sample_logs/                        # Pre-made test log files
│       ├── microservices_mixed.log         # Mixed microservices incidents
│       ├── kubernetes_cluster.log          # Kubernetes cluster failures
│       ├── database_outage.log             # PostgreSQL outage cascade
│       ├── security_incident.log           # Security breach scenarios
│       └── ci_cd_pipeline.log              # CI/CD pipeline failures
│
└── tasks/                                  # Planning documents
    ├── prd-devops-incident-analysis-suite.md        # Product Requirements Document
    ├── tasks-devops-incident-analysis-suite.md      # Implementation task list
    └── vibe-check-devops-incident-analysis-suite.md # Code quality review
```

---

## 8. Deep Dive Q&A — Key Concepts Explained

These are commonly asked questions about the inner workings of this project. Each one is answered with analogies and diagrams to make the concepts stick.

---

### 8.1 `invoke()` vs `run()` — What's the difference?

These look similar but are fundamentally different things:

#### `invoke()` — A LangChain/LangGraph method

`invoke` is part of the **LangChain Runnable interface**. Any LangChain object that is "runnable" (LLMs, compiled graphs, chains) has this method. It means "execute this thing synchronously and return the result."

It's used in two places in the project:

**1. Running the compiled graph** (`graph.py` line 163):
```python
compiled = build_graph()
result = compiled.invoke(initial_state)  # runs the entire pipeline
```

**2. Calling the LLM** (e.g., `log_classifier.py` line 137):
```python
response = llm.invoke([
    SystemMessage(content=SYSTEM_PROMPT),
    HumanMessage(content="Parse these log lines..."),
])
```

#### `run()` — Just a custom Python function

`run()` in this project is **not** a LangGraph method at all. It's a plain function the developer defined in each agent module as a naming convention. It could have been named `execute()` or `process()` — the name doesn't matter to LangGraph.

```python
# This is just a regular function, nothing special to LangGraph
def run(state: dict, llm) -> dict:
    ...
    return {"log_entries": [...]}
```

LangGraph only cares about the **node wrapper functions** registered in the graph:

```python
graph.add_node("log_classifier", log_classifier_node)  # ← this is what LangGraph knows about
```

#### Summary Table

| Method | Belongs to | Purpose |
|--------|-----------|---------|
| `invoke()` | LangChain Runnable interface | Execute a compiled graph or LLM call synchronously |
| `run()` | Custom code (developer-defined) | Just a naming convention for agent logic — LangGraph doesn't know or care about it |

The Runnable interface also has `ainvoke` (async), `stream` (get results token-by-token), and `batch` (run multiple inputs). In this project, only `invoke` is used since everything runs synchronously.

---

### 8.2 Why are there two `PipelineState` definitions?

`PipelineState` is defined **twice** in this codebase, and understanding why is important:

#### The one that actually runs — `graph.py` (lines 30–39)

```python
class PipelineState(TypedDict):
    raw_logs: str
    file_name: str
    log_entries: Annotated[list, _merge_lists]
    issues: Annotated[list, _merge_lists]
    cookbook: Annotated[str, _last_value]
    jira_tickets: Annotated[list, _merge_lists]
    notification: Annotated[Any, _last_value]
    current_agent: Annotated[str, _last_value]
    error: Annotated[str, _last_value]
```

This is the **authoritative** version. It's a `TypedDict` (a dictionary with fixed keys) that LangGraph uses as the shared state. The `Annotated` hints attach **reducer functions** that tell LangGraph how to merge results when parallel agents update the same field simultaneously.

LangGraph **requires** `TypedDict` for this reducer annotation pattern to work.

#### The one that's just documentation — `schemas.py` (lines 87–98)

```python
class PipelineState(BaseModel):
    raw_logs: str = ""
    log_entries: list[LogEntry] = Field(default_factory=list)
    issues: list[Issue] = Field(default_factory=list)
    ...
```

This is a **Pydantic `BaseModel`** version. It's not actually used at runtime — it serves as a readable reference for what the pipeline state looks like. The vibe-check document even flagged this as slightly redundant.

#### Comparison

| | `graph.py` (TypedDict) | `schemas.py` (BaseModel) |
|---|---|---|
| **Used at runtime** | Yes | No |
| **Has reducers** | Yes (`_merge_lists`, `_last_value`) | No |
| **LangGraph compatible** | Yes | No — LangGraph needs TypedDict |
| **Purpose** | Actual pipeline state | Documentation / data contract reference |

---

### 8.3 What are reducers and why do we need them?

#### The Problem

After the remediation agent finishes, three agents run **at the same time** (parallel fan-out):

```
remediation ──→ cookbook       (writes: cookbook, current_agent)
           ──→ jira_ticket   (writes: jira_tickets, current_agent)
           ──→ notification  (writes: notification, current_agent)
```

All three finish independently and each returns a partial state dict back to LangGraph. LangGraph now has **3 updates to the same state**. How does it combine them? That's what reducers answer.

#### `_merge_lists` — For list fields

```python
def _merge_lists(a: list, b: list) -> list:
    return (a or []) + (b or [])
```

Used on: `log_entries`, `issues`, `jira_tickets`

If two agents both returned `jira_tickets`, all tickets get combined into one list (not one overwriting the other).

#### `_last_value` — For single-value fields

```python
def _last_value(a, b):
    return b if b else a
```

Used on: `cookbook`, `notification`, `current_agent`, `error`

The latest non-empty value wins. For `current_agent`, all 3 parallel agents write this — whichever finishes last wins.

#### "But no two agents write to the same field — so why bother?"

Great observation! In this project, each parallel agent writes to its own unique field:

- cookbook agent → `cookbook`
- jira_ticket agent → `jira_tickets`
- notification agent → `notification`

There's no actual collision. **But LangGraph doesn't know that.** It just sees 3 parallel nodes finishing and needs a merge rule for EVERY field in the state, or it crashes.

#### The Pizza Kitchen Analogy

Imagine a pizza kitchen where 3 chefs work at the same counter simultaneously:

```
┌──────────────────────────────────────────────────────┐
│                  SHARED COUNTER                       │
│                                                      │
│  🍕 Pizza Tray    🥗 Salad Bowl    🥤 Drinks Tray    │
│                                                      │
└──────────────────────────────────────────────────────┘
        ▲                ▲                 ▲
        │                │                 │
   Chef Marco       Chef Priya        Chef Alex
   (makes pizza)    (makes salad)     (pours drinks)
```

Each chef ONLY touches their own area:
- Marco only puts pizzas on the Pizza Tray
- Priya only puts salad in the Salad Bowl
- Alex only puts drinks on the Drinks Tray

**No conflict, right?** Correct. But the kitchen manager (LangGraph) has a strict rule:

> "I don't care WHO puts WHAT WHERE. All I know is that 3 people are working at the same counter at the same time. I NEED a rule for EVERY item on that counter, or I refuse to open the kitchen."

The manager doesn't analyze which chef touches which tray. The manager just sees:

```
3 parallel workers + 1 shared counter = I NEED MERGE RULES FOR EVERYTHING
```

So you declare rules (reducers), even for trays that only one chef uses.

The reducers are like seatbelts — you need them even for short drives where nothing goes wrong, because the car (LangGraph) won't start without them.

#### When WOULD `_merge_lists` actually combine things?

If in a future v2 you added a **second JIRA agent** — one for security tickets, one for infrastructure tickets:

```
remediation ──→ jira_security_agent   → writes jira_tickets: [sec_ticket_1]
           ──→ jira_infra_agent       → writes jira_tickets: [infra_ticket_1, infra_ticket_2]
```

NOW two agents write to the same `jira_tickets` list. The `_merge_lists` reducer combines them:

```
[sec_ticket_1] + [infra_ticket_1, infra_ticket_2] = [sec_ticket_1, infra_ticket_1, infra_ticket_2]
```

Without the reducer, one would overwrite the other and you'd lose tickets.

---

### 8.4 Why don't `raw_logs` and `file_name` need reducers?

Because **no agent ever writes to them**. Look at what every agent returns:

```python
# log_classifier returns:
{"log_entries": [...], "current_agent": "log_classifier"}

# remediation returns:
{"issues": [...], "current_agent": "remediation"}

# cookbook returns:
{"cookbook": "...", "current_agent": "cookbook"}

# jira_ticket returns:
{"jira_tickets": [...], "current_agent": "jira_ticket"}

# notification returns:
{"notification": {...}, "current_agent": "notification"}
```

Not a single agent returns `raw_logs` or `file_name`. They only **read** those values:

```python
# log_classifier.py line 124 — reads raw_logs, never writes it back
raw_logs: str = state["raw_logs"]
```

Back to the pizza kitchen: the **Order Slip** (`raw_logs`, `file_name`) is placed on the counter at the start by the customer. Every chef reads it to know what to make, but **nobody writes on it or replaces it**. It just sits there untouched.

LangGraph only needs merge rules for things that **could be written to** during parallel execution. The order slip is read-only, so no rule needed.

```python
class PipelineState(TypedDict):
    raw_logs: str                              # ← read-only input, no reducer needed
    file_name: str                             # ← read-only input, no reducer needed
    log_entries: Annotated[list, _merge_lists]  # ← agents write here, needs reducer
    issues: Annotated[list, _merge_lists]       # ← agents write here, needs reducer
    cookbook: Annotated[str, _last_value]        # ← agents write here, needs reducer
    ...
```

---

### 8.5 How does the shared state get created, updated, and merged?

Let's trace the entire lifecycle of the state object through `graph.py`.

#### Step 1: State is Born (`graph.py` lines 151–161)

```python
initial_state = {
    "raw_logs": raw_logs,          # "2026-02-13 ERROR [auth] Login failed..."
    "file_name": file_name,         # "microservices_mixed.log"
    "log_entries": [],              # empty — Agent 1 will fill this
    "issues": [],                   # empty — Agent 2 will fill this
    "cookbook": "",                  # empty — Agent 3 will fill this
    "jira_tickets": [],             # empty — Agent 4 will fill this
    "notification": None,           # empty — Agent 5 will fill this
    "current_agent": "",
    "error": "",
}
```

This is just a plain Python dictionary. Nothing special yet. It's handed to LangGraph:

```python
result = compiled.invoke(initial_state)  # line 163
```

At this moment, LangGraph takes ownership of this dict. From now on, **LangGraph controls who sees what and when**.

#### Step 2: Agent 1 Reads and Writes — Log Classifier

LangGraph passes the **full state** to the first node. Inside `log_classifier.run()`, the agent **reads** from state:

```python
raw_logs: str = state["raw_logs"]  # reads the raw log text
```

Then it **returns only what it changed** (NOT the full state):

```python
return {"log_entries": [e.model_dump() for e in entries], "current_agent": "log_classifier"}
```

LangGraph receives this partial dict and **merges it into the full state**:

```
BEFORE merge:                          RETURNED by agent:
┌─────────────────────────────┐       ┌──────────────────────────────────┐
│ raw_logs: "2026-02..."      │       │ log_entries: [{line_number: 1,   │
│ file_name: "micro..."       │       │   level: "ERROR", ...}, ...]     │
│ log_entries: []        ◄────┼───────│ current_agent: "log_classifier"  │
│ issues: []                  │       └──────────────────────────────────┘
│ cookbook: ""                 │
│ jira_tickets: []            │
│ notification: None          │
│ current_agent: ""      ◄────┼───── updated
│ error: ""                   │
└─────────────────────────────┘

AFTER merge:
┌─────────────────────────────────┐
│ log_entries: [{...}, {...}, ...] │ ✅ updated
│ current_agent: "log_classifier"  │ ✅ updated
│ everything else: unchanged       │
└─────────────────────────────────┘
```

**Key insight**: Agents return **only the fields they changed**. LangGraph merges them into the existing state. Unchanged fields carry forward automatically.

#### Step 3: Agent 2 Reads Agent 1's Output — Remediation

LangGraph passes the **updated state** (now containing `log_entries`) to the next node. Inside `remediation.run()`, the agent **reads what Agent 1 wrote**:

```python
log_entries = state.get("log_entries", [])  # reads the entries Agent 1 produced
```

Then returns its own partial update:

```python
return {"issues": [...], "current_agent": "remediation"}
```

```
State after Agent 2 merge:
┌───────────────────────────────────────────┐
│ raw_logs: "2026-02..."                    │  (original)
│ file_name: "micro..."                     │  (original)
│ log_entries: [{...}, {...}, ...]           │  (from Agent 1)
│ issues: [{severity: "CRITICAL", ...}, ...]│  ✅ NEW from Agent 2
│ cookbook: ""                               │  (still empty)
│ jira_tickets: []                          │  (still empty)
│ notification: None                        │  (still empty)
│ current_agent: "remediation"              │  ✅ updated
└───────────────────────────────────────────┘
```

#### Step 4: The Parallel Fan-Out — Where Reducers Matter

LangGraph sends **a copy of the same state** to 3 agents simultaneously:

```
                    ┌─────────────────────────────────────┐
                    │        STATE (after Agent 2)         │
                    │  raw_logs, log_entries, issues, ...  │
                    └──────────┬──────────┬──────────┬─────┘
                               │          │          │
            ┌──────────────────┘          │          └──────────────────┐
            ▼                             ▼                            ▼
     Agent 3 (cookbook)          Agent 4 (jira_ticket)        Agent 5 (notification)
     reads: issues              reads: issues                reads: issues, cookbook
     returns:                   returns:                     returns:
     {                          {                            {
       "cookbook": "# Run...",     "jira_tickets": [...],       "notification": {...},
       "current_agent":           "current_agent":             "current_agent":
         "cookbook"                  "jira_ticket"                "notification"
     }                          }                            }
```

Now LangGraph has **3 partial updates**. It applies the reducers:

```
Field: cookbook
  Current: ""
  Agent 3 returns: "# Remediation Cookbook..."
  Agent 4 returns: (nothing for this field)
  Agent 5 returns: (nothing for this field)
  Reducer _last_value → "# Remediation Cookbook..."  ✅

Field: jira_tickets
  Current: []
  Agent 3 returns: (nothing for this field)
  Agent 4 returns: [ticket1, ticket2]
  Agent 5 returns: (nothing for this field)
  Reducer _merge_lists: [] + [ticket1, ticket2] → [ticket1, ticket2]  ✅

Field: notification
  Current: None
  Agent 3 returns: (nothing for this field)
  Agent 4 returns: (nothing for this field)
  Agent 5 returns: {summary: "...", sent: true}
  Reducer _last_value → {summary: "...", sent: true}  ✅

Field: current_agent
  Current: "remediation"
  Agent 3 returns: "cookbook"
  Agent 4 returns: "jira_ticket"
  Agent 5 returns: "notification"
  Reducer _last_value → "notification" (whichever finishes last wins)
```

#### Step 5: Final State Returned (`graph.py` line 163)

```python
result = compiled.invoke(initial_state)  # returns the fully populated state
```

```
Final state (what "result" contains):
┌───────────────────────────────────────────────────────┐
│ raw_logs: "2026-02-13 ERROR [auth] Login failed..."   │  (original input)
│ file_name: "microservices_mixed.log"                  │  (original input)
│ log_entries: [{...}, {...}, {...}, ...]                │  (Agent 1 wrote)
│ issues: [{severity: "CRITICAL", ...}, ...]            │  (Agent 2 wrote)
│ cookbook: "# Incident Remediation Cookbook\n..."        │  (Agent 3 wrote)
│ jira_tickets: [{summary: "OOM Kill", ...}, ...]       │  (Agent 4 wrote)
│ notification: {summary: "...", sent: true, ...}       │  (Agent 5 wrote)
│ current_agent: "notification"                         │  (last agent to finish)
│ error: ""                                             │  (no errors)
└───────────────────────────────────────────────────────┘
```

This dict is then handed to `app.py` which displays it across the 5 tabs.

#### The Complete Journey

```
initial_state (empty)
       │
       │  compiled.invoke()
       ▼
  ┌─────────┐     reads: raw_logs
  │ Agent 1  │──── writes: log_entries ──────────────────┐
  └─────────┘                                            │
       │                                            merge into state
       ▼                                                 │
  ┌─────────┐     reads: log_entries                     │
  │ Agent 2  │──── writes: issues ───────────────────────┤
  └─────────┘                                            │
       │                                            merge into state
       ├────────────────┬────────────────┐               │
       ▼                ▼                ▼               │
  ┌─────────┐     ┌─────────┐     ┌─────────┐          │
  │ Agent 3  │     │ Agent 4  │     │ Agent 5  │          │
  │writes:   │     │writes:   │     │writes:   │          │
  │cookbook   │     │jira_     │     │notifi-   │          │
  │          │     │tickets   │     │cation    │          │
  └────┬─────┘     └────┬─────┘     └────┬─────┘          │
       │                │                │               │
       └────────────────┴────────────────┘               │
                        │                           merge using
                        │                           REDUCERS
                        ▼                                │
                  final state ◄──────────────────────────┘
                        │
                        ▼
                 returned to app.py
```

The state is just a dictionary that gets **progressively enriched** as it passes through each agent. LangGraph is the traffic controller — it decides which agent gets the state, collects their partial updates, merges them using the reducers, and passes the enriched state to the next agent.

---

*This documentation was generated for the DevOps Incident Analysis Suite project to provide a complete, beginner-friendly explanation of the entire codebase.*
