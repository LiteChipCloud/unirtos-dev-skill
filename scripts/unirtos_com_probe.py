#!/usr/bin/env python3
"""UniRTOS COM port probe — enumeration always safe, identification opt-in.

Enumerates serial ports and classifies Quectel USB port roles. Identification
(`--identify COMx`) sends ONLY read-only AT queries (ATI / AT+CGMM / AT+CGMR)
to the single port named by the user. The script has no write/flash path.

Usage:
    python unirtos_com_probe.py [--json]
    python unirtos_com_probe.py --identify COM70
"""
import argparse
import json
import sys
import time

QUECTEL_VID = "2C7C"

ROLE_BY_NAME = [
    ("DIAG", "diag/EPAT log — never open manually"),
    ("AT Port", "AT commands / QFlash — identify before any write"),
    ("Modem", "PPP modem — do not open"),
    ("REPL", "dev-firmware console — identify before use"),
    ("NMEA", "GNSS sentences — read-only ok"),
    ("DM Port", "diag/dump — do not open"),
    ("SND", "audio — do not open"),
    ("VBUS", "virtual bus — do not open"),
]

FAMILY_PATTERNS = ("EG800Z", "EG915Z", "EC800Z")
FOREIGN_MARKERS = ("QPY",)  # QuecPython firmware revisions


def classify(desc: str) -> str:
    for needle, role in ROLE_BY_NAME:
        if needle.lower() in desc.lower():
            return role
    return "unknown role"


def list_ports() -> list[dict]:
    try:
        from serial.tools import list_ports as _lp
    except ImportError:
        print("ERROR: pyserial missing (pip install pyserial)", file=sys.stderr)
        sys.exit(2)
    ports = []
    for p in _lp.comports():
        is_quectel = (p.vid is not None and format(p.vid, "04X") == QUECTEL_VID)
        ports.append({
            "port": p.device,
            "description": p.description,
            "hwid": p.hwid,
            "quectel": is_quectel,
            "role": classify(p.description) if is_quectel else "",
        })
    return ports


def identify(port_name: str, ports: list[dict]) -> dict:
    info = next((p for p in ports if p["port"].upper() == port_name.upper()), None)
    if info is None:
        return {"port": port_name, "verdict": "error", "detail": "port not present"}
    if not info["quectel"]:
        return {"port": port_name, "verdict": "refused", "detail": "not a Quectel device"}
    if "AT" not in info["description"]:
        return {
            "port": port_name, "verdict": "refused",
            "detail": f"refuse to open non-AT port ({info['description']}); use the AT Port of the same device group",
        }

    import serial
    queries = [b"ATI\r", b"AT+CGMM\r", b"AT+CGMR\r"]
    lines, err = [], None
    try:
        with serial.Serial(port_name, 115200, timeout=2) as s:
            for q in queries:
                s.write(q)
                time.sleep(0.6)
                lines.append(s.read(4096).decode(errors="replace").strip())
    except Exception as e:  # noqa: BLE001
        err = str(e)

    if err is not None:
        return {"port": port_name, "verdict": "error", "detail": err}

    blob = "\n".join(lines)
    verdict, detail = "unknown", "no model string parsed — verify manually"
    for fam in FAMILY_PATTERNS:
        if fam in blob:
            verdict = "unirtos-family"
            detail = f"{fam} family detected — UniRTOS workflow applies"
            break
    else:
        if any(m in blob for m in FOREIGN_MARKERS):
            verdict = "foreign-device"
            detail = "QuecPython/other firmware detected — DO NOT FLASH this device"
    return {"port": port_name, "verdict": verdict, "detail": detail,
            "response": blob[:2000]}


def main() -> int:
    ap = argparse.ArgumentParser(description="UniRTOS COM probe (read-only)")
    ap.add_argument("--identify", metavar="COMx",
                    help="read-only identification (ATI/CGMM/CGMR) of ONE AT port")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    ports = list_ports()
    result = {"ports": ports}

    if args.identify:
        result["identify"] = identify(args.identify, ports)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if not ports:
        print("no serial ports found")
        return 0
    for p in ports:
        tag = "Quectel" if p["quectel"] else "  ---- "
        print(f"{p['port']:<7} [{tag}] {p['description']:<38} {p['role']}")
    if "identify" in result:
        r = result["identify"]
        print(f"\nidentify {r['port']}: {r['verdict']} — {r['detail']}")
        if "response" in r:
            print("--- raw ---")
            print(r["response"])
    print("\nnote: identification is read-only (ATI/CGMM/CGMR); flashing requires explicit user confirmation and a verified unirtos-family verdict")
    return 0


if __name__ == "__main__":
    sys.exit(main())
