# Project Instructions

## Required Workflow for New Features / Projects

Before writing any code, you MUST follow this sequence using the skills in `.claude/skills/`:

1. **`/create-prd`** — Generate a Product Requirements Document first. Ask clarifying questions. Save to `/tasks/prd-[feature-name].md`.
2. **`/generate-tasks`** — Break the PRD into actionable implementation tasks. Save to `/tasks/tasks-[feature-name].md`. Wait for user to say "Go" before generating sub-tasks.
3. **`/vibe-check`** — Review the plan for over-engineering before coding. Save findings to `/tasks/vibe-check-[feature-name].md`.
4. **Only then** — Start implementing code, following the approved task list.

Do NOT skip these steps. Do NOT start coding before the PRD is approved and tasks are generated.

## Project Structure

- `/tasks/` — PRDs, task lists, and vibe-check reports
- `/devops_incident_suite/` — Main application code
- `/.claude/skills/` — Skill definitions (create-prd, generate-tasks, vibe-check)

## Environment

- Python 3.11+ with venv at `/venv/`
- `.env` at project root contains API keys (OpenRouter, Slack webhook, etc.)
- Default LLM provider: OpenRouter via `OPENROUTER_API_KEY`
- Slack webhook sends to `#all-langgraphprojectfeb2026`

## Conventions

- Use Pydantic models for structured data between components
- Keep agents as simple functions — no base classes or frameworks
- Prefer regex/deterministic parsing before falling back to LLM calls
- Post-process LLM output in code when formatting must be exact
