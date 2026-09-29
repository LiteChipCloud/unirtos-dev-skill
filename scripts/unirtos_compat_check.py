#!/usr/bin/env python3
"""UniRTOS C source compatibility checker (static, heuristic).

Enforces the core rules from references/core-rules.md:
  E1  app entry registered via UNIRTOS_APP_EXPORT (exactly one per app group)
  E2  no direct FreeRTOS/POSIX includes (use qosa_sys.h)
  E3  every registered init function stays non-blocking (no while(1) in it)
  W1  task stack literals below 1024 bytes flagged
  W2  blocking network calls (qosa_datacall_start / qcm_mqtt_client_connect)
      inside an init function flagged
  W3  sleep used outside tasks (qosa_task_sleep in init fn) flagged

Usage:
    python unirtos_compat_check.py <dir-or-file> [--json]
Exit 0 when no errors (warnings allowed), 1 otherwise.
"""
import argparse
import json
import re
import sys
from pathlib import Path

BANNED_INCLUDES = [
    "FreeRTOS.h", "task.h", "queue.h", "semphr.h", "event_groups.h",
    "timers.h", "pthread.h", "unistd.h",
]
BLOCKING_CALLS = ["qosa_datacall_start(", "qcm_mqtt_client_connect("]
STACK_RE = re.compile(r"#define\s+\w*STACK\w*\s+(\d+)", re.IGNORECASE)


def check_file(path: Path) -> dict:
    issues = []
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        return {"file": str(path), "errors": [f"unreadable: {e}"], "warnings": []}

    # strip block comments to reduce false positives
    code = re.sub(r"/\*.*?\*/", "", text, flags=re.S)

    for inc in BANNED_INCLUDES:
        if re.search(rf'#include\s*[<"]{re.escape(inc)}[>"]', code):
            issues.append(("E2", f'direct "{inc}" include — use qosa_sys.h abstraction'))

    has_export = "UNIRTOS_APP_EXPORT" in code
    if path.suffix == ".c" and re.search(r"\bqosa_task_create\b", code) and not has_export:
        issues.append(("E1", "creates tasks but no UNIRTOS_APP_EXPORT registration"))

    # init fn = function whose name appears in the APP_EXPORT line
    m = re.search(r"UNIRTOS_APP_EXPORT\(\s*\w+\s*,\s*\"[^\"]*\"\s*,\s*(\w+)\s*\)", code)
    if m:
        init_fn = m.group(1)
        body = re.search(rf"void\s+{init_fn}\s*\([^)]*\)\s*\{{(.*?)\n\}}", code, flags=re.S)
        if body:
            b = body.group(1)
            if re.search(r"while\s*\(\s*1\s*\)|for\s*\(\s*;\s*;\s*\)", b):
                issues.append(("E3", f"init fn {init_fn}() contains an infinite loop — must create task and return"))
            for call in BLOCKING_CALLS:
                if call in b:
                    issues.append(("W2", f"blocking call {call} in init fn {init_fn}()"))
            if "qosa_task_sleep" in b:
                issues.append(("W3", f"qosa_task_sleep in init fn {init_fn}()"))

    for sm in STACK_RE.finditer(code):
        if int(sm.group(1)) < 1024:
            issues.append(("W1", f"stack size {sm.group(1)} < 1024 bytes in {sm.group(0).split()[1]}"))

    return {
        "file": str(path),
        "errors": [f"[{c}] {msg}" for c, msg in issues if c.startswith("E")],
        "warnings": [f"[{c}] {msg}" for c, msg in issues if c.startswith("W")],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="UniRTOS C compatibility checker")
    ap.add_argument("target", help="C source file or directory")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = Path(args.target)
    files = [root] if root.is_file() else sorted(root.rglob("*.c"))
    files = [f for f in files if ".git" not in f.parts and "qos_build" not in f.parts]
    if not files:
        print(json.dumps({"error": f"no .c files under {args.target}"}))
        return 1

    results = [check_file(f) for f in files]
    n_err = sum(len(r["errors"]) for r in results)
    n_warn = sum(len(r["warnings"]) for r in results)
    summary = {"files": len(results), "errors": n_err, "warnings": n_warn, "results": results}

    if args.json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        for r in results:
            if r["errors"] or r["warnings"]:
                print(f"--- {r['file']}")
                for e in r["errors"]:
                    print(f"  ERROR {e}")
                for w in r["warnings"]:
                    print(f"  warn  {w}")
        print(f"\n{len(results)} files, {n_err} errors, {n_warn} warnings")
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
