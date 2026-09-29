#!/usr/bin/env python3
"""UniRTOS environment doctor (read-only).

Checks every host-side prerequisite for UniRTOS development:
python, git, unirtos toolchain, unirtos-cli, SDK root (~/.unirtos),
installed SDK versions, git mirror setting.

Usage:
    python unirtos_env_doctor.py [--json]
Exit code 0 when all REQUIRED checks pass, 1 otherwise.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

OK = "ok"
WARN = "warn"
FAIL = "fail"


def _run(cmd: str, timeout: int = 20) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
        return p.returncode, (p.stdout or "").strip()
    except Exception as e:  # noqa: BLE001
        return -1, str(e)


def unirtos_root() -> Path:
    custom = os.environ.get("UNIRTOS_ROOT", "").strip()
    if custom:
        return Path(custom)
    up = os.environ.get("USERPROFILE", "").strip()
    if up:
        return Path(up) / ".unirtos"
    return Path.home() / ".unirtos"


def check(name: str, state: str, detail: str) -> dict:
    return {"name": name, "state": state, "detail": detail}


def main() -> int:
    ap = argparse.ArgumentParser(description="UniRTOS environment doctor (read-only)")
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()

    results = []

    # Python
    v = sys.version_info
    results.append(check(
        "python", OK if (v.major, v.minor) >= (3, 9) else FAIL,
        f"{sys.version.split()[0]} (need >=3.9)"))

    # Git
    rc, out = _run("git --version")
    results.append(check("git", OK if rc == 0 else FAIL, out or "git not found"))

    # unirtos toolchain
    rc, out = _run("unirtos --version")
    if rc == 0:
        state = OK
    elif shutil.which("unirtos"):
        state, out = WARN, "unirtos on PATH but --version failed"
    else:
        state, out = FAIL, "unirtos command not found (install unirtos-toolchain.exe, ~4.3 GB, default D:\\unirtos-toolchain)"
    results.append(check("unirtos-toolchain", state, out))

    # unirtos-cli (may live behind the Windows py launcher)
    cli_out, cli_state = "", FAIL
    for cmd in ("unirtos-cli version", "unirtos-cli.exe version", "python -m unirtos_cli version"):
        rc, out = _run(cmd)
        if rc == 0 and out:
            cli_out, cli_state = out.replace("\n", " "), OK
            break
    if cli_state == FAIL:
        cli_out = "unirtos-cli not found (pip install unirtos-cli)"
    results.append(check("unirtos-cli", cli_state, cli_out))

    # SDK root + installed versions
    root = unirtos_root()
    if root.exists():
        sdk_dir = root / "sdk"
        versions = sorted(
            d.name for d in sdk_dir.iterdir()
            if d.is_dir() and d.name.startswith("v")) if sdk_dir.exists() else []
        results.append(check("sdk-root", OK, str(root)))
        results.append(check(
            "sdk-versions",
            OK if versions else WARN,
            ", ".join(versions) if versions else "none installed (run unirtos-cli env-setup in a project)"))
        mirror_cfg = root / ".unirtosconfig"
        mirror = ""
        if mirror_cfg.exists():
            try:
                mirror = json.loads(mirror_cfg.read_text(encoding="utf-8")).get("git_mirror", "")
            except Exception:  # noqa: BLE001
                mirror = "(unreadable)"
        results.append(check(
            "git-mirror",
            OK if mirror == "gitee" else WARN,
            f"{mirror or '(default github)'} — use 'unirtos-cli git-mirror gitee' when GitHub is unreachable"))
    else:
        results.append(check("sdk-root", WARN, f"{root} does not exist yet (created by first env-setup)"))

    # Toolchain default install dir hint
    for hint in (r"D:\unirtos-toolchain", r"C:\unirtos-toolchain"):
        if Path(hint).exists():
            results.append(check("toolchain-dir", OK, hint))
            break
    else:
        results.append(check("toolchain-dir", WARN, "default dirs not found; unirtos on PATH is what matters"))

    failed = [r for r in results if r["state"] == FAIL]
    if args.json:
        print(json.dumps({"success": not failed, "results": results}, ensure_ascii=False, indent=2))
    else:
        icons = {OK: "[OK]  ", WARN: "[WARN]", FAIL: "[FAIL]"}
        for r in results:
            print(f"{icons[r['state']]} {r['name']:<18} {r['detail']}")
        print(f"\n{'PASS' if not failed else 'FAIL'}: {len(results) - len(failed)}/{len(results)} checks passed")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
