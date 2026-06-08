#!/usr/bin/env python3
"""Close idle tabs, keeping one about:blank placeholder.

Usage: python3 scripts/gc.py                  # close all, keep 1 about:blank
       python3 scripts/gc.py --keep-url foo    # also keep tabs whose url contains foo
"""
import argparse
import json
import sys
import urllib.request

CDP = "http://127.0.0.1:9222"   # adjust port if needed


def list_targets():
    return json.loads(urllib.request.urlopen(f"{CDP}/json/list", timeout=3).read())


def close(target_id):
    urllib.request.urlopen(f"{CDP}/json/close/{target_id}", timeout=3).read()


def new_blank():
    urllib.request.urlopen(f"{CDP}/json/new?about:blank", timeout=3).read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep-url", default=None, help="keep pages whose url contains this")
    args = ap.parse_args()

    targets = list_targets()
    pages = [t for t in targets if t["type"] == "page"]
    has_blank = any("about:blank" in t["url"] for t in pages)
    if not has_blank:
        new_blank()
        targets = list_targets()
        pages = [t for t in targets if t["type"] == "page"]

    to_close = []
    for t in pages:
        if "about:blank" in t["url"]:
            continue
        if args.keep_url and args.keep_url in t["url"]:
            continue
        to_close.append(t)

    print(f"before: {len(pages)} pages, {sum(1 for t in targets if t['type']=='iframe')} iframes")
    print(f"closing {len(to_close)} pages")
    for t in to_close:
        try:
            close(t["id"])
        except Exception as e:
            print(f"  failed {t['id'][:10]} {t['url'][:60]}: {e}", file=sys.stderr)

    after = list_targets()
    print(f"after:  {sum(1 for t in after if t['type']=='page')} pages, "
          f"{sum(1 for t in after if t['type']=='iframe')} iframes")


if __name__ == "__main__":
    main()
