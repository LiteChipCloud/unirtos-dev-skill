# UniRTOS Build Workflow

Complete host-side toolchain reference. Sources: official `unirtos-cli使用教程`, SDK README_zh, unirtos-cli 1.0.20 source inspection.

## 1. Toolchain inventory (Windows)

| Tool | Purpose | Version baseline | Install |
| --- | --- | --- | --- |
| Python 3 | runs unirtos-cli | ≥3.9 | python.org, add to PATH |
| Git | pulls SDK/libs/demos | ≥2.20 | git-scm.com |
| **unirtos-toolchain** | provides `unirtos` command → `unirtos make` (CMake + Ninja/Make driver) | ≥1.0.5 | `unirtos-toolchain.exe` from quectel.com.cn download zone; default dir `D:\unirtos-toolchain`; ~4.3 GB |
| unirtos-cli | project/env/build orchestration | ≥1.0.15 (PyPI latest 1.0.20) | `pip install unirtos-cli` |
| QFlash | firmware flashing (.hbinpkg) | V7.9+/V8.x | quectel.com.cn download zone |
| EPAT | log capture (UniLogViewer) | per download | quectel.com.cn download zone |
| QCOM | AT serial debugging | V1.8 | quectel.com.cn download zone |
| Quectel USB driver | COM port enumeration | V1.0 | quectel.com.cn download zone |
| VS Code + UniRTOS extension | IDE integration (optional) | — | UniRTOS-vscode-Extension repo / marketplace |

Verification one-liner:
```bash
python --version && git --version && unirtos --version && unirtos-cli version
```

Mirror (mainland China / blocked GitHub): `unirtos-cli git-mirror gitee` — stored in `~/.unirtos/.unirtosconfig`; all manifest/demo/sdk fetches follow it. Query current: `unirtos-cli git-mirror`.

## 2. Standard project lifecycle

```bash
# 1) create project (template mode) or from official demo
unirtos-cli new unirtos-app                 # template, auto-pins latest sdk.version
unirtos-cli new -r unirtos_helloworld_demos # demo mode (45 demos available)
#    options: -v 1.0.0 (demo version), -d <base-dir>, -f (force refresh demo manifest)

cd unirtos-app
# 2) edit env_config.json (module + sdk version + libraries)

unirtos-cli env-setup                       # pull SDK + libs to ~/.unirtos, emit .code-workspace
unirtos-cli menuconfig                      # Kconfig feature switches (optional)
unirtos-cli build                           # compile → qos_build/release/<version>/
unirtos-cli clean                           # remove qos_build/
```

`env-setup` generates `<app>.code-workspace` opening app + SDK + libraries together in VS Code.

## 3. env_config.json schema

```json
{
  "unirtos_root": "",
  "build": {
    "module": "EG800ZCN_LA",
    "version": "EG800ZCNLAR01A01_BETA_OCPU_20260513",
    "jobs": 8
  },
  "sdk": { "version": "1.0.5" },
  "libraries": {
    "list": [ { "name": "lib-name", "version": "2.0.0" } ]
  }
}
```

| Field | Required | Meaning |
| --- | --- | --- |
| `unirtos_root` | no | absolute override for SDK storage; default `C:\Users\<user>\.unirtos` |
| `build.module` | **yes** | build target string, e.g. `EG800ZCN_LA` → `unirtos make --project` |
| `build.version` | no | firmware version string → output folder `qos_build/release/<version>/`; fallback: app folder name |
| `build.jobs` | no | parallel jobs, default 4 (`-j` overrides) |
| `sdk.version` | **yes** | checked out from manifest tag `v<version>` |
| `libraries.list[]` | no | `{name, version}`; names must exist in unirtos-libs-manifests; linked into app automatically via CMake |

Environment variables injected by CLI at build (do not set manually): `UNIRTOS_EXTERNAL_APP_DIR`, `UNIRTOS_EXTERNAL_APP_NAME`, `UNIRTOS_ROOT`, `UNIRTOS_APP_TARGET_NAME`, `UNIRTOS_LIBRARIES_JSON`.

## 4. Build command matrix

```bash
unirtos-cli build                                              # use env_config defaults
unirtos-cli build -m EG800ZCN_LA -j 8                          # override module/jobs
unirtos-cli build -m EG800ZCN_LA -v EG800ZCNLAR01A01_OCPU_20260625
```

Known-good baseline for the local EG800Z QuecDuino EVB: `build.module = EG800ZCN_LA`, first verified SDK `1.0.1` (hello demo), docs verified against `1.0.5`.

Output layout:
```
<project>/qos_build/release/<version>/
├── <version>.hbinpkg      ← flash this with QFlash
└── <version>/DBG/comdb.txt ← load into EPAT for symbolized logs
```

## 5. SDK storage layout (`~/.unirtos`)

```
~/.unirtos/
├── .unirtosconfig          # global mirror config {"git_mirror": "gitee"}
├── sdk/
│   ├── manifests/          # unirtos-sdk-manifests clone (v1.0.1..v1.0.5)
│   └── v1.0.5/             # SDK checkout (git tag v1.0.5)
│       ├── cmake/  qos_applications/  qos_components/  qos_kernel/eigen_718/  qos_tools/
│       ├── Kconfig  build.sh  CMakeLists.txt  LICENSE
│       └── (kernel bins live here — explains the large clone)
├── libraries/<lib>/v<x>/   # dependency libraries
└── demos/manifests/        # unirtos-demos-manifests clone (45 demos)
```

SDK directory semantics (top level): `cmake` build system extensions; `qos_applications` app entry + built-in demos + `unirtos_std` standard AT app; `qos_components` open components (`components/`: mbedtls, ping, qcm_file, qcm_mqtt, qcm_ntp, qcm_uart_log, qcm_virt_at, qcm_websocket, qurl, socket, utils, vtls) + system services & HAL (`system/`: at, audio, cam, debug, dev, flash, fota, ftm, hal, modem ...); `qos_kernel` platform adaptation; `qos_tools` build/config/packaging python tools.

## 6. Discovery commands

```bash
unirtos-cli ls-sdk          # installed SDK versions (local cache)
unirtos-cli ls-sdk -r [-f] [-j]  # remote versions from manifest (-f force refresh, 1h cache)
unirtos-cli ls-libs [-r] [-f] [-j]
unirtos-cli ls-demos [-f] [-j]   # 45 official demos, e.g. gpio/uart/mqtt/sms/aliyun/lpm/lvgl...
```

Demo catalog highlights (unirtos-demos-manifests): `unirtos_helloworld_demos`, gpio, uart, adc, pwm, iic, spi, lcd, camera, audio, tts, voice-call, rtc, lpm, network, mqtt, websocket, qurl-http, dmhttp, ntp, ping, sms, sim, qvsim, at, virt-at, usb, usbnet, file, vfs, builtin-flash, fota(?), secboot, dump-flash-upload, lbs, wifiscan, xlat, pwrkey, jammed-detect, aliyun, maker-examples, quecduino-sensor-kit, lvgl.

## 7. Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `unirtos: command not found` after toolchain install | PATH missing | reopen shell; add toolchain bin dir to PATH |
| `unirtos make execution failed` | toolchain missing/mismatch | reinstall `unirtos-toolchain.exe`, verify `unirtos --version` |
| `Configured SDK version does not exist in manifests` | stale manifest cache or typo | `unirtos-cli ls-sdk -r -f -j`; fix `sdk.version` in env_config.json |
| git clone timeouts | GitHub unreachable | `unirtos-cli git-mirror gitee`, retry |
| clone `early EOF` / archive truncated | large SDK over flaky network | use gitee mirror; retry; avoid VPN fragmentation |
| build picks wrong module | env_config vs CLI flag mismatch | CLI flags win; keep `build.module` authoritative for the project |
| EPAT shows garbage/no logs | wrong port or comdb mismatch | DIAG port + `comdb.txt` from the exact `qos_build/release/<version>/DBG` |
