# ops-session — directory, lifecycle & meta file

How a session is physically laid out and how it starts/ends. Paths use
`<your-archive-dir>` as the archive root — pick one you control (a common choice is
`~/ops-archive/`) and keep it consistent.

## Directory layout

```
<your-archive-dir>/
  YYYY-MM-DD-<topic-kebab>/
    README.md            wrap-up, filled at the end
    plan.md              background + acceptance + risks + rollback
    rootcause.md         RC-NNN evidence cards
    actions.log          one line per write op
    verify.md            V-NNN verification records
    lessons.md           L-NNN lessons (only when earned)
    backups/             pre-change exports (objects/config/rows)
    .session-meta.json   machine-readable session state
```

One topic per directory. Name the topic in `kebab-case`; the directory name carries
the date so sessions sort chronologically.

## Optional: per-session lock for parallel work

If you run multiple Claude Code sessions at once, isolate them with a per-session
lock so two sessions don't clobber a shared "current session" pointer:

- Lock file: `<your-archive-dir>/.session-<id>`, where `<id>` is
  `${CLAUDE_CODE_SESSION_ID}` (a Claude Code env var) or any unique token.
- On start: if a lock for this session already exists, refuse and ask the user to
  end it first.
- On end: remove the lock.
- A `status` view can list all live locks across sessions and flag stale ones.

This is optional scaffolding; a single-session workflow doesn't need it.

## Start

1. Resolve the session id (or skip if running solo). Take the lock if you use one.
2. Pick `kind` (prod-change / troubleshoot / migration / routine / investigation).
   If unspecified, infer from the topic and confirm: prod/cutover → prod-change or
   migration; "why is X broken" → troubleshoot; sweep/restart/sync → routine;
   read-only research → investigation.
3. Derive default `autonomy` from `kind` (see SKILL.md). Honor an explicit override.
4. Create the directory and seed the files above from `templates.md`.
5. Pre-load prior burns: grep past sessions' `lessons.md` and your long-term notes
   for the topic keywords; paste hits into the top of `plan.md`. ≥3 hits → warn the
   user this area has bitten before.
6. **Gate:** complete `plan.md`'s background + acceptance sections before opening any
   RC card. If the ask is fuzzy, write your interpretation and confirm with the user.

## Lifecycle actions

Run these as plain file edits (Read/Write/Edit) — no scripts required.

- **new card** — append `RC-NNN` to `rootcause.md` (NNN auto-increments). Never write
  only a hypothesis; the counter-hypothesis, evidence, and strength are mandatory.
- **action** `<RC-ID> <description>` — check the card is ≥ medium (refuse on weak),
  append a pre-declaration line to `actions.log`, show the command (always for
  manual/destructive; per tier otherwise), run it, append the result, then
  **immediately verify** — never finish an action without verifying.
- **verify** `<RC-ID|V-ID>` — write the record to `verify.md`. On failure: downgrade
  the card, draft a lesson stub, and decide between re-diagnosing and escalating.
- **status** — show this session (dir, kind, autonomy, active cards sorted by
  strength, action/verify/lesson counts) plus health signals: # weak cards, #
  unverified actions, # undigested lessons.

## End

1. Check for unfinished items: actions with no matching verify; active weak cards;
   skipped verifies missing `skip_reason`/`resume_condition`. If any exist, warn and
   make the user confirm "ending with leftovers."
2. Fill `README.md` from the template:
   - header: kind / autonomy / status filled for real
   - acceptance: count + ID range + any skips, mapped to `plan.md`
   - root-cause history: one line per strong card (ID + conclusion + strength +
     evidence pointer)
   - change list: grouped by tool (apply/patch/http/db/…)
   - no-RC actions: out-of-bounds audit (writes with no card reference)
   - verification summary (skipped items list `skip_reason` + `resume_condition`)
   - lessons (with which note each merged into)
   - rollback commands (inferred from `actions.log` + `backups/`)
   - leftovers (each with trigger / est. effort / how-to-resume)
3. Run the wrap-up self-check (the 6-item list in SKILL.md). Self-check failures
   don't block the end — they prompt you to patch the README before lessons reflow.
4. Reflow earned lessons to your long-term notes store, with the user confirming each.
5. Release the lock if you took one.

## .session-meta.json

```json
{
  "topic": "<kebab-case>",
  "start_ts": "YYYY-MM-DDTHH:MM:SSZ",
  "end_ts": null,
  "session_id": "<id or null>",
  "kind": "troubleshoot",
  "autonomy": "semi",
  "autonomy_overridden": false,
  "stats": {
    "rc_count": 0, "rc_weak_active": 0,
    "actions_count": 0, "actions_no_rc": 0,
    "verify_pass": 0, "verify_fail": 0,
    "lessons_count": 0
  }
}
```

Fill `stats` at end by scanning the files.
