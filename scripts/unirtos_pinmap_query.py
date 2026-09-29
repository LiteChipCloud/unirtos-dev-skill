#!/usr/bin/env python3
"""UniRTOS EG800Z QuecDuino EVB pin map query.

Two data sources with different trust levels:
  doc    — official doc table (may match a different HW revision)
  silk   — V1.0 board silk/diagram (matches the physical EVB in hand)
Where they disagree the entry is flagged. Always code against the silk
mapping for the local V1.0 board and verify with a meter before wiring.

Usage:
    python unirtos_pinmap_query.py --pin 19          # by module PIN number
    python unirtos_pinmap_query.py --header D0      # by header label
    python unirtos_pinmap_query.py --header 10 --json
"""
import argparse
import json
import sys

# header_label: {source: module_pin}
BOARD = {
    "A0":  {"doc": "ADC0", "silk": "ADC0", "note": "analog 0-1.2V"},
    "A1":  {"doc": "ADC1", "silk": "ADC1", "note": "analog 0-1.2V"},
    "D0":  {"doc": "PIN19", "silk": "PIN19"},
    "D1":  {"doc": "PIN20", "silk": "PIN20"},
    "D2":  {"doc": "PIN21", "silk": "PIN21"},
    "D3":  {"doc": "PIN25", "silk": "PIN22", "conflict": True},
    "0":   {"doc": "RXD2", "silk": "RX2", "note": "main UART RX"},
    "1":   {"doc": "TXD2", "silk": "TX2", "note": "main UART TX"},
    "2":   {"doc": "RXD0", "silk": "RXD0", "note": "aux UART RX"},
    "3":   {"doc": "TXD0", "silk": "TXD0", "note": "aux UART TX"},
    "4":   {"doc": "PIN23", "silk": "PIN23"},
    "5":   {"doc": "PIN22", "silk": "PIN25", "conflict": True},
    "6":   {"doc": "PIN28", "silk": "PIN28"},
    "7":   {"doc": "PIN29", "silk": "PIN29"},
    "8":   {"doc": "PIN58", "silk": "PIN66", "conflict": True},
    "9":   {"doc": "PIN80", "silk": "PIN67", "conflict": True},
    "10":  {"doc": "PIN31", "silk": "PIN64", "conflict": True, "note": "silk: SPI CLK group"},
    "11":  {"doc": "PIN32", "silk": "PIN63", "conflict": True, "note": "silk: SPI MISO"},
    "12":  {"doc": "PIN33", "silk": "PIN62", "conflict": True, "note": "silk: SPI MOSI"},
    "13":  {"doc": "PIN30", "silk": "PIN49", "conflict": True, "note": "silk: SPI CS"},
    "14":  {"doc": "GND", "silk": "GND"},
    "15":  {"doc": "NC", "silk": "NC"},
    "16":  {"doc": "PIN66", "silk": "PIN58", "conflict": True, "note": "silk: SCL group"},
    "17":  {"doc": "PIN67", "silk": "PIN57", "conflict": True, "note": "silk: SDA group"},
    "LED1": {"doc": None, "silk": "POW", "note": "power LED"},
    "LED2": {"doc": None, "silk": "NET", "note": "network LED"},
    "LED3": {"doc": None, "silk": "PIN55", "note": "user LED, silk D3"},
    "LED4": {"doc": None, "silk": "PIN56", "note": "user LED, silk D4"},
    "KEY_S1": {"doc": None, "silk": "PWKEY", "note": "power key"},
    "KEY_S2": {"doc": None, "silk": "PIN50", "note": "user key"},
    "KEY_S3": {"doc": None, "silk": "PIN51", "note": "user key"},
}

# reverse index: module pin -> headers
by_pin = {}
for label, entry in BOARD.items():
    for src in ("doc", "silk"):
        val = entry.get(src)
        if isinstance(val, str) and val.startswith("PIN"):
            by_pin.setdefault(int(val[3:]), set()).add(f"{label}({src})")


def main() -> int:
    ap = argparse.ArgumentParser(description="EG800Z QuecDuino EVB pin map query")
    ap.add_argument("--pin", type=int, help="module PIN number, e.g. 19")
    ap.add_argument("--header", help="header label, e.g. D0, A1, 10, LED3, KEY_S2")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.pin is not None:
        hits = sorted(by_pin.get(args.pin, []))
        out = {"pin": f"PIN{args.pin}", "headers": hits,
               "advice": "code uses the PIN number (qosa_gpio pin num); for the local V1.0 board trust silk entries"}
    elif args.header:
        key = args.header.upper()
        entry = BOARD.get(key)
        if entry is None:
            print(json.dumps({"error": f"unknown header '{args.header}'",
                              "known": sorted(BOARD.keys())}, ensure_ascii=False))
            return 1
        conflict = entry.get("conflict", False)
        out = {"header": key, **entry,
               "trust": "silk (V1.0 board in hand)" if conflict else "doc and silk agree"}
    else:
        out = {"error": "pass --pin N or --header LABEL", "known_headers": sorted(BOARD.keys())}
        print(json.dumps(out, ensure_ascii=False))
        return 1

    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        for k, v in out.items():
            print(f"{k:>8}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
