# UniRTOS Release Readiness Checklist

Quality gates before declaring a UniRTOS deliverable done. Adapted from `quecpython-dev` commercial-readiness practice + UniRTOS specifics.

## 1. Code gates

- [ ] `python scripts/unirtos_compat_check.py <app-dir>` — 0 errors (E1 entry registered, E2 no bare FreeRTOS includes, E3 init non-blocking)
- [ ] Stack sizes reviewed per task (network ≥4 KB, MQTT/TLS ≥6 KB; total RAM < ~1024 KB budget with headroom)
- [ ] Return codes checked and QLOG-logged on all qosa_/qcm_ calls (no fire-and-forget)
- [ ] Error/reconnect paths exercised: datacall drop → redial; MQTT disconnect → re-open
- [ ] menuconfig trimmed for flash budget (~800 KB usable): unused components off (camera/audio/GNSS...)

## 2. Build gates

- [ ] Clean build from scratch: `unirtos-cli clean && unirtos-cli build -m <module> -v <version-string>`
- [ ] Version string follows convention `EG800ZCNLARxxAxx[_BETA]_SKU_YYYYMMDD` and is recorded
- [ ] Artifacts present: `<version>.hbinpkg` + `DBG/comdb.txt` + elf/map (archive DBG with the release)
- [ ] Build log archived under `<project>/review/`

## 3. Device gates (evidence required, not claims)

- [ ] Flash PASS (QFlash/QPYcom log or screenshot) on the verified target port
- [ ] Post-flash identity: `ATI` revision shows the new version string
- [ ] EPAT capture with matching comdb shows app QLOG lines (or `app init:` boot lines at minimum)
- [ ] Soak: key path stable ≥ N hours/days as the product requires (log capture archived)
- [ ] FOTA path validated if the product updates in field (FOTA升级 doc + signed package)

## 4. Documentation gates

- [ ] README: build/flash/log steps with the exact module target and versions used
- [ ] Pin usage table for the specific board revision (V1.0 silk mapping) recorded in project docs
- [ ] Known limitations + troubleshooting appendix linking skill references
- [ ] License note: SDK is Quectel Custom Source License — confirm redistribution terms before shipping source

## 5. Delivery

- [ ] Deliverable reviewed/accepted by the requester: device + firmware + docs + evidence pack
- [ ] Evidence pack: build log, flash PASS, EPAT capture, AT transcripts — under `<project>/review/`
