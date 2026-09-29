# EG800Z QuecDuino EVB Board Reference

Source: official docs `assets/docs-md/开发板介绍/QuecDuino开发板介绍/QuecDuino开发板介绍.md`. Companion board: pico 开发板 (docs same folder) — check which board the user actually has before pin-level work.

## 1. Board identity

| Item | Value |
| --- | --- |
| Name | EG800Z QuecDuino EVB |
| Module | EG800Z series (EG800ZCNXX / EG800ZEUXX / EG800ZGL), LTE Cat.1, optional GNSS (GPS/BDS/GLONASS/Galileo) |
| Form factor | Arduino-standard female-header PCB + 4G FPC antenna |
| USB | Type-C USB 2.0 — power + flash + AT + debug (single cable workflow) |
| Power in | Type-C 5V / DC jack 5–16 V / pin header 5V (V1.1: header 5V pins NC!) ; 3.3 V/200 mA out |
| GPIO | 22 × digital, 3.3 V logic |
| ADC | 2 ch, 12-bit, **input range 0–1.2 V only** |
| Keys | 3 function keys + RST + BOOT (force download mode) |
| LEDs | 4 (power, network status, 2 user-defined) |
| SIM | NANO slot, 1.8/3.0 V |
| Audio (optional) | onboard MIC + 3 W Class-D amp |
| Serial | 4 × UART, 1 × SPI, 1 × I2C; main UART up to 921600 bps |

## 2. Arduino header pin map (module PIN numbers)

| Header | Module pin | Function |
| --- | --- | --- |
| BOOT | BOOT | USB_BOOT (force download with pull per module) |
| RST | RESET | low = reset |
| 3.3V | — | 3.3 V/200 mA output |
| 5V | — | 5 V/2A in/out (NC on V1.1) |
| A0 | ADC0 | analog in 0–1.2 V |
| A1 | ADC1 | analog in 0–1.2 V |
| D0 | PIN19 | GPIO |
| D1 | PIN20 | GPIO |
| D2 | PIN21 | GPIO |
| D3 | PIN25 | GPIO |
| 0 | RXD2 | **main UART** receive |
| 1 | TXD2 | **main UART** transmit |
| 2 | RXD0 | auxiliary UART receive |
| 3 | TXD0 | auxiliary UART transmit |
| D4 | PIN23 | GPIO |
| D5 | PIN22 | GPIO |
| D6 | PIN28 | GPIO |
| D7 | PIN29 | GPIO |
| D8 | PIN58 | GPIO |
| D9 | PIN80 | GPIO |
| D10 | PIN31 | GPIO |
| D11 | PIN32 | GPIO |
| D12 | PIN33 | GPIO |
| D13 | PIN30 | GPIO |
| D14 | GND | ground |
| D15 | NC | — |
| D16 | PIN66 | GPIO |
| D17 | PIN67 | GPIO |

GPIO code uses the **module PIN number** (e.g. `#define LED_PIN_NUM 19` for D0), not the D-number — see official LED demo.

### ⚠ Doc-table vs V1.0 silk discrepancy

The official doc table above and the user's physical board silk (EG800Z QuecDuino EVB **V1.0**) disagree on several pins. Verified from the V1.0 board diagram (2026-09-10):

| Header | Doc table | V1.0 silk (actual board) |
| --- | --- | --- |
| D3 | PIN25 | **PIN22** |
| 5 | PIN22 | **PIN25** |
| 8 / 9 | PIN58 / PIN80 | **PIN66 / PIN67** |
| 10–13 | PIN31/32/33/30 | **PIN64 / PIN63 / PIN62 / PIN49** |
| 16 / 17 | PIN66 / PIN67 | **PIN58 / PIN57** |
| User LEDs D3/D4 | — | PIN55 / PIN56 |
| User keys S2/S3 | — | PIN50 / PIN51 (S1 = PWKEY) |

**Field-confirmed (2026-09-20)**: D3=PIN55 / D4=PIN56 verified controllable via GPIO — requires the correct mapping: `qosa_get_pin_default_cfg(pin,&cfg)` → `cfg.gpio_num` → `qosa_gpio_init/set_level(cfg.gpio_num,...)`. Raw `QOSA_GPIO_55` enum does NOT drive PIN55 (GPIO-space ≠ PIN-space). Alternate-blink demo: unirtos-led-mqtt project.

Additional V1.0-only labels: SPI group CLK/MISO/MOSI/CS and I2C SCL/SDA, `VUSB_EN`/`VBAT_EN` jumpers, `PA_EN`. **Rule: for pin-level work on this V1.0 board, trust the silk/diagram; verify with a multimeter or a safe output-low test before wiring external hardware, and record which mapping you coded against.**

## 3. Workflows on this board

1. Power on: long-press power key; verify "Quectel" ports appear in Device Manager.
2. First firmware: module ships with AT firmware; UniRTOS dev flow = build app → QFlash `.hbinpkg` over AT port.
3. Serial: main UART (header 0/1, UART2) is the app/log surface; USB AT port is flash + AT; USB DIAG port is EPAT logs.
4. LED blink sanity check: D0 (PIN19) with `qosa_gpio_init` output — mirrors official 点亮LED demo.
5. Button/ADC: map function keys and A0/A1 via `qosa_gpio`/`qosa_adc` headers; respect the 1.2 V ADC ceiling — use a divider for 3.3 V signals.

## 4. Build target mapping

| Board module | env_config `build.module` |
| --- | --- |
| EG800Z-CN (this EVB, China) | `EG800ZCN_LA` |
| EG800Z-EU / GL / LA | check `unirtos make --project` list in toolchain; docs only exemplify EG800ZCN_LA |
| EC800Z-CN / EG915Z-EU | analogous target strings; verify via `ls-sdk`/toolchain docs before use |
