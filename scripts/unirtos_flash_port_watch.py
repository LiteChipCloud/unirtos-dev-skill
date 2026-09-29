#!/usr/bin/env python3
"""Flash port watcher — poll serial ports and detect download-mode enumeration.

Monitors for "QDLoader" (EC718-family download/boot port) and reports every
Quectel port transition so flashing sessions have evidence of mode entry.

Usage:
    python unirtos_flash_port_watch.py --wait 60        # wait up to 60s for QDLoader
    python unirtos_flash_port_watch.py --watch 30       # observe transitions for 30s
    python unirtos_flash_port_watch.py --json --wait 60
Exit 0 when QDLoader appeared (within --wait), 1 otherwise.
"""
import argparse
import json
import sys
import time


def snapshot() -> dict:
    from serial.tools import list_ports
    return {p.device: p.description for p in list_ports.comports()}


def main() -> int:
    ap = argparse.ArgumentParser(description="UniRTOS flash port watcher (read-only)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--wait", type=int, metavar="SEC", help="wait for a QDLoader port to appear")
    g.add_argument("--watch", type=int, metavar="SEC", help="observe and print transitions")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not args.wait and not args.watch:
        args.wait = 1

    baseline = snapshot()
    deadline = time.time() + (args.wait or args.watch or 1)
    last = baseline
    qdloader_seen = any("QDLoader" in d for d in baseline.values())

    def report(msg: str):
        if not args.json:
            print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)

    report(f"baseline: {len(baseline)} ports; QDLoader present: {qdloader_seen}")
    while time.time() < deadline:
        time.sleep(1)
        cur = snapshot()
        for dev, desc in cur.items():
            if dev not in last:
                report(f"APPEARED {dev}: {desc}")
                if "QDLoader" in desc:
                    qdloader_seen = True
        for dev, desc in last.items():
            if dev not in cur:
                report(f"DISAPPEARED {dev}: {desc}")
        last = cur

    out = {"qdloader_present": any("QDLoader" in d for d in last.values()),
           "seen_during_session": qdloader_seen, "ports": last}
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"final: qdloader_present={out['qdloader_present']}  ports={list(last.keys())}")
    return 0 if out["seen_during_session"] or out["qdloader_present"] else 1


if __name__ == "__main__":
    sys.exit(main())
