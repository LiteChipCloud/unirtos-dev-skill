# UniRTOS vs QuecPython

Both are Quectel application-layer ecosystems for overlapping module families (EC7xx/EG8xx/EC8xx). Choose deliberately; do not mix workflows.

## Decision table

| Dimension | UniRTOS (this skill) | QuecPython (`quecpython-dev` skill) |
| --- | --- | --- |
| Language | C (GCC cross-compile) | Python (MicroPython fork) |
| Kernel | FreeRTOS-based, kernel bin per platform | ThreadX (module-dependent) under MicroPython VM |
| Iteration | recompile + QFlash per change | script push to `/usr`, instant REPL |
| Footprint | tight control via menuconfig; ~800 KB flash budget | VM overhead; larger baseline |
| Determinism / timing | RTOS-grade, explicit stacks/priorities | GC pauses; softer timing |
| Access to low-level | full (HAL/QOSA, FOTA, SECBOOT, NV, LPM) | curated Python module set |
| Skill fit | performance/supply-chain/binary-delivery products | rapid prototyping, glue logic, tooling-heavy apps |
| Toolchain | unirtos-cli + 4.3 GB toolchain + QFlash/EPAT | QPYcom/qpy-vscode + REPL |
| Current modules | EC800Z-CN, EG800Z-EU/CN/LA/GL, EG915Z-EU (+EC718/QCX216 roadmap) | much wider model list |

## Rules of thumb

1. User names QuecPython/REPL/`.py` on device → `quecpython-dev`. User names UniRTOS/unirtos-cli/`.hbinpkg`/C on device → this skill.
2. Same physical board can host either firmware (e.g. EG800Z module ships AT/QuecPython/UniRTOS variants) — **the flashed firmware decides, not the hardware**. Identify before assuming: ATI revision ending `_QPY` = QuecPython; a UniRTOS build answers per its custom app (or stock AT via unirtos_std).
3. Never push QuecPython scripts to a UniRTOS device or vice versa; flashing chains differ (QFlash `.hbinpkg` vs `.bin` firmware packages) and wrong packages can brick the bootloader state.
4. Prototype in QuecPython when speed-of-iteration dominates and the model supports both; port to UniRTOS when binary delivery, memory budget, or deterministic behavior dominates. Port cost ≈ rewrite — plan the choice up front.
5. Coexistence on one host is fine: separate skills, separate tools, separate COM rules — always ATI-identify which firmware is on the port before touching it.
