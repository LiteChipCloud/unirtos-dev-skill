# unirtos-dev CHANGELOG

Format based on Keep a Changelog; versioning: semver (MAJOR.MINOR.PATCH — MINOR bump on new capability/reference/script additions, PATCH on corrections).

## [1.1.1] — 2026-09-20

### Full-stack IoT validation (EG800Z + ESP32-S3 camera)
- Complete bidirectional IoT loop verified on hardware: EG800Z (D3/D4 LEDs) <-> MQTT <-> cloud. Commands on/off/blink executed by device, confirmed via telemetry. Camera (ESP32-S3 + GC2145) captured the EG800Z board in each state.
- at+ecrst=delay,599 on AT port = repeatable software download-mode entry (no wires). Discovered via UniRTOS-vscode-Extension source reverse-engineering.
- FlashToolCLI 9-step burn (pkg2img -> probe -> burnone x6 -> sysreset) field-verified zero failures.
- GPIO mapping fix field-verified: pin_cfg.gpio_num (not raw pin number) drives GPIO ops. D3=PIN55 / D4=PIN56 confirmed controllable.
- SDK 1.0.5 tree reconstruction: API-tree SHA diff -> raw-fetch -> hash-object -> mktree bottom-up (352/352 verified). Only 21 files differ v1.0.1 vs v1.0.5.
- ESP32-S3 camera streaming: GC2145 detected, AP mode + BMP snapshot server, 5-frame sequence captured over LAN.

## [1.1.1] — 2026-09-20 (original)

### Added
- `scripts/unirtos_epat_connect.py` — EPAT auto-connect (patch EPAT.xml Device_0 → DIAG COM, launch, drive `Select Data Source` modal via pywinauto message-based clicks, verify by port-hold). Field-tested up to connection; comdb load stays manual by design.
- `references/flash-and-logs-workflow.md`: EPAT field notes — DIAG raw stream is comdb-indexed binary (raw grep cannot find app strings), post-flash extra dormant USB serial COM, per-session Logs folders, "Database is unmatched" dialog meaning and resolution.

### Verified on hardware (2026-09-20)
- EPAT auto-connected to COM71 (DIAG) via script: `at^logversion` handshake + `IMC_UEVERSION` + UnilogMessageParserJob thread confirmed in session traces.
- DIAG raw capture: ~80 KB/s binary UniLog; `hello world` not greppable raw (confirms comdb decoding requirement).
- **App-log visibility root cause**: SDK 1.0.1's `DBG/comdb.txt` covers the CP/modem domain only (verified: system strings present in plaintext, app strings absent; both comdbs in build output carry DbVersion 1514229316). The user app's QLOG strings are confirmed present in the flashed `ap_application.bin` but cannot decode in EPAT without an app-inclusive comdb. Remedies: upgrade `sdk.version` to 1.0.5 (newer DBG may regenerate comdb with app strings) or mirror app logs via `qcm_uart_log` to a hardware UART.
- **UniLog ID mechanism decoded** (from SDK 1.0.5 source): app QLOG* macros expand to `swLogPrintf(UNILOG_UNIQUE_ID(UNILOG_CUSTOMER, tag), P_INFO, ...)` — the format string is DISCARDED at compile time (`(void)format`); only a build-pasted symbol `CUSTOMER__<TAG>__<file>_<line>` (packed ownId|modId|subId|len 32-bit ID) is sent. Decoding therefore requires a comdb containing entries keyed by that generated ID — which no shipped comdb covers for user apps (the vendor's comdb generator is internal). Epaper trail: comdb entry format is `id,params,0,0,MODULE,SUB,func_symbol,LEVEL,swLogPrintf("fmt")` with plaintext format strings.
- SDK 1.0.5 built successfully end-to-end with the reconstructed tree (gpio demo, version EG800ZCNLAR01A05_GPIO_20260920) — the tree-rebuild recipe is exact (352/352 subtrees SHA-verified against the API).
- EPAT UI automation notes: EPAT runs elevated (UIPI blocks window-message control from unelevated scripts) — raw mouse/keyboard at UIA-reported coordinates work; message-based WM_SETTEXT/BM_CLICK are silently dropped; GetWindowText read-back of controls returns empty (also UIPI). Search dialog hidden by default; State/CheckVersion/Save-As dialogs enumerable via win32.
- Saved artifacts: `review/epat-raw-pre-comdb.zip` (17.5 MB raw stream), `review/diag-boot-capture.bin` (4.7 MB boot stream), viewer screenshots.
- SDK 1.0.5 fetch status: gitee pack transfer fails at any size tonight (full/filtered/incremental clones + lazy blob fetches all die with early EOF); API-raw transfer of `images/EG800ZCN_LA/gccout.7z` (13.9 MB @ v1.0.5) dies at 3-5 MB consistently; server ignores HTTP Range (no chunked download). Only the v1.0.1↔v1.0.5 diff is 21 files — 11 fetched, the 10 gccout.7z binaries blocked. Working recipe documented: local-dir copy of v1.0.1 repo → API-tree SHA diff (only 21 files) → raw-fetch small files → git-channel big blobs (works when network cooperates).

## [1.1.0] — 2026-09-20

### Added
- **Automated flashing recipe (field-verified)**: `AT+QDOWNLOAD=1` software download-mode entry + `Eigen_718/FlashToolCLI.exe` 9-step burn sequence (`pkg2img → probe → burnone agentboot/bootloader/system/cp_system/pkgflx0/pkgflx1 → sysreset`), reverse-engineered from the official open-source UniRTOS-vscode-Extension (`src/commands/flash/flashFirmware.ts`, constants `AT_DOWNLOAD = 'AT+QDOWNLOAD=1'`). No QFlash login, no jumper wires. Reusable script: `unirtos-workspace/flash_now.py`.
- `scripts/unirtos_device_info_probe.py` — read-only full AT dossier (model/fw/IMEI/SIM/ICCID/signal/registration), refuses non-AT ports.
- `scripts/unirtos_pinmap_query.py` — EG800Z QuecDuino EVB pin lookup with doc-table vs V1.0-silk dual mapping + conflict flags.
- `scripts/unirtos_compat_check.py` — static C lint: E1 `UNIRTOS_APP_EXPORT` registration, E2 no bare FreeRTOS/POSIX includes, E3 non-blocking init, W1 stack <1 KB, W2 blocking call in init, W3 sleep in init.
- `scripts/unirtos_flash_port_watch.py` — serial-port transition watcher; detects QDLoader (download-mode) enumeration.
- `references/troubleshooting.md` — symptom→fix matrix (flash/ports/build/logs/device), distilled from official FAQ + field lessons.
- `references/release-checklist.md` — code/build/device/documentation/delivery release gates.
- SKILL.md "docs-first rule": for any device bring-up/flash/log question, grep bundled `assets/docs-md/开发工具/` + `FAQ/` BEFORE improvising (the 短接5V+BOOT answer was in the bundled QFlash tutorial all along).
- Device-probe workflow: live port registry for this machine (remote-switch EC800K group off-limits; EVB group), EVB health snapshot.
- Board reference: V1.0 silk vs doc-table pin conflict table (D3/5/8/9/10–13/16/17, user LEDs PIN55/56, user keys PIN50/51), SPI/I2C group labels.

### Changed
- `references/flash-and-logs-workflow.md` — rewritten into two flash paths: 2a automated FlashToolCLI (recommended) and 2b QFlash GUI; added tooling-gotchas table (QFlash login gate, toolchain has no flasher, cmake 7z race workaround, setup.bat bin_i686 bug, EPAT direct URL).
- `references/device-probe-workflow.md` — added QDLoader role, port↔device attribution rules.
- SKILL.md — 7 scripts, 10 references, version + history table.

### Verified on hardware (2026-09-20, EG800Z QuecDuino EVB)
- `AT+QDOWNLOAD=1` → QDLoader (COM74) → 9-step FlashToolCLI burn: zero failures.
- Post-flash `ATI`: `Revision: QSR01A03_C_SDK_LTE_E_BETA20260511` (C SDK firmware replaced stock AT `R07A07M04`); `CustRevision: EG800ZCNLAR01A01_BETA_OCPU_20260512`.
- `[pkgflx0] ap_application.bin @0x258000` confirmed in regenerated `quec_download_usb.ini` = user app burned.
- Known behavior: unirtos_std AT set answers `AT+CGMM/CGMR` with ERROR — use `ATI` for identity.

### Fixed
- Doctor script GBK decode crash on zh-Windows consoles (`errors="replace"`).

## [1.0.0] — 2026-09-10

### Added
- Initial skill: scope for UniRTOS C development + device ops on Quectel EC718-family modules (EG800Z focus).
- Offline official docs: complete 125-page markdown set (`assets/docs-md/`) synced from docs.quectel.com Sphinx `_sources` (bypasses JS-rendered portal).
- SDK inventories: full file tree (1922 files) + 1197 QOSA/QCM header index (from gitee.com/UniRTOS mirror).
- References (8): core-rules (architecture mermaid, app-init registry, memory budget, license), build-workflow (unirtos-cli full reference, env_config schema, troubleshooting), api-index (feature→header→function map), board-eg800z-quecduino, flash-and-logs, device-probe (safety rules: remote-switch device off-limits, ATI-before-write), docs-workflow, vs-quecpython.
- Scripts (3): env_doctor, docs_fetch, com_probe (role classification + opt-in read-only ATI identification).
- Templates (5): main.c, env_config.json, CMakeLists, net_datacall, mqtt_uplink — aligned to real SDK headers (`qcm_mqtt_config_t` fields verified).
- gitee mirror strategy: `unirtos-cli git-mirror gitee`; SDK robust-fetch recipe (partial clone + raw-fill + object-store rebuild) after 7× clone failures.

### Environment notes
- Local machine: remote-switch device (EC800K + QuecPython, COM67–70) off-limits; EVB group COM71–73.
- Toolchain unirtos 1.0.5 at `C:\Users\kingd\unirtos-toolchain` (setup.bat xz path bug worked around); unirtos-cli 1.0.20; mirror=gitee.

## 1.2.0
| 2026-09-29 | troubleshooting 增补 ACM0 诊断/qurl TLS/nvitem 三组实战条目 |
