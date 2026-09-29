#!/usr/bin/env python3
"""EPAT auto-connect: attach EPAT to the module DIAG port without manual clicking.

Flow (field-verified on EPAT V1.5.315.676, EG800Z EVB):
  1. Patch Bin/config/EPAT.xml  -> Device_0 = DIAG COM port, Enabled=1
  2. Launch EPAT.exe
  3. Drive the 'Select Data Source' modal via pywinauto (Serial Device + COM + OK)
  4. Verify connection by checking the COM port is now held by EPAT

Afterwards (manual, by design): Database state -> Update -> load the build's
DBG/comdb.txt (database binding is a UI state, not automatable reliably).

Usage:
    python unirtos_epat_connect.py --epat-bin <EPAT Bin dir> --diag COM71 [--baud 3000000]
Exit 0 when EPAT holds the DIAG port.
"""
import argparse
import subprocess
import sys
import time


def patch_xml(epat_bin: str, com: str, baud: int) -> None:
    path = epat_bin + r"\config\EPAT.xml"
    x = open(path, encoding="utf-8").read()
    # replace only the Device_0 block values (first occurrences)
    x = x.replace("<COMName>USB Serial Port</COMName>", f"<COMName>Quectel USB DIAG Port</COMName>", 1)
    import re
    x = re.sub(r"(<Device_0_Settings>.*?)<COMNumber>\d+</COMNumber>",
               r"\1<COMNumber>%d</COMNumber>" % int(com.replace("COM", "")),
               x, count=1, flags=re.S)
    x = re.sub(r"(<Device_0_Settings>.*?)<BaudRate>\d+</BaudRate>",
               r"\1<BaudRate>%d</BaudRate>" % baud,
               x, count=1, flags=re.S)
    x = x.replace("<Enabled>0</Enabled>", "<Enabled>1</Enabled>", 1)
    open(path, "w", encoding="utf-8").write(x)
    print(f"patched {path}: Device_0 -> {com} @{baud}, enabled")


def port_free(com: str) -> bool:
    import serial
    try:
        s = serial.Serial(com, 115200, timeout=0.5)
        s.close()
        return True
    except Exception:
        return False


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto-connect EPAT to the module DIAG port")
    ap.add_argument("--epat-bin", required=True, help=r"e.g. C:\tools\EPAT_V1.5.315.676\Bin")
    ap.add_argument("--diag", required=True, help="DIAG port, e.g. COM71")
    ap.add_argument("--baud", type=int, default=3000000)
    args = ap.parse_args()

    try:
        import pywinauto  # noqa: F401
    except ImportError:
        print("ERROR: pip install pywinauto (and a comtypes build matching your python)")
        return 2

    patch_xml(args.epat_bin.rstrip("\\"), args.diag, args.baud)

    subprocess.run(["powershell", "-NoProfile", "-Command",
                    "Get-Process EPAT -ErrorAction SilentlyContinue | Stop-Process -Force"],
                   capture_output=True)
    time.sleep(2)
    subprocess.Popen([args.epat_bin + r"\EPAT.exe"], cwd=args.epat_bin)
    print("EPAT launched, waiting for the Select Data Source dialog...")
    time.sleep(12)

    from pywinauto import Application
    for attempt in range(10):
        try:
            app = Application(backend="win32").connect(title="Select Data Source")
            break
        except Exception:
            time.sleep(1)
    else:
        print("ERROR: Select Data Source dialog never appeared")
        return 1

    dlg = app.window(title="Select Data Source")
    children = dlg.children()
    radios = [c for c in children if c.window_text() == "Serial Device"]
    oks = [c for c in children if c.window_text() == "OK"]
    edits = [c for c in children if c.friendly_class_name() == "Edit"]
    WM_SETTEXT = 0x000C
    radios[0].check()
    time.sleep(0.3)
    if edits:
        edits[0].send_message(WM_SETTEXT, 0, args.diag)  # message-based: works cross-elevation
    time.sleep(0.3)
    oks[0].click()
    time.sleep(3)

    if port_free(args.diag):
        print(f"WARNING: {args.diag} still free — EPAT did not take it. Check the Select dialog/combo.")
        return 1
    print(f"OK: EPAT is connected to {args.diag} and streaming.")
    print("NEXT (manual): Database state -> Update -> load the build's DBG/comdb.txt,")
    print("then Ctrl+F in UniLogViewer for your log text.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
