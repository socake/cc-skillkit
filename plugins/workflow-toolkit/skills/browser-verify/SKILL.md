---
name: browser-verify
description: Use when you need to verify a frontend / gateway / end-to-end flow in a real browser instead of by hand — drive a containerized Chromium (Playwright over CDP) through the click path, capture console/network/screenshots, correlate the frontend symptoms with backend logs by trace id, and report a pass/fail conclusion with evidence. Triggers like "verify X in the browser", "e2e check X", "click through the UI for X".
---

# browser-verify

Drive a real browser through a click path, capture what happened (console, network,
screenshots), correlate it with backend logs by trace id, and return a **pass/fail
conclusion** — not a pile of artifacts. The point is to verify behavior the way a
user experiences it, and to attribute any failure to a concrete layer (frontend,
network, or backend) with one line of evidence. **Don't ask a human to click the UI.**

The reference setup is a containerized Chromium exposing the Chrome DevTools Protocol
(CDP), with a persistent profile so login state survives, plus Playwright (via MCP or
a Python fallback) to drive it. It runs wherever you can reach the CDP endpoint;
[references/cold-start.md](references/cold-start.md) brings it up from scratch on any
Linux host with Docker.

## When to use

- Verify a frontend/gateway/routing flow actually works end to end after a change.
- Reproduce a "works in my browser / fails in prod" symptom under controlled capture.
- Attribute a slow or failing user action across frontend ↔ network ↔ backend.

**When *not* to use:** unit/integration tests (use the test runner); pure backend API
checks (use `curl`); anything that needs no rendering. And never use it to push writes
into production on a user's behalf — see [Red lines](#red-lines).

## First: environment self-check

Run in order; **fix any failing step before continuing** — don't push through.
(`$CDP_PORT` defaults to 9222, `$BROWSER_DIR` is wherever the container repo lives.)

1. **Is the container running?**
   ```bash
   docker ps --filter name=browser --format '{{.Names}}\t{{.Status}}'
   ```
   - no output → cold start, see [references/cold-start.md](references/cold-start.md)
   - `Restarting` / `Exited` → `docker logs <name> --tail 50` to diagnose

2. **Is CDP reachable?**
   ```bash
   curl -sf "http://127.0.0.1:${CDP_PORT:-9222}/json/version" | head -3
   ```
   not reachable → [references/troubleshooting.md](references/troubleshooting.md), "CDP
   unreachable".

3. **Is Playwright wired up?** If you use the Playwright MCP server, confirm it's
   connected; otherwise fall back to driving CDP directly from Python with
   `connect_over_cdp("http://127.0.0.1:<port>")` (skeletons in `assets/scripts/`).

4. **How many tabs are open?**
   ```bash
   curl -s "http://127.0.0.1:${CDP_PORT:-9222}/json" \
     | python3 -c "import json,sys; d=json.load(sys.stdin); print('tabs=', len([x for x in d if x['type']=='page']))"
   ```
   If it's high (>6), run `python3 assets/scripts/gc.py --keep-url <url-to-keep>` first
   to avoid OOM.

## Resolve the goal

The user's goal may be a URL / a resource id / a feature description / a bug link.
Before turning it into a concrete click path, pin down three things:

1. **Entry point** — log in and navigate from the home page, or a deep link?
2. **Path** — list each click step (cap at ~5; if more, ask first).
3. **Pass/fail criterion** — HTTP 200 + a key DOM node present? a specific API field?
   no console errors? Be explicit.

If any is unclear, ask — **don't run blind**.

## Execute the e2e (standard steps)

Full version in [references/e2e-workflow.md](references/e2e-workflow.md); short form:

1. `connect_over_cdp("http://127.0.0.1:<port>")` to reuse the logged-in profile.
2. Register listeners (`page.on("response")`, `page.on("console")`,
   `page.on("pageerror")`) **before** navigating.
3. Stamp `window_before = utcnow()` before triggering the action.
4. `goto` / `click` through the path; screenshot each key node to a temp dir.
5. Pull an identifier from a response body/header (e.g. a `trace_id` / `request_id` /
   a resource id) to correlate with the backend.
6. Query the backend log store for that id over a small time window (your log backend
   — Loki / CloudWatch Logs / Elasticsearch / etc.; see e2e-workflow.md for the
   query shape).
7. Use the `trace_id` to line up frontend and backend timestamps → attribute latency
   / locate the error.

## Output format

**Rule: don't dump artifacts — give the conclusion.** Template:

```
PASS / FAIL: <one-line cause>

Evidence:
- Frontend: <URL>, path X→Y→Z, key DOM appeared ✓ / stuck at step N ✗
- Network:  N requests; 4xx/5xx: <list>; slow (>1s): <list>
- Backend:  trace_id=<id>, <2–3 lines of relevant log>
- Latency:  frontend T0 → backend received T1 → backend responded T2 → rendered T3;
            dominant segment = …

Appendix (on request):
- Screenshots: <temp path>/browser-verify-<topic>-{before,after,error}.png
- HAR: <temp path>/har-<ts>.json
- console / backend-log raw: <path>
```

## Red lines

- **Production writes** follow your project's change-control rules — show the action
  and wait for confirmation; never click "confirm" on a user's behalf.
- **Don't fabricate data** — reproduce with existing accounts/resources; don't write
  junk into a production system.
- **Expired login** (session cookie / id token) → have someone log in once through the
  container's noVNC view (`http://127.0.0.1:<NOVNC_PORT>`); the cookie persists into
  the mounted `profile/` directory and is reused next run.
- **CDP locality** — Chrome binds the debugging port to `127.0.0.1`. If the container
  is on a remote host, reach it over an SSH tunnel rather than exposing CDP publicly.

## References & assets

- Cold start on a fresh host: [references/cold-start.md](references/cold-start.md) +
  `assets/Dockerfile`, `assets/docker-compose.yml`, `assets/supervisord.conf`,
  `assets/entrypoint.sh`.
- Full e2e workflow: [references/e2e-workflow.md](references/e2e-workflow.md)
- Troubleshooting: [references/troubleshooting.md](references/troubleshooting.md)
- Scripts: `assets/scripts/{cdp_smoke.py, e2e_flow.py, capture_har.py, gc.py}`
