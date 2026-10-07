---
name: unirtos-dev
version: 1.2.0
updated: 2026-09-29
description: UniRTOS (Quectel 统一 C 语言嵌入式 SDK) 设备开发与运维技能。当任务涉及 UniRTOS 应用开发（qosa_/qcm_/qurl_ C API）、unirtos-cli 工程（new/env-setup/build/menuconfig）、env_config.json、EG800Z/EC800Z/EG915Z 模组、EG800Z QuecDuino EVB/pico 开发板、QFlash 烧录 .hbinpkg、EPAT 日志抓取、QCOM AT 调试、蜂窝拨号 DataCall、MQTT/Socket 云对接时使用。用户提到 UniRTOS、unirtos-cli、QuecDuino、qosa API 或在 EG800Z 板子上做 C 开发时即应触发，即使用户没有明说 "UniRTOS"。
---

# UniRTOS Dev

## Scope

Use this skill to produce deployable UniRTOS C solutions for Quectel cellular modules — not generic embedded C snippets, and NOT QuecPython (that is a separate skill: `quecpython-dev`).
Apply it for both:
1. Device-side coding tasks (QOSA/QCM/QURL C APIs, `UNIRTOS_APP_EXPORT` entry registration, external app contract).
2. Device operations tasks (env-setup, build, QFlash flashing, EPAT log capture, AT probe, board bring-up).

Ground truth: current platform is `eigen_718` (EC718 chipset), kernel is FreeRTOS-based. Supported modules (SDK 1.0.x): EC800Z-CN, EG800Z-EU/CN/LA/GL, EG915Z-EU. The primary target on this machine is the **EG800Z QuecDuino EVB** (`EG800ZCN_LA` build target).

## Quick Workflow

1. Identify task mode:
   - Coding mode: app feature, peripheral driver use, network/cloud connect, bugfix, compatibility review.
   - Operations mode: environment check, project create, build, flash, log capture, device probe.
2. Capture required context before coding or commands:
   - Module model (e.g. EG800Z-CN), build target string (`EG800ZCN_LA`), SDK version, firmware version string, COM ports, board type.
3. **Docs-first rule for device operations**: for ANY bring-up/flash/log/mode-entry question, grep the bundled official docs FIRST — `assets/docs-md/开发工具/` (tool tutorials) and `assets/docs-md/FAQ/`. They contain the authoritative procedures (e.g. download-mode entry, port naming) and beat intuition. Reference: `references/troubleshooting.md`.
4. Run environment and device checks (read-only):
   - `python scripts/unirtos_env_doctor.py` — toolchain/CLI/SDK/mirror health.
   - `python scripts/unirtos_com_probe.py` — enumerate Quectel COM ports; only opens a port when the user explicitly asks to identify that specific port.
   - `python scripts/unirtos_device_info_probe.py --port COMx` — full read-only AT dossier (model/fw/IMEI/SIM/ICCID/signal/registration).
   - `python scripts/unirtos_flash_port_watch.py --wait 60` — wait for download-mode (QDLoader) enumeration during flashing.
5. For coding, follow the app contract:
   - Entry function registered with `UNIRTOS_APP_EXPORT(order, "name", init_fn)` (see `references/core-rules.md`).
   - Project layout + CMake + `env_config.json` from `assets/templates/` (see `references/build-workflow.md`).
   - `python scripts/unirtos_compat_check.py <app-dir>` before every delivery.
6. Choose APIs from the index, not from memory:
   - `references/api-index.md` maps features → `qosa_*.h` headers → exact repo paths; grep `assets/unirtos_qosa_headers.txt` for the full 1197-header inventory.
   - `python scripts/unirtos_pinmap_query.py --pin 19 | --header D0` — board pin lookup with doc-vs-silk conflict flags.
7. Build/flash/log per `references/build-workflow.md` and `references/flash-and-logs-workflow.md`; release per `references/release-checklist.md`.

## Rules First

Read `references/core-rules.md` before writing any device code. Hard constraints:
1. Device code is C (C11-era, GCC toolchain). Never propose Python-on-device; QuecPython is a different firmware.
2. Every app registers its entry via `UNIRTOS_APP_EXPORT(order_value, entry_name, entry_fn)`; init functions must be non-blocking (create a task, return).
3. Task stacks are small: default demo uses 1 KB; network tasks need ~4 KB. Module budget: ~1024 KB usable RAM, ~800 KB usable flash. Always set stack sizes explicitly.
4. Use only QOSA/QCM/QURL APIs (`qosa_task_*`, `qosa_gpio_*`, `qcm_mqtt_*`, `qcm_socket_*`, `qurl_*` ...). No direct FreeRTOS/pthread calls in app code.
5. Never flash, reset, or push firmware to an unidentified COM device. The other device on this machine (a remote switch unit running EC800K + QuecPython firmware) is off-limits — verify with ATI before any write action on any port.
6. In mainland-China environments set the git mirror once: `unirtos-cli git-mirror gitee` (GitHub is often unreachable).

## References Map

Load only the file needed for the current task:
1. `references/core-rules.md`: mandatory baseline, app init registry mechanics, memory limits, error-code conventions.
2. `references/build-workflow.md`: `unirtos-cli` full command reference, `env_config.json` schema, module targets, build output, menuconfig, troubleshooting.
3. `references/api-index.md`: feature → header → key functions map (QOSA system, HAL peripherals, DataCall, QCM MQTT/Socket/WebSocket, FOTA, NV, custom AT).
4. `references/board-eg800z-quecduino.md`: EG800Z QuecDuino EVB pin map (D0–D17 → module PINs), power, buttons, LEDs, UART/ADC wiring.
5. `references/flash-and-logs-workflow.md`: QFlash `.hbinpkg` flashing, EPAT log capture with `comdb.txt`, QCOM verification, version string conventions, tooling gotchas.
6. `references/device-probe-workflow.md`: COM port discovery, port-role classification (DIAG/AT/Modem/REPL/QDLoader), read-only identification, safety rules.
7. `references/docs-workflow.md`: offline doc lookup in `assets/docs-md/` (125 official pages) and refresh via `scripts/unirtos_docs_fetch.py`.
8. `references/vs-quecpython.md`: UniRTOS vs QuecPython decision table, coexistence notes, when to switch.
9. `references/troubleshooting.md`: symptom→fix matrix for flash/ports/build/logs/device issues (FAQ distillation + field lessons).
10. `references/release-checklist.md`: code/build/device/documentation/delivery gates for a shippable release.

When API behavior is uncertain:
1. Grep `assets/unirtos_qosa_headers.txt` to locate the header path.
2. Read the corresponding markdown in `assets/docs-md/` (API 说明 sections carry exact signatures).
3. Cross-check against the SDK source at `~/.unirtos/sdk/v<version>/qos_components/...` once env-setup has run.

## Scripts

1. Environment doctor (read-only health check):
```bash
python scripts/unirtos_env_doctor.py            # human-readable
python scripts/unirtos_env_doctor.py --json     # machine-readable
```
Checks python/git versions, `unirtos` toolchain, `unirtos-cli`, SDK root (`~/.unirtos`), installed SDK versions, git mirror setting.

2. Official docs fetch/refresh (downloads all pages as markdown):
```bash
python scripts/unirtos_docs_fetch.py --out assets/docs-md
python scripts/unirtos_docs_fetch.py --out review/docs --lang zh
```

3. COM port probe (enumeration is always safe; identification is opt-in per port):
```bash
python scripts/unirtos_com_probe.py                       # list ports, classify roles
python scripts/unirtos_com_probe.py --json                # machine-readable
# Identification (sends only ATI/CGMM/CGMR — read-only AT queries):
python scripts/unirtos_com_probe.py --identify COM70
```
The script refuses to open DIAG/REPL/Modem ports and refuses wildcard identification. Model strings not matching EG800Z/EC800Z/EG915Z family are reported as "foreign device — do not flash".

4. Full device info probe (read-only AT dossier):
```bash
python scripts/unirtos_device_info_probe.py --port COM73 --json
```

5. Flash port watcher (download-mode detection):
```bash
python scripts/unirtos_flash_port_watch.py --wait 60      # wait for QDLoader port
python scripts/unirtos_flash_port_watch.py --watch 30     # observe transitions
```

6. Compatibility checker (static C lint):
```bash
python scripts/unirtos_compat_check.py main/src
python scripts/unirtos_compat_check.py <app-dir> --json
```

7. Board pin map query:
```bash
python scripts/unirtos_pinmap_query.py --pin 19
python scripts/unirtos_pinmap_query.py --header 10 --json
```

## Assets

1. Templates (`assets/templates/`):
   - `main.template.c` — minimal app: QOSA task + QLOG logging + `UNIRTOS_APP_EXPORT`.
   - `env_config.template.json` — project config preset for `EG800ZCN_LA`.
   - `CMakeLists.template.txt` — external-app contract CMake (auto-globs `main/src`, `main/inc`).
   - `net_datacall_template.c` — cellular bootstrap: attach wait → PDP config → dial → event callbacks.
   - `mqtt_uplink_template.c` — QCM MQTT client: config → connect → subscribe → publish loop.
2. Offline docs: `assets/docs-md/` — full official UniRTOS doc set (125 pages, zh) + `_index.md.txt` catalog.
3. SDK inventories: `assets/unirtos_qosa_headers.txt` (1197 headers with repo paths), `assets/unirtos_sdk_file_tree.txt` (1922 files).

## Output Contract

When this skill is used for implementation:
1. Return buildable project code that follows the external-app contract (CMakeLists + env_config.json + main/src), and list host-side prerequisites separately (toolchain, SDK version).
2. Include explicit build/flash/run steps: `unirtos-cli env-setup` → `build -m <module>` → QFlash port + `.hbinpkg` path.
3. Include a rules check result (stack sizes, init registry, memory budget) or state why a check was skipped.
4. Never claim a device-side result without evidence: build log tail, EPAT/QCOM capture, or AT responses.

## Version History

Detailed change log: [CHANGELOG.md](CHANGELOG.md).

| Version | Date | Highlights |
| --- | --- | --- |
| 1.1.1 | 2026-09-20 | EPAT 自动连接脚本（pywinauto 消息级点击）+ DIAG 流/comdb 解码机制笔记 |
| 1.1.0 | 2026-09-20 | 全自动烧录配方验证落地（`AT+QDOWNLOAD=1` + FlashToolCLI 九步序列）；+4 脚本（device_info_probe / pinmap_query / compat_check / flash_port_watch）；+2 引用（troubleshooting / release-checklist）；docs-first 设备操作规则；V1.0 板丝印引脚差异表；本机设备安全注册表 |
| 1.0.0 | 2026-09-10 | 初版：125 页官方文档离线包、8 references、3 scripts、5 工程模板、SDK 文件树/1197 头文件索引、设备探针安全规则 |
