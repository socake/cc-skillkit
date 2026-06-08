# ops-session — fill-in templates

Copy the card you need. Keep cards terse; evidence is the point, not prose.

---

## plan.md

```markdown
# <topic> — plan

## Prior burns
<pasted from past lessons / long-term notes; "(none found)" if clean>

## Background
<the user's ask, verbatim + your restatement to confirm understanding>

## Acceptance criteria (must be verifiable)
- [ ] <hard signal 1 — e.g. replica min/max = 5/20 and deploy is synced/healthy>
- [ ] <hard signal 2 — e.g. no auth errors in the 5 min after the change>

## Subtasks
1. <subtask>
2. <subtask>

## Known risks & rollback
- Risk: <…>  →  Rollback: <exact command / restore-from-backup path>
```

---

## Root-cause card (rootcause.md)

```markdown
## RC-001  <one-line symptom or claim>
- Time            : YYYY-MM-DD HH:MM
- Hypothesis      : <one line>
- Counter-hypothesis: <≥1 rival explanation — mandatory>
- Evidence (hard only):
    [+] <supports: file:line / command+output / config key / metric value>
    [-] <what the counter can't explain, or evidence against it>
- Unruled-out     : <paths not yet checked>
- Strength        : weak | medium | strong
- Next            : <gather more evidence | proceed to Action>
```

Strength: `strong` = ≥2 independent hard items + counter falsified + nothing
unruled-out. `medium` = 1 hard item + counter de-risked + 1–2 unruled-out.
`weak` = keyword guess / analogy / counter not considered / many unruled-out.
**Weak blocks all writes.**

---

## Action line (actions.log)

```
YYYY-MM-DD HH:MM | RC-XXX | <command summary> | autonomy=manual|semi|auto
```

A write with no `RC-XXX` is out of bounds. Back up mutable state to `backups/`
before the change.

---

## Verify card (verify.md)

```markdown
## V-001  verify RC-XXX resolved
- Method          : <exact command / check>
- Expected        : <specific output / state>
- Actual          : <pasted command + output>
- Verdict         : pass | fail | partial | skipped
- On failure      : <re-diagnose RC-XXX | escalate to user>
- skip_reason     : <only if skipped — why now, with hard evidence>
- resume_condition: <only if skipped — what must be true to return, and who triggers>
```

Re-running the same "successful" command is **not** verification. A failed verify
downgrades the card and sends you back to RootCause.

---

## Lesson card (lessons.md)

**Short form** (investigation / routine, 1 field):

```markdown
## L-001  <rule>
- Why: <one line>
```

**Full form** (troubleshoot / migration / prod-change, 6 fields):

```markdown
## L-001  <one-line, actionable rule>
- Misdiagnosis    : <how you read it at the time>
- Real cause      : <what it actually was>
- Misread signal  : <took X for Y because Z>
- Future rule     : <next time you hit <trigger>, first <action>; don't <prohibition>>
- Related cards   : RC-XXX, RC-XXX
- Target note     : <which long-term note to merge into, or "do not persist">
```

Lesson-title writing — three rules, with examples:

| Bad | Better | Why |
|---|---|---|
| "remember to verify" | "after a write, verify independently (grep status / read log / check metric); never re-run the same command as proof" | says how, removes ambiguity |
| "check docs first" | "for config questions, fetch the official docs to confirm field name + type before advising" | names the trigger scene |
| "be careful with deletes" | "before any delete, back up the target to backups/ and confirm with the user even on auto tier" | names the prohibition |

Name the **trigger** ("when X"), the **action** ("first do Y"), and the
**prohibition** ("don't Z").

---

## README.md (wrap-up)

```markdown
# <topic>

> Started : YYYY-MM-DD HH:MM:SS UTC
> Ended   : <filled at end>
> Status  : in progress | done | done (with leftovers)
> Dir     : <your-archive-dir>/YYYY-MM-DD-<topic>/
> Kind    : prod-change | troubleshoot | migration | routine | investigation
> Autonomy: manual | semi | auto

## Background
<from plan.md>

## Acceptance
<end: each plan.md checkbox vs actual; e.g. "5/5 static checks pass VR-1..4,7;
VR-5/6 skipped, see V-002">

## Root-cause history
<one line per strong card: RC-NNN [conclusion] strength=strong, evidence V-XXX / file:line>

## Change list
<from actions.log, grouped by tool>

## No-RC actions (out-of-bounds audit)
<writes with no card reference; "(none)" if clean>

## Verification
<from verify.md; skipped items list skip_reason + resume_condition>

## Lessons
<from lessons.md; note which long-term note each merged into>

## Rollback
<from actions.log + backups/>

## Leftovers
<- item: … | trigger: … | est. effort: … | how-to-resume: …>

## Linked notes
<long-term notes written this session, if any>
```
