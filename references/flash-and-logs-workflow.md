# Flash & Logs Workflow

Sources: official docs 快速上手/烧录固件, 快速上手/日志调试, 开发工具/QFlash/QCOM/EPAT/FOTA/QMulti_DL 教程 (full text in `assets/docs-md/`).

## 1. Identify before you touch (mandatory)

```bash
python <skill>/scripts/unirtos_com_probe.py            # enumerate + classify
python <skill>/scripts/unirtos_com_probe.py --identify COM70   # read-only ATI on ONE port
```

Expected EG800Z EVB identity: ATI → `Quectel`, `EG800Z...`, Revision like `EG800ZCNLARxxAxx..._OCPU_...`. Foreign responses (e.g. `EC800K ... _QPY` = the local remote-switch device) → STOP, never flash.

## 2. Flash — two official paths

### 2a. Fully automated (verified working 2026-09-20, EG800Z EVB) — RECOMMENDED

No wires, no QFlash, no login. Requires only: unirtos build output + any Quectel tool install that bundles `Eigen_718/FlashToolCLI.exe` (QPYcom ≥4.1 auto-extracts it into `<qpycom>/exes/Eigen_718/` on first download attempt; also shipped inside UniRTOS-vscode-Extension `src/data/Eigen_718/`).

Flow (mirrors official UniRTOS-vscode-Extension `flashFirmware.ts`):

1. Send **`AT+QDOWNLOAD=1`** to the module's **AT port** (115200) → module reboots into download mode; AT/DIAG/Modem ports disappear.
2. Poll ≤20 s for the new **`Quectel QDLoader Port`** (e.g. COM74). ⚠️ Download mode times out (~1–2 min) — start flashing immediately.
3. Run FlashToolCLI sequence (cfg = `quec_download_usb.ini` from the release dir; cwd anywhere writable):
```bash
FlashToolCLI --cfgfile <rel>/quec_download_usb.ini pkg2img
FlashToolCLI --cfgfile <cfg> --port <QDLoader> probe
FlashToolCLI --skipconnect 1 --cfgfile <cfg> --port <QDLoader> burnone agentboot
FlashToolCLI --skipconnect 1 --cfgfile <cfg> --port <QDLoader> burnone bootloader
FlashToolCLI --skipconnect 1 --cfgfile <cfg> --port <QDLoader> burnone system
FlashToolCLI --skipconnect 1 --cfgfile <cfg> --port <QDLoader> burnone cp_system
FlashToolCLI --skipconnect 1 --cfgfile <cfg> --port <QDLoader> burnone pkgflx0   # ← ap_application.bin (user app) @0x258000
FlashToolCLI --skipconnect 1 --cfgfile <cfg> --port <QDLoader> burnone pkgflx1   # ← ap_updater.bin
FlashToolCLI --skipconnect 1 --cfgfile <cfg> --port <QDLoader> sysreset
```
4. Module reboots into the new firmware. Verify: ATI shows `Revision: QSR01A03_C_SDK_...` + `CustRevision: ...` (C SDK) instead of the stock `...RxxAxxMxx` AT revision. Note: unirtos_std's AT set is reduced — `AT+CGMM`/`CGMR` answer ERROR; use `ATI`.
5. `pkg2img` regenerates `quec_download_usb.ini` with concrete `pkgimg_gen/...` paths + partition addresses (`[pkgflx0] ap_application.bin @0x258000` = user app) — keep this file with the release as flash evidence.

Gotchas learned:
- FlashToolCLI global args: `--port --cfgfile --skipconnect --lineid --verbose`; subcommand args (e.g. `--snd_ass_port`) come AFTER the subcommand. Empty/guessed `config.ini` schemas silently yield empty linelist → `[com open fail]`; always pass cfg via `--cfgfile` to the release `quec_download_usb.ini`.
- `assist_second_port_cmd = at+ecrst=delay,599` inside the ini is the tool's UART-mode reset fallback; USB flow does not need it.
- Reusable script pattern: `unirtos-workspace/flash_now.py` (QDOWNLOAD → poll QDLoader → 9-step sequence).

### 2b. QFlash (official GUI alternative)

1. Build: `unirtos-cli build -m EG800ZCN_LA -v <version>` → `<project>/qos_build/release/<version>/<version>.hbinpkg` (file named `at_command.hbinpkg` in SDK 1.0.1).
2. Enter download mode: 官方 QFlash 教程 — 开发板正面**短接 5V 和 BOOT 排针**再上电（wire method), or `AT+QDOWNLOAD=1` (software method).
3. `Quectel QDLoader Port` appears → QFlash Load FW Files → `.hbinpkg` → select QDLoader port → Start → **PASS**.
4. Verify: ATI/CGMR as above.
5. QFlash ≥V8.0 required for EC718 platform (login-gated download); QPYcom ≥3.9 的"下载固件" page is equivalent but its AT-port flow needs the module already in download mode.

### Tooling gotchas (learned 2026-09-10, machine: win11 / EG800Z EVB)

| Issue | Fact | Workaround |
| --- | --- | --- |
| QFlash download is login-gated | `QFlash_V8.0_CN` (311 MB) on quectel.com.cn download-zone requires a (free) account; `authority=1` on the search API | Download manually once into `<workspace>/tools/`; old local QFlash V7.3 does NOT support EC718/EG800Z (no mention in its ini configs) |
| No flasher in toolchain | unirtos-toolchain ships `unirtos.exe` (build only) — no download/flash subcommand | QFlash (or QMulti_DL for batch) is mandatory for serial flashing |
| first cmake configure fails | `toolchain.cmake:121 Failed to extract archive.7z` — flaky 7z call inside execute_process | Pre-extract manually: `7z x qos_build/gccout/images/firmware_base_release_pack.7z -oqos_build/gccout/images/firmware_base_release_pack`, rebuild (cmake then takes the "Reusing" branch) |
| toolchain setup.bat broken on some hosts | `setup.bat` adds `xz-5.2.9\bin_x86-64` to PATH but the SFX ships `bin_i686` → txz components never unpack ("系统找不到指定的路径") | `set PATH=<toolchain>\xz-5.2.9\bin_i686;%PATH%` then `tar\tar.exe -Jxf <comp>.txz` per archive; then add `<toolchain>\bin` to user PATH |
| EPAT is not login-gated | `EPAT_V1.5.x.zip` fetches via the same `admin-ajax` `multifile_download` flow without login | direct: `https://www.quectel.com.cn/wp-content/uploads/2026/04/EPAT_V1.5.315.676.zip` |

Notes:
- QFlash rewrites the whole image — first flash of a custom app replaces the stock AT firmware.
- Multi-device batch flashing: QMulti_DL tool (docs: QMulti_DL使用教程).
- OTA instead of cable: FOTA (docs: FOTA升级 + FOTA工具使用教程) — needs a signed/fota package and server-side flow.

## 3. App logs with EPAT

Automated connection (field-verified): `python scripts/unirtos_epat_connect.py --epat-bin <Bin> --diag COM71` — patches `config/EPAT.xml` (Device_0 → DIAG COM, Enabled), launches EPAT, drives the `Select Data Source` modal via pywinauto, verifies by port-hold. Requires `pip install pywinauto` (32-bit EPAT automatable from 64-bit Python via win32 backend + message-based clicks).

1. Ports: `Quectel USB DIAG Port` = log; `Quectel USB AT Port` = AT. Record both.
2. EPAT → Serial Device → Device Communication → Device 0 Settings → select DIAG COM → enable Device 0 → UniLogViewer streams.
3. Database: Database state → Update → browse `comdb.txt` from `<project>/qos_build/release/<version>/<version>/DBG/` → Update. Logs only symbolize with the comdb matching the exact build — EPAT shows **"Database is unmatched, please select correct database file and update it"** when the stream decodes with the wrong DB (shipped DB decodes kernel/system messages; app QLOG strings need the build's own comdb).
4. Filter: Pause/Stop capture, Ctrl+F, e.g. search `hello world` (Match Case + List All Found Items).
5. `QLOGV/D/I/W/E` app logs appear with the `QOS_LOG_TAG`/entry name registered at boot (`app init: <name>` lines at startup are visible in EPAT).

Field notes (2026-09-20):
- DIAG raw stream is high-volume binary UniLog (~80 KB/s on idle EG800Z): kernel/system text is protocol-encoded; log strings are indexed by the comdb database, so raw pyserial capture cannot grep app strings — EPAT+comdb is mandatory for decoding.
- UniRTOS firmware (post-flash) enumerates an extra `USB 串行设备` COM (dormant, silent at all bauds — not the log port). Use the DIAG port.
- EPAT launches create per-session folders under `Bin/Logs/<YYYYMMDD_HHMMSS>/` (trace logs only; decoded log text stays in the viewer unless saved).

Alternative: `qcm_uart_log` component can mirror logs to a hardware UART (e.g. main UART header 0/1) for bench logging without EPAT.

### App-log visibility caveat (SDK 1.0.1, field-verified)

The `DBG/comdb.txt` from an SDK 1.0.1 build covers the CP/modem domain only — system messages decode in EPAT, but **user-app QLOG strings are absent from the database** (the app IS in the flashed image; verified via string search in `ap_application.bin`). If `hello world`-style app lines don't appear:
1. upgrade `sdk.version` (1.0.5+) and rebuild — newer DBG may regenerate comdb with app strings;
2. or mirror app logs via `qcm_uart_log` to the main UART;
3. or match the DB by UE version: State dialog shows `UE Ver` vs `PC Ver` — the module reports its embedded log-db version (e.g. `0x5a414e44`) which the base comdb (`0x0de85ecd` / DbVersion 1514229316) does not match.

## 4. AT workflow (QCOM or any serial tool)

- Port: `Quectel USB AT Port`, baud 115200 (main UART header supports up to 921600).
- Sanity set: `AT` → OK; `ATI`; `AT+CGMM`; `AT+CGMR`; network: `AT+CPIN?`, `AT+CSQ`, `AT+CEREG?`, `AT+CGATT?`.
- On UniRTOS **custom app** firmware, the standard AT surface may be reduced (your app replaced unirtos_std). If AT is required on-device, either flash the stock AT firmware or implement a custom AT command (docs: 自定义AT开发指南, `qosa_at_cmd.h`).

## 5. Evidence discipline (delivery rule)

Every "flashed/works/logs clean" claim needs one of:
1. QFlash PASS screenshot/log + post-flash `ATI` response.
2. EPAT capture showing the app's QLOG lines with matching comdb.
3. AT transcript with timestamps.

Store evidence under `review/` of the working project, not in the skill.
