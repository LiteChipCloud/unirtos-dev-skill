#!/usr/bin/env python3
"""Fetch the official UniRTOS documentation set as markdown.

Downloads the Sphinx sources of https://docs.quectel.com/zh/UniRTOS/
(index.md.txt catalog + every linked page). Idempotent: re-running refreshes.

Usage:
    python unirtos_docs_fetch.py --out <target-dir> [--delay 0.3]
"""
import argparse
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

INDEX_URL = ("https://docs.quectel.com/zh/UniRTOS/UniRTOS%E6%96%87%E6%A1%A3/"
             "_sources/index.md.txt")
BASE_URL = ("https://docs.quectel.com/zh/UniRTOS/UniRTOS%E6%96%87%E6%A1%A3/"
            "_sources/")
UA = {"User-Agent": "Mozilla/5.0 (unirtos-dev skill docs fetcher)"}


def fetch(url: str, retries: int = 3) -> bytes:
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(1 + attempt)
    raise RuntimeError(f"fetch failed after {retries} tries: {url} ({last})")


def main() -> int:
    ap = argparse.ArgumentParser(description="Download UniRTOS docs as markdown")
    ap.add_argument("--out", default="docs-md", help="output directory")
    ap.add_argument("--delay", type=float, default=0.2, help="seconds between requests")
    args = ap.parse_args()

    try:
        index = fetch(INDEX_URL).decode("utf-8")
    except RuntimeError as e:
        print(f"ERROR: cannot read docs index: {e}", file=sys.stderr)
        return 1

    links = re.findall(r"\[.*?\]\(<(.*?)>\)", index)
    print(f"pages in catalog: {len(links)}")

    ok, failed = 0, []
    for rel in links:
        url = BASE_URL + urllib.parse.quote(rel) + ".txt"
        try:
            data = fetch(url)
        except RuntimeError as e:
            failed.append(rel)
            print(f"FAIL {rel}: {e}", file=sys.stderr)
            continue
        out_path = Path(args.out) / rel
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(data)
        ok += 1
        time.sleep(args.delay)

    (Path(args.out) / "_index.md.txt").write_text(index, encoding="utf-8")
    print(f"done: ok={ok} fail={len(failed)} -> {args.out}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
