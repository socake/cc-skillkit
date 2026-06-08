# Good vs bad PR descriptions

Concrete contrasts. The pattern: bad descriptions restate *what files changed* and
hide risk; good ones explain *why*, surface the soft spots, and steer the review.

---

## Example 1 — a behavior change

### Weak

> Updated the API client and some configs. Added tests. Should be good.

Tells the reviewer nothing they can't get from `git diff --stat`, and worse —
"should be good" is an unverified claim dressed as reassurance.

### Strong

> **Summary** — Add bounded retry-with-backoff to the upstream client so transient
> 5xx/timeouts no longer surface as user-facing errors.
>
> **Motivation** — ~0.3% of requests fail on brief upstream blips that succeed on
> immediate retry. Today we pass the error straight through.
>
> **Changes** — Retry wrapper (3 attempts, exponential backoff + jitter, 2s cap);
> only idempotent GETs are retried; retries are surfaced as a metric.
>
> **Risk & rollback** — Adds up to ~2s latency on the unhappy path. Behind config
> `client.retry.enabled` (default off in prod for this PR); roll back by flag, no
> deploy needed.
>
> **Reviewer notes** — Focus on `client.go` retry loop: is the
> idempotency guard correct? `config.go` / test files are mechanical.

Why it's better: intent-grouped, names the load-bearing file, states the latency
tradeoff *and* a flag-based rollback, and is honest that only GETs are covered.

---

## Example 2 — being honest about gaps

### Weak

> Fully tested, works end to end.

A blanket claim no reviewer can trust and you probably can't back. If it's wrong,
it burns trust on every future PR.

### Strong

> **Testing** — Unit tests for the parser cover valid input + the three malformed
> cases from the bug. Manually ran the import on a staging copy of prod data (12k
> rows) — clean.
> **Not covered:** concurrent imports (single-threaded path only); very large files
> (>1M rows) untested — follow-up tracked. No load test.

Naming what you *didn't* test is a feature: it tells the reviewer exactly where to
apply extra scrutiny, and it's accurate.

---

## Example 3 — breaking changes

### Weak

> Refactored the config loading.

Buries a breaking change in an innocent word. Reviewers (and downstream users)
discover it when something breaks.

### Strong

> **⚠ Breaking change** — `timeout` config key is renamed `timeout_ms` and is now
> milliseconds (was seconds). Existing configs with `timeout: 30` must become
> `timeout_ms: 30000`. No automatic migration; deploys with the old key now fail
> fast at startup with a clear error (chosen over silently misinterpreting the
> value).

Why it's better: states old→new, the unit trap, who must act, and the deliberate
fail-loud decision so a reviewer can challenge it.

---

## Phrasing risk and rollback honestly

- **Name the blast radius.** "Affects all write paths" vs "isolated to the export
  job" changes how hard the reviewer looks.
- **Distinguish reversible from not.** A code change reverts cleanly; a data
  migration or backfill may not. Say which, and give the down path if one exists.
- **Prefer a real rollback lever.** "Revert the commit", "flip flag X off",
  "run migration down" — concrete and testable beats "we can roll back if needed".
- **If there's no clean rollback, say so.** That's exactly the line a reviewer
  needs to see before approving.

## Smells to delete on sight

- "various improvements", "minor changes", "cleanup" with no specifics
- "as discussed" / "per the meeting" — context the reviewer doesn't have
- restating the file list the diff already shows
- "should work", "fully tested", "no risk" — unverifiable confidence
- an empty **Risk** section on a change that obviously has risk
