# e2e workflow: browser + backend logs, correlated

Everything to do in a single session: walk the UI, line up backend logs against the
frontend timestamps, and give a pass/fail conclusion.

## Backend log store

Use whatever your environment provides — Loki (`logcli`), CloudWatch Logs, an
Elasticsearch/Kibana cluster, or `kubectl logs`. What matters is that you can query by
**a correlation id over a time window**. Generic shape:

```
<log-query-tool> --env <environment> --grep '<id-or-pattern>' --since <window, e.g. 5m>
```

Keep a small table mapping your *environment names* → *target (context / log stream)*
locally; don't hardcode it here. The two facts that bite: (1) an environment's display
name may not match the underlying target, so confirm which one you're actually
querying; (2) start the window wider than you think (`5m`, then `30m`) — clock skew and
buffering hide events.

## Playwright MCP path (preferred)

When the Playwright MCP server is connected, drive it directly:

```python
# illustrative
mcp__playwright__browser_navigate(url="https://app.example.com/...")
mcp__playwright__browser_console_messages()
mcp__playwright__browser_network_requests()
mcp__playwright__browser_click(element="Login button", ref="...")
mcp__playwright__browser_take_screenshot(filename="/tmp/browser-verify-after-click.png")
mcp__playwright__browser_evaluate(function="() => window.__APP_STATE__")
```

## Python fallback (no MCP)

```python
from playwright.sync_api import sync_playwright
from datetime import datetime, timezone
import json

CDP = "http://127.0.0.1:9222"   # adjust port if needed

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0]            # reuse the logged-in profile
    page = ctx.new_page()

    network, console = [], []
    page.on("response", lambda r: network.append({
        "url": r.url, "status": r.status,
        "timing": r.request.timing if r.request else None,
    }))
    page.on("console", lambda m: console.append({
        "type": m.type, "text": m.text, "location": m.location,
    }))
    page.on("pageerror", lambda e: console.append({"type": "pageerror", "text": str(e)}))

    t0 = datetime.now(timezone.utc)
    page.goto("https://<target-url>", wait_until="networkidle", timeout=30_000)
    page.wait_for_selector("<key DOM selector>", timeout=10_000)
    t1 = datetime.now(timezone.utc)

    page.screenshot(path="/tmp/browser-verify-after.png", full_page=True)

    # pull a correlation id from a response (example)
    api = [r for r in network if "/api/<endpoint>" in r["url"]]
    corr_id = "..."   # parse it out of api

    open("/tmp/browser-verify-summary.json", "w").write(json.dumps({
        "t0": t0.isoformat(), "t1": t1.isoformat(),
        "duration_ms": (t1 - t0).total_seconds() * 1000,
        "network_count": len(network),
        "errors_4xx_5xx": [n for n in network if n["status"] >= 400],
        "console_errors": [c for c in console if c["type"] in ("error", "pageerror")],
        "corr_id": corr_id,
    }, indent=2, default=str))
```

A fuller version with a timing report is in `assets/scripts/e2e_flow.py`.

## Line up frontend & backend timestamps

With a correlation id + the frontend `t0`/`t1`:

```bash
# widen the backend window a minute or two each side
<log-query-tool> --env <environment> --grep 'corr_id=<id>' --since 5m | tee /tmp/backend.log

# a trace_id, if present, is more precise than a resource id
<log-query-tool> --env <environment> --grep 'trace_id=<id>' --since 5m
```

Then align the log timestamps to the frontend `t0`/`t1` and find:
- **gateway received − frontend t0** = network + queueing
- **handler finished − gateway received** = pure backend time
- **frontend t1 − handler finished** = response return + render

The largest segment is the bottleneck.

## Capture a HAR (for full request timing)

```bash
python3 assets/scripts/capture_har.py "https://app.example.com/<path>"
# writes /tmp/har-<ts>.json
```

Each entry carries
`startTime / domainLookupStart-End / connectStart-End / requestStart / responseStart /
responseEnd` — precise for separating browser queue wait vs main-thread blocking vs
real network time.
