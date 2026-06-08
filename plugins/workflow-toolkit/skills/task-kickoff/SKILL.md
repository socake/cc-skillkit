---
name: task-kickoff
description: Use at the start of a complex or long task — anything past ~5 tool calls, multi-service/multi-environment work, production writes, debugging with several hypotheses, cross-repo refactors, or resuming work across sessions. Sets up the session right: plan/implement separation, externalized state, human-in-the-loop only at high-leverage gates, stop-after-two-failures, and multi-level verification. Skip for single lookups or pure chat.
---

# task-kickoff

The opening protocol for human+AI collaboration on a long task. Most agent failures
happen in the first few minutes — planning and implementing at the same time, never
externalizing state, stutter-stepping the human on every action, or grinding the
same broken approach a third time. This skill front-loads the decisions that prevent
those.

## When to use

Fire if **any** holds:

- The user says "kickoff" / "let's start" / "spin this up" (or your own kickoff
  trigger).
- The task will take more than ~5 tool calls.
- It touches **production**, multiple clusters/environments, multiple services, or
  any write (deploy, apply, push, DB/config mutation).
- It's debugging/troubleshooting with several independent hypotheses to test.
- It's a cross-repo refactor.
- It resumes earlier work ("pick up yesterday's plan").

**Don't fire** for: a single query (one pod status, one log line, one file read),
pure chat, or a task already past an approved plan.

## The four opening moves

Run in order.

### 1. Track the work

If the task has ≥3 independently verifiable sub-results, spans environments, will
exceed ~5 tool calls, or includes reversible write steps — create a task list. One
item = one verifiable result, not one command.

### 2. Decide on a plan

| Size | Plan handling |
|---|---|
| single step / one file | no plan |
| medium (3–5 steps) | a short plan inline; let the user approve before you act |
| long (>5 steps / multi-service / writes prod) | enter plan mode; write `<your-plans-dir>/<date>-<topic>.md` with goal / blast radius / acceptance / risks / rollback |

**Ironclad:** don't *write* to prod before the plan is approved. Reading is fine.

### 3. Decide on an ops-session

If you're about to make a **substantive production change**, start an `ops-session`
(see the ops-session skill) so the change gets a Plan→RootCause→Action→Verify→Learn
trail with backup and rollback.

### 4. Load only what you need

Don't pre-load context. Read on demand: the specific service/config/runbook the task
touches, the glossary entry for a term you're unsure of, the prior report/plan for
resumed work. If you keep a personal reference library (coding standards, a
code-taste benchmark, past postmortems), **consult it on review/design tasks** —
and when you do, cite specifics (`file:line` + the reference), never a vague
"looks fine / looks off." This hook is optional; wire it to whatever library you keep.

## The five ironclad rules

Expanded in `references/protocol.md`.

1. **Plan / implement separation.** Planning while implementing is the #1 agent
   failure. Edit the plan before generating the work.
2. **Externalize state.** Plan files, progress notes, commits, and an ops archive
   beat implicit session memory — which decays as context fills.
3. **Stop after two failures.** Two similar failed attempts → stop and report (what
   you tried, the verbatim error, ≥2 candidate hypotheses). Don't try a third on
   your own unless the user asks.
4. **Human-in-the-loop at 4 gates only.** Plan approval / before a write / root-cause
   call / before commit. Don't stutter-step the human on read-only actions.
5. **Multi-level verification.** Self-verify after writing; for major changes, get a
   cold-context review (a fresh session/agent that only sees the diff + plan).

## Decision tree

```
user message
  │
  ├─ single query / one file?      → just do it, skip kickoff
  │
  ├─ prod write / DB write / config write?
  │    → start an ops-session
  │    → produce plan + blast radius + acceptance + rollback + risks
  │    → wait for "go" before writing
  │
  ├─ medium (3–5 steps)?
  │    → task list
  │    → short inline plan, user approves, then go
  │
  └─ long (>5 steps / multi-service / cross-repo)?
       → task list
       → plan mode + <your-plans-dir>/<topic>.md
       → checkpoint commits / archive
       → stop after two failures
       → cold review for major changes
```

## Anti-patterns (any one → stop and ask)

- A **third** retry of the same approach (even if the last two "almost worked").
- >10 steps into a long task with **no plan and no archive** — state has been lost.
- A **prod write with no explicit user confirmation**.
- **≥2 unrelated topics** piled into one session — time to split (see
  `references/multi-session.md`).
- The user **says "actually it's X" twice** — you're guessing instead of reading the
  source; go read it.
- The user mentions a *future/other-track* "next, also do Y" mid-task and you grab it
  — confirm whether it's this topic's next step or a different line before diving in.

## References

| File | Read when |
|---|---|
| `references/protocol.md` | you want the why/how/edge-cases behind a rule |
| `references/templates.md` | filling a plan, kickoff checklist, verification, candidate-cause, or cold-review trigger |
| `references/multi-session.md` | context switching, /clear vs /compact, running parallel sessions without crossing wires |
