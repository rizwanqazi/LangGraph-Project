---
name: generate-tasks
description: Break down a PRD into actionable implementation tasks
---

# Rule: Generating a Task List from User Requirements

## Goal

The objective is to guide an AI assistant in creating detailed, step-by-step task lists in Markdown format based on user requirements, feature requests, or existing documentation to guide developer implementation.

## Output

- **Format:** Markdown (`.md`)
- **Location:** `/tasks/`
- **Filename:** `tasks-[feature-name].md` (e.g., `tasks-user-profile-editing.md`)

## Process

1. **Receive Requirements:** User provides feature request, task description, or points to existing documentation
2. **Analyze Requirements:** AI analyzes functional requirements, user needs, and implementation scope
3. **Phase 1: Generate Parent Tasks:** Create file and generate main, high-level tasks. "Always include task 0.0 'Create feature branch' as the first task, unless the user specifically requests not to create a branch." Present tasks without sub-tasks and wait for user confirmation
4. **Wait for Confirmation:** Pause and wait for user to respond with "Go"
5. **Phase 2: Generate Sub-Tasks:** Break down each parent task into smaller, actionable sub-tasks
6. **Identify Relevant Files:** Based on tasks and requirements, identify potential files that will need creation or modification
7. **Generate Final Output:** Combine parent tasks, sub-tasks, relevant files, and notes into final Markdown structure
8. **Save Task List:** Save document in `/tasks/` directory with filename `tasks-[feature-name].md`

## Output Format

The generated task list must follow this structure:

```
## Relevant Files

- `path/to/potential/file1.ts` - Brief description
- `path/to/file1.test.ts` - Unit tests for `file1.ts`

### Notes

- Unit tests should be placed alongside code files
- Use `npx jest [optional/path/to/test/file]` to run tests

## Instructions for Completing Tasks

**IMPORTANT:** Check off each task by changing `- [ ]` to `- [x]` after completing.

## Tasks

- [ ] 0.0 Create feature branch
  - [ ] 0.1 Create and checkout new branch
- [ ] 1.0 Parent Task Title
  - [ ] 1.1 [Sub-task description]
  - [ ] 1.2 [Sub-task description]
```

## Interaction Model

The process requires an explicit pause after generating parent tasks to obtain user confirmation ("Go") before proceeding to detailed sub-task generation, ensuring the high-level plan aligns with expectations.

## Target Audience

Assume the primary reader is a junior developer who will implement the feature.
