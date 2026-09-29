# UniRTOS Troubleshooting

Distilled from official FAQ (assets/docs-md/FAQ/), tool tutorials, and local bring-up experience (2026-09-10). **Rule: before improvising a bring-up/flash answer, grep `assets/docs-md/开发工具/` + `assets/docs-md/FAQ/` — the official procedure is bundled and wins over intuition.**

## Flash & download mode

| Symptom | Root cause | Fix |
| --- | --- | --- |
| 烧录工具"未检测到模块" | Module still in normal AT mode — download mode never entered | **软件法（推荐）：AT 口发 `AT+QDOWNLOAD=1`**，等 QDLoader 口出现立即烧录；**接线法（QFlash 教程）**：短接 5V 和 BOOT 排针再上电 |
| QDLoader port appeared then vanished | Download mode boot-ROM timeout (~1–2 min, no host activity) | Enter download mode and start the burn sequence in one continuous script (see flash_now.py pattern) |
| FlashToolCLI `[com open fail]` despite free port | cfg missing line entries (hand-made config.ini) | Do NOT handcraft config.ini — pass `--cfgfile <release>/quec_download_usb.ini`; run `pkg2img` first to generate concrete paths |
| QDLoader port never appears | Power off; USB cable; short not making contact | Check POW LED; long-press PWK ON to boot WITH short in place; try re-seat cable; keep short until mode entered |
| 下载固件失败，请检查模块和固件包 | Wrong port selected (e.g. another device's AT port) or package mismatch | Verify the module answers ATI on that port FIRST; ensure `.hbinpkg` matches module (EG800ZCN_LA build); never flash an unidentified port |
| Flash PASS but module dead | Wrong-model package or interrupted transfer | Confirm `.hbinpkg` suffix and model; reflash; check供电稳定 (QFlash FAQ) |
| QFlash local version can't load `.hbinpkg` | QFlash <V8 predates EC718 platform | Use QFlash V8 (login-gated download) **or QPYcom ≥3.9 下载固件** (same protocol, supports EG800Z) |

## Ports & drivers

| Symptom | Fix |
| --- | --- |
| No "Quectel" ports in Device Manager | Install Quectel Windows USB driver (V1.0); check 未知设备 with yellow mark (QFlash FAQ) |
| COM numbers change on replug | Never trust stale numbers — re-run `scripts/unirtos_com_probe.py` and identify by ATI before ANY write |
| Two Quectel devices look identical | VID/PID `2C7C:6002` is shared; only ATI response distinguishes models |
| Port busy / cannot open | Close other tools holding the port (QPYcom/EPAT/python sessions); `unirtos_com_probe.py` enumerates without opening |

## Environment & build

| Symptom | Fix |
| --- | --- |
| `unirtos: command not found` | Toolchain bin not on PATH; setup.bat may have failed (its xz path bug) — see gotchas table in `flash-and-logs-workflow.md` |
| SDK clone "early EOF" repeatedly | gitee kills big pack transfers. Robust recipe: partial clone (`--filter=blob:limit=200k`) + lazy per-blob fetch via checkout, or raw-file fill + `git hash-object -w` to rebuild the object store; then disable promisor |
| cmake "Failed to extract archive.7z" at toolchain.cmake:121 | Pre-extract `qos_build/gccout/images/firmware_base_release_pack.7z` into its sibling dir; rebuild (cmake reuses it) |
| `Configured SDK version does not exist` | `unirtos-cli ls-sdk -r -f -j`; fix `sdk.version` in env_config.json |
| GitHub unreachable (CN) | `unirtos-cli git-mirror gitee` |

## Logs & debug

| Symptom | Fix |
| --- | --- |
| EPAT no logs / garbage | Wrong port (use DIAG port) or comdb.txt mismatch — comdb must come from the exact `qos_build/release/<version>/DBG` |
| App logs missing in EPAT | App entry not registered (see E1) or QLOG_TAG confusion; boot shows `app init: <name>` lines when registered |
| Module won't boot to app | Boot order values conflict; init fn blocked (E3); stack too small (W1) — run `scripts/unirtos_compat_check.py` |
| **App crashes but no fault info anywhere** | USB CDC TX buffer loses the last lines at hardfault — pre-crash logs vanish. Use the ACM0 self-report channel (below) |
| **Reboot right at a specific call** (no diag printed) | Suspect hidden traps: uninitialized struct passed to SDK (`qurl_tls_cfg_t` MUST be `= {0}`), libc malloc paths in app context — audit before stack-size theories |

### ACM0 self-report channel (field-proven 2026-09-29)

When EPAT+comdb is unavailable/mismatched, make the app narrate itself over the dormant
`USB 串行设备` COM port (QOSA_USB_PORT_ACM0):

```c
#include "qosa_uart.h"
qosa_uart_open(QOSA_USB_PORT_ACM0);           // USB settle is racy — retry ×10 @500ms
qosa_uart_write(QOSA_USB_PORT_ACM0, buf, len); // printf-style diag helper on top
```

PC side: open that COM at 115200. Boot trace + every bringup step + tool calls become
plain text. **Caveat: lines still in the TX buffer are LOST on hardfault** — a missing
diag means "crashed before flush", not "never executed". This channel cracked 10 real
bugs in one session (datacall/MQTT/TLS/Lua-coroutine stack). Worth wiring into any
bring-up firmware as `claw_diag.c`-style module.

## Networking & TLS (field notes 2026-09-29, EG800Z + LiteGate)

| Symptom | Root cause | Fix |
| --- | --- | --- |
| MQTT fine but qurl HTTP fails `0x80010018` (NETWORK_ERR) | qurl default `nw_id=-1` (PDP unspecified) → "PDP not activated" | `qurl_core_setopt(core, QURL_OPT_NETWORK_ID, 1L)` — bind to the CID you dialed |
| qurl HTTPS fails `0x8001008c` (TLS_CONNECT_ERR) but TLS1.2 server-accepted from PC | **qurl sends no SNI** → modern CDN default vhost serves ECDSA-only suites → device mbedtls mini config lacks ECDSA → handshake dead | `tls_cfg.bits.sni_enable = 1` (host taken from URL) |
| Hard reboot on first qurl perform | `qurl_tls_cfg_t` on stack WITHOUT `= {0}` → garbage into mbedtls | zero-init before `qurl_tls_cfg_init` (official examples do `{0}`) |
| POST body ignored (`0x80010008` misread as data issue) | rc decode trap: -2147418088 is `0x80010018` NETWORK_ERR, NOT `0x80010008` | decode unsigned hex before naming the enum |
| glm tool args extracted wrong/URL garbage | args JSON key order differs (glm: arguments BEFORE name); uninit buffers show stack residue | anchor on `"function":{` block, order-independent extract; zero every buffer |
| Datacall never attaches (camps LTE fine) | missing explicit PDP context | official example sequence: sleep 3s → wait_attached → **set_pdp_context** → conn_new → start |
| Lua skill dispatch "cannot resume dead coroutine" | claw_on_cmd pushed on MAIN lua stack, not the coroutine's | `lua_getglobal(g_co, fn)` after `lua_newthread`; keep thread anchored on g_L while suspended (GC) |

## Lua hot-update over MQTT (field notes 2026-09-29)

| Symptom | Root cause | Fix |
| --- | --- | --- |
| hotload "OK" but no skill defined | line-append WITHOUT newline: whole chunk on one line, leading `--` comments everything; empty chunk compiles as VALID Lua | append newline per line |
| lua_resume OK but skill never ran | no-skill fallback path also returns OK — false positive | make no-skill path report back via claw.say |
| lines containing escaped quotes truncated (unfinished string) | flat json_str uses strchr — stops at escaped quote inside value | escape-aware end scan (skip backslash pairs) |
| MQTT chunked upload loses messages | rapid qos1 publishes drop on public broker | per-line ACK with tail-8 verification + resend |
| /user files after reflash | they SURVIVE reflash (unlike pkgflx) | reflash is not factory reset for /user |

## NVM / nvitem (field notes 2026-09-29)

| Symptom | Root cause | Fix |
| --- | --- | --- |
| write returns `0x80050003` PATH_ERROR | name must be `file.json/config/node` (3-segment), not `file.json/node` | probe on device if unsure; `.json` + `/config/` + node |
| read returns `0x80050005` NO_SEARCH right after successful write | **read value_size must EXACTLY equal stored length** (doc note) | use FIXED sizes both sides: zero-fill buffer, write sizeof(buf), read sizeof(buf) |
| Config lost after reflash | nvitem JSON lives in pkgflx partition — flashing erases it | expected "factory reset"; power-cycle preserves |

## Device behavior

| Symptom | Fix |
| --- | --- |
| CPIN/QCCID → CME ERROR 10 | No SIM (or tray empty). Insert NANO SIM for network work; GPIO/build work unaffected |
| Attach/registration fails | Signal first (AT+CSQ; >10 ≈ usable), then SIM state, then APN (qosa_datacall_set_pdp_context) |
| Module "off" after USB plug | USB powers but does NOT boot — long-press PWK ON (~2s) |
