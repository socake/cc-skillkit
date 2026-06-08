---
name: ops-session
description: Use when running a structured operational change or investigation that deserves a paper trail — a production change, multi-step troubleshooting, a migration/upgrade, or a recurring routine op. Drives a Plan→RootCause→Action→Verify→Learn loop with an anti-hallucination root-cause card (weak evidence hard-blocks writes), autonomy tiers by task kind, evidence-pointer discipline (no bare assertions), and archive + backup + rollback. Not for one-off read-only lookups or a single obvious command.
---

# ops-session

A protocol for running an operational task as a *disciplined session* instead of a
stream of ad-hoc commands. The enemy is the confident wrong move: acting on a
guess, declaring success because a tool printed "ok", or leaving no trail to roll
back or learn from. This skill forces evidence before action, verification after
it, and a durable record either way.

It is **tool-agnostic** — the examples use `kubectl`/`helm`/SQL/HTTP, but the
discipline applies to any system you mutate.

## When to use

- A **production change** (infra, config, schema, traffic, DNS) — anything where a
  bad move costs you.
- **Multi-step troubleshooting** where the cause is unclear and you'll mutate state
  to fix it.
- A **migration / upgrade / cutover** spanning environments or systems.
- A **recurring routine op** (log sweep, rolling restart, config sync) you want
  executed consistently and logged.

**When *not* to use:** a single read-only lookup, one obvious command, or a pure
chat answer. Don't wrap trivial work in ceremony.

## Set up the session

Pick a **kind** (it sets your default autonomy — see below) and create a session
directory under an archive root you control (e.g. `<your-archive-dir>/YYYY-MM-DD-<topic>/`).
Seed it with the files in `references/templates.md`:

- `plan.md` — what and how
- `rootcause.md` — the evidence cards
- `actions.log` — every write you make
- `verify.md` — proof each write did what you intended
- `lessons.md` — what to do differently next time (only when earned)
- `README.md` — the wrap-up, filled at the end

Before writing the plan, **grep your past sessions and long-term notes** for the
topic keywords and paste any prior lessons into the top of `plan.md` as a
"prior burns" note. If three or more hits, slow down — this area has bitten you
before.

## The loop

Every operation goes through five phases; each writes to a file. A failed verify
or a refuted cause sends you back to RootCause.

```
  1. Plan       → plan.md
  2. RootCause  → rootcause.md   (evidence card per claim)
  3. Action     → actions.log    (every write, citing a card)
  4. Verify     → verify.md      (independent proof)
  5. Learn      → lessons.md      (only when you took a wrong turn)
       ↑________________________________│
       (verify fails / cause refuted → back to 2)
```

### 1. Plan

First thing, before any card: write `plan.md` with the task background (the user's
ask + your restatement to confirm you understood), **verifiable acceptance
criteria** (hard signals, not "looks fine"), the subtask breakdown, and known
risks + rollback. Never skip straight to acting. If the ask is fuzzy, write your
interpretation and ask before proceeding.

### 2. RootCause — the anti-hallucination core

Any judgment of the form **"this is because X"** (diagnosis) or **"this *is* X"**
(a factual assertion about the system) gets a card in `rootcause.md` *first*:

```
## RC-001  <one-line symptom or claim>
- Hypothesis      : <one line>
- Counter-hypothesis: <at least one rival explanation — mandatory>
- Evidence (hard only — no "I think / usually"):
    [+] <supports: file:line / command+output / config key / metric>
    [-] <what the counter-hypothesis can't explain, or evidence against it>
- Unruled-out     : <paths you haven't checked yet>
- Strength        : weak | medium | strong
- Next            : <gather more evidence | proceed to Action>
```

**Strength rubric:**

- `strong` = ≥2 independent hard evidence items **and** the counter-hypothesis is
  explicitly falsified **and** nothing left unruled-out.
- `medium` = 1 hard evidence item, counter can't be falsified but is lower
  probability, 1–2 unruled-out paths.
- `weak` = guessed from a log keyword / reasoned by analogy / counter not seriously
  considered / several unruled-out paths.

**Weak hard-blocks writes.** You may not run *any* write (apply/patch/delete,
non-GET HTTP, upgrade, push, config change, DML) off a weak card. Keep gathering
evidence or ask the user. If the user says "just try it," bump the card to medium
and tag it `user-authorized downgrade`.

The same card format covers both a *diagnosis* ("why did X break") and a plain
*assertion* ("the current replica count is N") — only the Hypothesis field differs.

### 3. Action — every write cites a card

Each write op appends one line to `actions.log`:

```
YYYY-MM-DD HH:MM | RC-XXX | <command summary> | autonomy=manual|semi|auto
```

A write with no RC reference is out of bounds and gets flagged at wrap-up.
Production changes: show the exact command and wait for confirmation.
Destructive commands (delete/drop/`rm -rf`/force-push/truncate) always confirm,
even on the `auto` tier. **Back up mutable state before you change it** (export the
current object/config/rows) so rollback is a restore, not a reconstruction.

### 4. Verify — prove it, independently

After each action append to `verify.md`: method, expected, actual (paste the
command + output), and verdict (pass / fail / partial / **skipped**). A failed
verify **downgrades** the card's strength and sends you back to RootCause.
**Re-running the same command that "succeeded" is not verification** — check the
state from a different angle (grep the status, read the log, query the metric).

If a verify must wait on something external (a merge, a sync, a pipeline, a user
action), don't silently skip it — record `skip_reason` and `resume_condition` so
whoever returns knows *when* to come back, not just that it was skipped.

### 5. Learn — only when you took a wrong turn

Lessons are for "next time, less detour" — **not** a complete log. If nothing went
wrong, write no card. Record a lesson only on a **strong signal**:

1. a strong/medium card got **refuted** (counter confirmed / verify failed / user
   corrected you);
2. the **user intervened** to say you misread something or went the wrong way;
3. an action was **rolled back**;
4. it took **≥3 cards** to find the cause (you wandered).

Don't write lessons for a fact you nailed first try (that's a finding — put it in
the README), or for skill self-improvements (edit this file instead). Card formats
(short / full) and the writing rules are in `references/templates.md`. The one
rule worth repeating: a lesson title must name the **trigger** ("when X happens"),
the **action** ("first do Y"), and the **prohibition** ("don't Z") — no vague
"be more careful."

## Autonomy by kind

The session `kind` sets how far you run on your own:

| kind | meaning | default autonomy | behavior |
|---|---|---|---|
| `prod-change` | production mutation | `manual` | confirm before every write |
| `troubleshoot` | diagnose + fix, any env | `semi` | strong card + clear verify → run; weak/unclear → stop |
| `migration` | cross-env/system cutover | `manual` | same as prod-change |
| `routine` | patterned, low-risk op | `auto` | run to acceptance; destructive cmds still confirm |
| `investigation` | read-only, no writes | `auto` | run freely |

The user can override at start. On `semi`/`auto`, **stop automatically** when: the
active card is weak; a destructive command is next; a verify failed; an exit code
is non-zero and unexpected; or you've hit the same failure pattern ≥3 times.

## Evidence-pointer discipline (no bare assertions)

Any conclusion you mark `strong` — in the README, the wrap-up message, anything you
tell the user — **must carry at least one pointer**: a `file:line`, the literal
command, a verify ID (`see V-001`), or a card+evidence ref (`see RC-002 [+] #2`).
Banned: "all aligned", "everything passed", "no issues" with nothing to grep. The
test: take a one-line conclusion, grep it against `verify.md`/`rootcause.md`/
`actions.log`; if it doesn't land on real evidence, it's unbacked — fix it.

## Critical-thinking checkpoint

Before writing each card, run this on yourself:

1. Am I keyword-matching instead of reasoning about cause? ("saw `timeout` → it's
   the network" — but timeout is also DNS, pool exhaustion, slow query…)
2. Is my counter-hypothesis real, or padding? ("maybe it's the network" doesn't
   count — be specific.)
3. Is my evidence just "the log says X so it's X"? (Logs mislead; verify from the
   cause side.)
4. Am I treating correlation as causation? (Co-occurrence ≠ one caused the other.)
5. Did I skip enumerating *all* known causes of this symptom before excluding?
6. Did I ask "why was this fine before and broken now?" (Change-tracking is the
   shortcut to a cause.)
7. Does my `strong` survive "if I'm wrong, what would the counter-evidence be?"

## Wrap up

At the end, fill `README.md` (template in `references/templates.md`) and run the
self-check before declaring done:

- [ ] Kind / autonomy / status filled in for real (no template placeholders).
- [ ] Every strong card has a one-line summary in the README — don't make the
      reader open `rootcause.md` to learn the key judgment.
- [ ] Acceptance section lists count + ID range; gaps in numbering are explained.
- [ ] Every strong conclusion carries an evidence pointer.
- [ ] Leftover items carry three fields: trigger / est. effort / how-to-resume.
- [ ] Skipped verifies carry `skip_reason` + `resume_condition`.

Then, if you earned any lessons, **write them back to your long-term memory / notes
store** — ask the user before persisting each one, fuzzy-match against existing
notes to update rather than duplicate, and keep your index in sync. The session
directory is the per-task record; your notes store is the cross-task memory that
pre-loads the *next* session's "prior burns."

## Hard rules

- No `plan.md` → no cards. No cards → no writes. No write without an RC reference.
- Weak card → no writes. Ever.
- "The tool said it worked" ≠ "the goal was met" — always verify independently, and
  never accept re-running the same command as the verification.
- Back up mutable state before mutating; keep a rollback for every change.
- A `strong` conclusion with no greppable evidence pointer is a violation.
- Don't silently skip a verify, and don't leave template placeholders in the README.
- Never persist a lesson to your notes store without the user's confirmation.

References: `references/session-layout.md` (directory + lifecycle + meta file),
`references/templates.md` (all fill-in cards and the README template).
