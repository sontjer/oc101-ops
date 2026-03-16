---
name: session-memory-promotion
description: Promote completed OpenClaw/Codex session outcomes into durable knowledge layers. Use when the user wants to convert audited session results (done) into session memory updates, rule updates, skill updates, and long-term personal MEMORY.md entries in a repeatable workflow.
---

# Session Memory Promotion

Use this skill when the task is to standardize knowledge promotion from completed sessions into durable layers.

## When To Use

- The user asks to "梳理流程", "沉淀经验", "复盘并固化", or "把 done 会话升格为规则/技能/长期记忆".
- You have one or more finished sessions and need reproducible conversion into reusable artifacts.

## Inputs

- Source sessions marked as done.
- Existing rule files, skills, and `MEMORY.md` (if present).

## Output

- A promotion report with 4 sections:
  - Session Memory
  - Rules Layer
  - Skill Layer
  - Long-term Memory (`MEMORY.md`)
- Concrete file edits committed to repo (or a patch list if write is not allowed).

Read [references/promotion-matrix.md](references/promotion-matrix.md) for criteria and templates.

## Workflow

1. Collect done-session evidence.
2. Extract candidate knowledge atoms:
   - stable facts
   - reusable decisions
   - repeatable procedures
   - personal preferences
3. Score each atom with promotion matrix.
4. Promote atoms to the highest justified layer:
   - Session Memory: short-lived task context, run-specific continuity
   - Rules Layer: policy/guardrail, must-follow constraints
   - Skill Layer: reusable multi-step workflow, templates, scripts
   - `MEMORY.md`: long-lived personal preference or durable identity/context
5. De-duplicate:
   - reject near-duplicates
   - merge overlapping rules
   - keep one canonical skill path
6. Apply edits and run validation commands relevant to changed files.
7. Produce a compact report:
   - what was promoted
   - why this layer was chosen
   - what was intentionally not promoted

## Hard Rules

- Do not promote one-off incident details into rules or MEMORY.
- Prefer reversible edits in lower layers unless repetition evidence exists.
- Promotion to Rules or `MEMORY.md` needs explicit stability evidence from at least 2 occurrences or an explicit user directive.
- Skills must be procedural and reusable; do not create skills for a single session summary.

## Minimal Command Pattern

Use fast search first:

```bash
rg -n "done|复盘|结论|行动项|规则|偏好" sessions/ skills/ .
```

Then map files and edit only required targets.

## Report Format

- `Promoted`
- `Deferred`
- `Dropped`

For each promoted item include:
- source session(s)
- target layer
- reason in one line

