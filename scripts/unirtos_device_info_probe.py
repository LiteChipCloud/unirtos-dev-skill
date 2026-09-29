#!/usr/bin/env python3
"""UniRTOS device info probe — read-only AT interrogation of ONE named AT port.

Collects: model, firmware revision, IMEI, SIM state, ICCID, IMSI, signal,
network registration, packet attachment, plus optional raw transcript.

Usage:
    python unirtos_device_info_probe.py --port COM73 [--json] [--include-raw]

Safety: refuses non-AT ports; sends only query commands; writes nothing.
"""
import argparse
import json
import re
import sys
import time

import serial

QUERIES = [
    ("model", b"ATI\r"),
    ("device_model", b"AT+CGMM\r"),
    ("firmware", b"AT+CGMR\r"),
    ("imei", b"AT+CGSN\r"),
    ("manufacture_id", b"AT+CGMI\r"),
    ("sim_state", b"AT+CPIN?\r"),
    ("iccid", b"AT+QCCID\r"),
    ("imsi", b"AT+CIMI\r"),
    ("signal", b"AT+CSQ\r"),
    ("lte_registration", b"AT+CEREG?\r"),
    ("packet_attachment", b"AT+CGATT?\r"),
    ("subscriber_number", b"AT+CNUM\r"),
]

REFUSED_FRAGMENTS = ("DIAG", "REPL", "Modem", "NMEA", "DM Port", "SND")
FAMILY = ("EG800Z", "EG915Z", "EC800Z")


def send(s, cmd: bytes, wait: float = 0.8) -> str:
    s.reset_input_buffer()
    s.write(cmd)
    time.sleep(wait)
    return s.read(8192).decode(errors="replace").strip()


def main() -> int:
    ap = argparse.ArgumentParser(description="UniRTOS read-only device info probe")
    ap.add_argument("--port", required=True, help="AT port, e.g. COM73")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--include-raw", action="store_true")
    args = ap.parse_args()

    from serial.tools import list_ports
    desc = next((p.description for p in list_ports.comports() if p.device == args.port), "")
    if any(f.lower() in desc.lower() for f in REFUSED_FRAGMENTS):
        print(json.dumps({"success": False, "error": f"refused non-AT port: {desc}"}))
        return 1

    result = {"port": args.port, "success": True, "data": {}, "raw": {}}
    try:
        with serial.Serial(args.port, args.baud, timeout=2) as s:
            for name, cmd in QUERIES:
                resp = send(s, cmd)
                result["data"][name] = " ".join(resp.split())
                if args.include_raw:
                    result["raw"][name] = resp
                time.sleep(0.2)
    except serial.SerialException as e:
        result = {"success": False, "port": args.port, "error": str(e)}
        print(json.dumps(result, ensure_ascii=False))
        return 1

    blob = " ".join(result["data"].values())
    result["unirtos_family"] = any(f in blob for f in FAMILY)
    m = re.search(r"(EG800Z|EG915Z|EC800Z)[A-Z0-9_]*", blob)
    result["module_model"] = m.group(0) if m else None
    csq = re.search(r"\+CSQ:\s*(\d+),", blob)
    if csq:
        rssi = int(csq.group(1))
        result["signal_dbm"] = (-113 + 2 * rssi) if 0 <= rssi <= 31 else None
    result["sim_ok"] = "READY" in result["data"].get("sim_state", "")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"port={result['port']}  family={result['unirtos_family']}  model={result.get('module_model')}")
        for k, v in result["data"].items():
            print(f"  {k:<18} {v[:100]}")
        print(f"  signal_dbm        {result.get('signal_dbm')}  sim_ok={result.get('sim_ok')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
