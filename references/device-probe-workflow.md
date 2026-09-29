# Device Probe Workflow

How to discover and identify local devices safely. Encodes the local safety rule: one machine may host several Quectel devices with different owners — identification precedes any action.

## 1. Enumerate (always safe)

```bash
python <skill>/scripts/unirtos_com_probe.py --json
```

Classifies ports by Windows friendly name:
| Name fragment | Role | Safe to open? |
| --- | --- | --- |
| `Quectel USB AT Port` | AT command / QFlash flashing | only after identification, and only for read-only AT unless user approved flashing |
| `Quectel USB DIAG Port` | EPAT binary log stream | never open manually (EPAT owns it) |
| `Quectel USB Modem` | PPP modem | no |
| `Quectel USB REPL Port` | dev-firmware console | never assume — REPL implies a Python/dev firmware; identify first |
| `Quectel USB NMEA` | GNSS sentences | read-only OK |

One physical module enumerates as a group (same `hwid` serial/location). Group ports by VID:PID+serial before attributing them to a board.

## 2. Identify (opt-in, read-only)

```bash
python <skill>/scripts/unirtos_com_probe.py --identify COM70
```

Sends only `ATI`, `AT+CGMM`, `AT+CGMR` at 115200 and prints the response with a verdict:
- `EG800Z*` / `EC800Z*` / `EG915Z*` → UniRTOS-capable family, green light for the workflow.
- `EC800K` + `_QPY` (or any `*QPY*` revision) → **QuecPython device (the local remote switch unit) — do not flash, do not reset, do not install anything.**
- No response → wrong port or non-AT port; do not retry blindly on DIAG/Modem.

## 3. Known state on this machine (2026-09-10, post power-on)

| Device | Ports | Identity | Policy |
| --- | --- | --- | --- |
| 远程开关设备 (remote switch) | COM67 DIAG, COM68 Modem, COM69 REPL, COM70 AT | EC800K, QuecPython (`..._QPY`, ThreadX R-5.1) | **off-limits — never flash/reset/write** |
| EG800Z QuecDuino EVB | COM71 DIAG, COM72 Modem, COM73 AT | EG800Z (`EG800ZCNLAR07A07M04`), stock AT firmware | UniRTOS dev target |

EVB health snapshot at bring-up: RSSI -79 dBm (CSQ 17), no SIM inserted (CPIN/QCCID → CME ERROR 10), therefore CEREG 0 / CGATT 0. Networking work needs a NANO SIM first; build/flash/GPIO bring-up does not.

Power-on reminder: USB only powers the board — long-press the **PWK ON (PWKEY)** button (~2 s) to boot; new ports appear only after boot.

## 4. Rules

1. Never flash a port that was not identified in this session — ports renumber on re-plug.
2. Never send AT to a DIAG/Modem/REPL port (binary protocols; may wedge the module).
3. When both devices are enumerated, do port↔device mapping by identification verdict, record it in the working project's `review/`, and proceed only against the EG800Z group.
4. All probe operations are read-only by design; the script contains no write/flash path at all.
