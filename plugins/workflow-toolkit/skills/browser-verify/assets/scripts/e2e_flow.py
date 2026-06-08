#!/usr/bin/env python3
"""e2e: open a target URL, record frontend network/console + a UTC time window for
backend log correlation.

Usage:
  BASE_URL=https://app.example.com python3 scripts/e2e_flow.py /some/path
  python3 scripts/e2e_flow.py https://app.example.com/some/path

Adjust the wait selectors / id-extraction to your app. The script is deliberately
generic: it captures timing, console errors, 4xx/5xx, and prints the UTC window to
feed into your log-query tool.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

CDP = os.environ.get("CDP", "http://127.0.0.1:9222")
BASE = os.environ.get("BASE_URL", "")
OUT = Path(os.environ.get("OUT_DIR", "/tmp/browser-verify"))
OUT.mkdir(parents=True, exist_ok=True)


def main():
    if len(sys.argv) < 2:
        print("need a path or full URL", file=sys.stderr)
        return 2
    arg = sys.argv[1]
    url = arg if arg.startswith("http") else BASE.rstrip("/") + arg
    if not url.startswith("http"):
        print("set BASE_URL or pass a full URL", file=sys.stderr)
        return 2

    ts = int(time.time())
    report = {"url": url, "ts": ts, "start_iso": datetime.now(timezone.utc).isoformat()}

    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        ctx = browser.contexts[0]
        page = ctx.new_page()

        responses, console_msgs = [], []
        page.on("response", lambda r: responses.append({
            "url": r.url, "status": r.status,
            "method": r.request.method, "resource_type": r.request.resource_type,
        }))
        page.on("console", lambda m: console_msgs.append({"type": m.type, "text": m.text}))
        page.on("pageerror", lambda e: console_msgs.append({"type": "pageerror", "text": str(e)}))

        t0 = time.time()
        report["window_before_iso"] = datetime.now(timezone.utc).isoformat()
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        t_dcl = time.time()
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception as e:
            print(f"networkidle timeout (continuing): {e}")
        t_idle = time.time()
        report["window_after_iso"] = datetime.now(timezone.utc).isoformat()

        screenshot = OUT / f"e2e-{ts}.png"
        page.screenshot(path=str(screenshot), full_page=False)

        report["timing"] = {
            "dom_content_loaded_ms": int((t_dcl - t0) * 1000),
            "network_idle_ms": int((t_idle - t0) * 1000),
        }
        report["screenshot"] = str(screenshot)
        report["console_errors"] = [m for m in console_msgs if m["type"] in ("error", "pageerror")]
        report["network_total"] = len(responses)
        report["network_5xx"] = [r for r in responses if r["status"] >= 500]
        report["network_4xx"] = [r for r in responses if 400 <= r["status"] < 500]

        page.close()
        browser.close()

    rep_path = OUT / f"e2e-{ts}.json"
    rep_path.write_text(json.dumps(report, ensure_ascii=False, indent=2))

    print(f"\n=== e2e summary ({url}) ===")
    print(f"  DCL:      {report['timing']['dom_content_loaded_ms']} ms")
    print(f"  net idle: {report['timing']['network_idle_ms']} ms")
    print(f"  network: total={report['network_total']}, "
          f"5xx={len(report['network_5xx'])}, 4xx={len(report['network_4xx'])}")
    print(f"  console errors: {len(report['console_errors'])}")
    for m in report["console_errors"][:5]:
        print(f"    [{m['type']}] {m['text'][:200]}")
    print(f"  screenshot: {report['screenshot']}")
    print(f"  report:     {rep_path}")
    print(f"\nUTC window for log query: {report['window_before_iso']}  ..  {report['window_after_iso']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
