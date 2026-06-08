#!/usr/bin/env python3
"""Drive the logged-in container Chrome over CDP to open a URL and capture timing.

Usage:
  capture_har.py <url> [output.json]

The output records each request's full timing
(blocked/dns/connect/ssl/send/wait/receive), so you can separate browser queue /
main-thread blocking from real network time.
"""
import json
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9222"   # adjust port if needed


def main(url: str, out_path: Path) -> None:
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        # reuse the logged-in default context (persisted in /profile)
        ctx = browser.contexts[0] if browser.contexts else browser.new_context()

        events: list[dict] = []

        def on_request(req):
            events.append({
                "type": "request", "ts": time.time(),
                "url": req.url, "method": req.method,
                "headers": dict(req.headers), "resource_type": req.resource_type,
            })

        def on_response(resp):
            req = resp.request
            events.append({
                "type": "response", "ts": time.time(),
                "url": resp.url, "status": resp.status,
                "timing": req.timing,   # startTime, domainLookup*, connect*, request*, response*
                "headers": dict(resp.headers),
                "from_service_worker": resp.from_service_worker,
            })

        page = ctx.new_page()
        page.on("request", on_request)
        page.on("response", on_response)

        nav_start = time.time()
        page.goto(url, wait_until="networkidle", timeout=60000)
        nav_end = time.time()

        out_path.write_text(json.dumps({
            "url": url,
            "nav_start": nav_start, "nav_end": nav_end,
            "nav_duration_s": nav_end - nav_start,
            "events": events,
        }, indent=2, default=str))

        print(f"navigation: {nav_end - nav_start:.2f}s")
        print(f"events: {len(events)}")
        print(f"saved: {out_path}")
        browser.close()   # leaves the tab for noVNC viewing


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    url = sys.argv[1]
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(f"/tmp/har-{int(time.time())}.json")
    main(url, out)
