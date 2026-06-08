# task-kickoff — templates

Copy and adapt. Paths use `<your-plans-dir>` etc. — substitute roots you control.

---

## 1. Long-task plan (`<your-plans-dir>/<date>-<topic>.md`)

```markdown
# <one-line goal>

> Created: YYYY-MM-DD
> Status : draft | in review | executing | done | abandoned
> Links  : archive dir / pipeline / PR / notes

## Goal
<one line, independently verifiable>

## Blast radius
- Repos      : repo-a / repo-b
- Services   : svc-x / svc-y
- Environments: dev / staging / prod
- Clusters   : cluster-a / cluster-b
- Downstream : who/what is affected

## Known risks & past burns
<front-loaded, not "later if there's time">
1. <risk>: mitigation / fallback
2. <risk>: …

## Acceptance (3–5, independently verifiable)
- [ ] <metric / command / observable>
- [ ] …

## Steps
1. <step>
2. <step>

## Rollback
```bash
# if step X fails
<undo / revert / restore-from-backup / re-sync previous version>
```

## Resume anchor
- Current step : <where>
- Committed    : <hash>
- Archived     : <archive path>
- Dangling     : <TODO>
```

---

## 2. Kickoff checklist (5-minute open)

```markdown
# Kickoff — <topic>

## Sizing
- [ ] Scale: single query / medium / long
- [ ] Touches prod writes: yes / no
- [ ] Multi-service / multi-cluster: yes / no

## Setup
- [ ] Task list created
- [ ] If prod write: ops-session started
- [ ] If long task: plan file written
- [ ] Relevant service/config/runbook read (not pre-loaded)
- [ ] Risks & burns front-loaded
- [ ] Acceptance aligned with the user

## HITL gates
- [ ] Plan awaiting approval
- [ ] Prod write awaiting confirmation (command shown)
- [ ] Root-cause call has ≥2 candidates
- [ ] Diff shown before commit/PR

## Stop-loss
- [ ] Two-failure stop line noted
- [ ] ≥2 distinct candidate approaches listed (avoid single-point trial-and-error)
```

---

## 3. Verification report

```markdown
# Verification — <topic>

> Run: YYYY-MM-DD HH:MM UTC

## Level 1 — self-verify
| Check | Command / method | Result |
|---|---|---|
| lint | <cmd> | pass / fail |
| types / build | <cmd> | pass / fail |
| unit tests | <cmd> | pass / fail |
| dry-run / build | <cmd> | pass / fail |

## Level 2 — end-to-end
| Path | Command / observable | Result |
|---|---|---|
| <happy path 1> | <curl / log / metric> | pass / fail |

## Level 3 — cold review (major changes)
- Reviewer session: <triggered? id or N/A>
- Findings        : <summary>
- Disposition     : <accepted / clarified / fixed>

## Acceptance (vs plan)
- [x] criterion 1 — pass
- [ ] criterion 2 — partial, <reason>

## Dangling / follow-up
- <issue>
```

---

## 4. Candidate causes (root-cause HITL gate)

```markdown
# Candidate causes: <problem>

## Symptom
<what you observed>

## Candidates (by probability)

### 1 (most likely): <hypothesis>
- Evidence : <log / config / state>
- Counter  : <evidence against; "none found" if none>
- How to verify: <independent check>

### 2: <hypothesis>
- Evidence / Counter / How to verify

### 3 (low prob, rule out): <hypothesis>

## Already excluded
- ~~<intuitive guess>~~ — ruled out by <evidence>

## Awaiting user
- Fix candidate 1, or run a verification first?
```

---

## 5. Cold-review trigger

```markdown
# Trigger a cold review?

≥2 boxes → trigger:
- [ ] 5+ files or 200+ lines changed
- [ ] Prod-critical path (auth / payments / ingress / data migration)
- [ ] Shared script / tool / common lib
- [ ] Cross-repo refactor
- [ ] User uneasy / "might have missed something"
- [ ] A domain you haven't worked in before

## How
1. Writer session finishes, commits/pushes.
2. Fresh session or sub-agent as cold reviewer:
   "You're a cold-context reviewer. Independently review this change:
    - repo: <repo>
    - PR / commit: <url or hash>
    - context: <plan path>
    Focus on: <3 concerns>. Don't infer the author's intent — check whether the
    diff and plan align."
3. Writer processes the findings.
```
