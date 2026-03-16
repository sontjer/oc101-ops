# Promotion Matrix

## Layer Decision Table

| Signal | Session Memory | Rules Layer | Skill Layer | MEMORY.md |
|---|---|---|---|---|
| Time horizon | days-weeks | months+ | months+ | long-term |
| Reusability | low-medium | high | high | high |
| Scope | single run/track | global behavior constraints | repeated workflows | stable personal context |
| Volatility | high | low | low-medium | very low |

## Decision Heuristics

Promote to **Session Memory** when:
- needed for ongoing thread continuity
- likely to expire soon

Promote to **Rules Layer** when:
- behavior must be consistently enforced
- violation would cause repeated quality or safety issues

Promote to **Skill Layer** when:
- procedure has 3+ repeatable steps
- pattern appears across different topics/tasks
- templates/scripts can reduce repeated manual work

Promote to **MEMORY.md** when:
- preference or long-term context is user-stable
- useful across many future tasks

## Evidence Threshold

- Rules/Skill/MEMORY promotion default threshold: 2+ supporting occurrences
- Threshold can be bypassed only by explicit user instruction

## Canonical Promotion Record Template

```md
### <item title>
- Source: <session id / file>
- Target: <session-memory|rules|skill|MEMORY.md>
- Why: <one-line rationale>
- Change: <file path + summary>
```

## Anti-Patterns

- Turning raw chat transcript into MEMORY.md.
- Encoding temporary incidents as permanent rules.
- Creating a new skill when a short rule update is enough.
- Duplicating the same instruction across Rules and Skill without purpose split.

