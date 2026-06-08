#!/usr/bin/env python3
"""CDP smoke test: connect to the container's Chrome over CDP and open a page."""
from playwright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9222"   # adjust port if needed

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp(CDP)
    ctx = browser.contexts[0] if browser.contexts else browser.new_context()
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://example.com", wait_until="domcontentloaded")
    print("title:", page.title())
    print("url:  ", page.url)
    browser.close()   # detaches; the tab stays open for noVNC viewing
