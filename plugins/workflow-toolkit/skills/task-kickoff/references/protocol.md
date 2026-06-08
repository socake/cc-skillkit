# task-kickoff — the five rules, expanded

Ordered by leverage. Each: why / how / edge cases / anti-patterns. Paths use
`<your-plans-dir>`, `<your-reports-dir>`, `<your-archive-dir>` — pick roots you
control and keep them consistent.

---

## Rule 1 — Plan / implement separation

### Why
Cross-vendor consensus (every serious coding agent has a plan mode): "planning while
implementing is the main cause of agent failure." Editing a plan before code is an
order of magnitude cheaper than correcting after.

### How
**Long task (>5 steps / multi-service / writes prod):**
1. Enter plan mode (or explicitly say "plan first, then act").
2. Write `<your-plans-dir>/<date>-<topic>.md`: goal (one line), blast radius
   (repos/services/environments/clusters), acceptance (3–5 independently
   verifiable), known risks + past burns, rollback commands.
3. Show the plan. Act only after the user says "go."

**Medium task (3–5 steps):** short plan inline (no file required); user reviews
before you start.

### Edge cases
- Single file read / one query: no plan.
- User says "just do it": skip the plan but still track the work.
- Emergency production firefight: stop the bleeding first, write the plan after,
  and archive it.

### Anti-patterns
- Thinking-while-typing: plan in your head, code already moving.
- A plan with "what" but no "how to verify" — no acceptance = no way to know when
  it's done.
- A plan that skips known risks — list the burns up front, not "later if there's time."

---

## Rule 2 — Externalize state

### Why
Context windows degrade as they fill (attention rot); recall drops well before the
window is full. Long tasks that rely on implicit session memory *will* drift.
Cross-session resume must be reconstructable from files.

### How

| Artifact | Purpose | Where |
|---|---|---|
| Task list | in-session progress | the built-in tool |
| Plan | how you'll do it | `<your-plans-dir>/<date>-<topic>.md` |
| Report | what you produced | `<your-reports-dir>/<date>-<topic>.md` |
| Issue log | dangling cross-session items | `<your-issues-dir>/<topic>.md` |
| Ops archive | substantive prod changes | `<your-archive-dir>/<date>-<topic>/` |
| Long-term notes | stable cross-session knowledge | your notes store |

Rhythm: write at each milestone (commit / archive together); before resuming, read
the plan + progress + recent `git log` instead of going on memory; archive partial
results as you go, not all at the end.

### Edge cases
- A small task that finishes in one session: the task list is enough; no files.

### Anti-patterns
- "I remember we said X" with no doc — guaranteed drift.
- Writing the *why* of a decision only in a commit message — commit context is
  narrow and future-you won't find it. Put it in the plan/report.

---

## Rule 3 — Stop after two failures

### Why
The trial-and-error loop is the most typical failure mode. Tell-tale sign: the
second attempt looks almost identical to the first. Patching an in-progress mess is
usually slower and dirtier than revert-refine-rerun.

### How
Second failure of the same approach → stop and report: what you tried, the verbatim
error, and **≥2** candidate hypotheses (not just one). Let the user decide: redirect
/ give more info / accept current state / `/clear` and restart. Don't try a third on
your own.

### Signals
- Same `grep`/`curl`/command tried ≥2 times with tweaked args.
- Explanations getting longer, output not improving.
- Fixing A surfaces B, fixing B surfaces C.
- Editing the same region of the same file over and over.

### Edge cases
- User explicitly says "try again" → follow the user.
- Network blip / rate limit / flaky API → retrying the same command is fine (that's
  not "retrying the same *approach*").

### Anti-patterns
- Stacking prompt onto an error ("this time add `--force`") — usually a new hole.
- "Almost there" optimism — the third try is often the biggest hole.
- Not telling the user the failure count — they can't judge when to step in.

---

## Rule 4 — Human-in-the-loop at four gates only

### Why
Stutter-stepping (approve every action) makes an agent unusable. Approve at the
leverage points; let the agent self-drive everything else.

### The four gates

| Gate | You provide | User does |
|---|---|---|
| Plan approval | plan + blast radius + acceptance + risks | approve / redirect |
| Before a write | the exact command (SQL / patch / diff / apply) | confirm "go" |
| Root-cause call | ≥2 candidate causes + evidence | judge the real cause |
| Before commit / PR | `git diff` + commit-message draft | review, then push |

### No approval needed
Read-only queries (GET / SELECT / read-only CLI), file reads, grep/find, temp-file
writes.

### Edge cases
- User pre-authorizes ("just run these next ones") — honor it, scoped to what they said.
- Emergency firefight: act first, archive after (mark "emergency").

### Anti-patterns
- Asking "should I run this?" on every read-only command — the user will tune you out.
- A prod write with no confirmation — a hard line.
- Treating a one-time authorization as unlimited — keep it scoped.

---

## Rule 5 — Multi-level verification

### Why
Even simple tasks carry a 5–10% baseline hallucination rate, hard to push under 2%.
Types, linters, and tests are the most reliable auto-checks. A cold-context review
catches far more than same-session self-review (the context is already biased).

### How
**Level 1 — self-verify after writing:** lint / test / type-check code; build or
dry-run manifests; `SELECT` to confirm affected rows before `UPDATE`/`DELETE`; read
back a changed config to confirm it took.

**Level 2 — end-to-end:** not just unit-green; run one full happy path; after a prod
write, confirm with a log / metric / request.

**Level 3 — cold review (major changes):** a fresh session/agent reviews the diff +
plan with no implementation bias. Trigger when: 5+ files or 200+ lines changed; a
prod-critical path; a shared script/tool/lib; a cross-repo refactor; or the user is
uneasy.

### Anti-patterns
- "It compiles, done" — compiling ≠ correct.
- "Tests pass" without checking which path they cover.
- Same-session self-review — the context is already polluted.

---

## Anti-pattern quick-reference

| Signal | Usual cause | Action |
|---|---|---|
| Explanations grow, no output | attention rot or wrong direction | stop, report; maybe `/clear` |
| Re-grepping the same thing | wrong path | ask the user for a pointer |
| Editing the same region repeatedly | wrong approach | step back to the plan |
| Third retry of one approach | broke Rule 3 | stop now |
| User says "no, it's X" twice | guessed instead of reading | go read the source |
| >10 steps, nothing archived | broke Rule 2 | write progress now |
| Prod write ran without confirmation | broke Rule 4 | apologize + report state |
| User mentions "next, also Y" and you grab it | didn't notice it may be a different track | ask: now, or just flagging it? |
| You ignored a protocol you just set up | written ≠ in working memory | make "self-check the protocol" a milestone |
