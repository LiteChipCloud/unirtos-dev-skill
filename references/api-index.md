# UniRTOS API Index

Feature → header → key functions. Paths are relative to the SDK root (`~/.unirtos/sdk/v<version>/`). Full inventory: grep `assets/unirtos_qosa_headers.txt` (1197 headers). Exact signatures: read the matching page in `assets/docs-md/` (每页含"API说明/函数详解"), then confirm against the header itself.

Naming conventions: `qosa_*` = system/HAL abstraction; `qcm_*` = communication components (mqtt/socket/websocket/file/ntp/virt-at); `qurl_*` = high-level URL/HTTP client; `QLOG*` = logging; `UNIRTOS_APP_EXPORT` = entry registry.

## QOSA system core — `qos_components/system/...` (docs: 系统功能/)

| Feature | Header | Key functions |
| --- | --- | --- |
| Tasks | `qosa_sys.h` | `qosa_task_create/_static/_delete/_suspend/_resume/_get_current_ref`, `qosa_task_sleep_ms/_sec`; `QOSA_PRIORITY_NORMAL` |
| Semaphore | `qosa_sys.h` | `qosa_sem_create/_wait/_post/_delete` |
| Mutex | `qosa_sys.h` | `qosa_mutex_create/_lock/_unlock/_delete` |
| Msg queue | `qosa_sys.h` | `qosa_msgq_create/_send/_recv/_delete` |
| Event flags | `qosa_sys.h` | `qosa_event_create/_notify_register/_wait/_delete` |
| Timers | `qosa_sys.h` | soft timer APIs (docs: 定时器应用指导) |
| Heap | `qosa_sys.h` | `qosa_malloc/_free/_memset/_memcpy` (docs: 内存堆管理) |
| Log | `system/debug/qosa_log.h` | `QLOGV/D/I/W/E`, `QOS_LOG_TAG` |
| Errors/types | `qosa_def.h`, `qosa_errno.h` | `QOSA_OK`, `qosa_uint8_t`..., `QOSA_TRUE/FALSE` |
| System time | `qosa_sys.h` | docs: 系统时间 |
| Power on/off | `system/hal/qosa_power.h` | docs: 开关机 |
| LPM | `system/hal/qosa_lpm.h` | low-power modes (docs: 低功耗应用指导) |
| FOTA | `system/fota/qosa_fota.h` | firmware upgrade over the air (docs: FOTA升级) |
| NV config | `qosa_nv.h`(tree: qos_tools/... or system) | NV parameter store (docs: NV配置开发指南) |
| SECBOOT | `qosa_secboot.h`(tree) | secure boot (docs: SECBOOT) |
| Custom AT | `system/at/qosa_at_cmd.h` + `qcm_virt_at` | user AT command registration (docs: 自定义AT开发指南) |
| RNG | `qosa_sys.h` | docs: 随机数 |
| VFS/File | `qosa_vfs.h`/`qcm_file` | file I/O (docs: 文件系统) |

## HAL peripherals — `qos_components/system/hal/` (docs: 外设与驱动/)

| Peripheral | Header | Key functions |
| --- | --- | --- |
| GPIO | `qosa_gpio.h` + `qosa_pinctrl.h` | `qosa_get_pin_default_cfg(pin,&cfg)` → `qosa_pin_set_func(pin,cfg.gpio_func)` → **`qosa_gpio_init(cfg.gpio_num,dir,pull,level)`** — GPIO calls use `cfg.gpio_num` (the GPIO-space number mapped from the PIN), **never the raw PIN number** (field-verified: using `QOSA_GPIO_55` for PIN55 does not drive the pin) |
| UART | `qosa_uart.h` | `qosa_uart_open/close/write/read/_read_available/_write_available/_register_cb/_check_support_baudrate/_ioctl`; ports `QOSA_UART_PORT_0..3`, `QOSA_USB_PORT_AT/MODEM/NMEA/ACM0` |
| ADC | `qosa_adc.h` | `qosa_adc_get_volt()` (0–1.2 V range on EVB A0/A1) |
| PWM | `qosa_pwm.h` | PWM output |
| I2C | `qosa_iic.h` | `qosa_i2c_init()` ... |
| SPI | `qosa_spi.h` | SPI master |
| RTC | `qosa_rtc.h` | real-time clock |
| HW timer | `qosa_hw_timer.h` | hardware timers |
| LCD/Camera | `qosa_lcd.h`, `qosa_camera.h` | display/camera (platform-dependent) |
| USB | `qosa_usb.h` | USB stack |
| Built-in flash | `qosa_built_in_flash.h` | internal flash access |
| Flash | `system/flash/qosa_flash.h` | flash partition ops |

## Cellular networking — `qos_components/system/modem/include/` (docs: 网络与通信/)

| Feature | Header | Key functions |
| --- | --- | --- |
| DataCall (dial) | `qosa_datacall.h` | `qosa_datacall_attach/_wait_attached(simid,timeout)`, `_set_pdp_context/_get_pdp_context`, `_set_pdp_auth`, `_conn_new`, `_start/_start_async`, `_stop`, `_get_status`, `_get_ip_info`, `_get/set_dns_addr`, `_get_traffic_statistics`; events `QOSA_EVENT_NW_PDN_DEACT` etc. via `qosa_event_notify_register` |
| SIM | `qosa_sim.h` | SIM status/ICCID/IMSI (docs: SIM, eSIM, QVSIM) |
| SMS | `qosa_sms.h` | send/read SMS (docs: SMS) |
| Voice call | `qosa_voice_call.h` | dial/answer/hangup |
| CLAT | `qosa_clat.h` | IPv6-only networks / 464XLAT (docs via xlat demo) |
| USBNET | `qosa_usbnet.h` | module as USB NIC (docs: USBNET功能) |
| Network utils | `qosa_ip_addr.h`, `qosa_network.h` | `qosa_ip_addr_inet_ntop()` |
| GNSS/LBS/WiFi scan | platform headers | docs: 定位应用 (GNSS定位/基站定位/Wi-Fi Scan) |

## QCM communication components — `qos_components/components/` (docs: 网络协议/)

| Feature | Header/component | Key functions |
| --- | --- | --- |
| Socket TCP/UDP(+SSL) | `socket/` (docs: Socket) | `qcm_socket_create/_connect/_read/_send/_listen/_accept/_close/_sendto/_recvfrom`, `qcm_socket_ssl_config/_ssl_connect`, `qcm_socket_set_opt/_get_opt`, `qcm_socket_register_event` |
| MQTT (3.1.1/5.0) | `qcm_mqtt/` (docs: MQTT) | `qcm_mqtt_client_default_config/_create/_init/_open/_connect/_subscribe/_unsubscribe/_publish/_disconnect/_close/_wait_read_cnt`; event cb via init |
| HTTP(S) | `qurl/` (docs: HTTP_HTTPS) | `qurl_*` high-level client; `dmhttp` low-level |
| WebSocket | `qcm_websocket/` (docs: WebSocket) | ws client |
| NTP | `qcm_ntp/` (docs: NTP) | time sync |
| FTP/SMTP/Ping/DNS | components + docs | 网络协议 chapter |
| TLS | `vtls/` + `components/mbedtls/` | docs: SSL_TLS |
| Crypto | mbedtls wrappers | docs: 加解密协议 (AES/DES_3DES/RSA/Hash/ECDH/ECDSA) |
| Aliyun IoT | docs: AliYun平台 + aliyun demo | MQTT-based cloud connect |

## Standard AT app — `qos_applications/unirtos_std/`

UniRTOS builds ship a standard AT firmware (`unirtos_std`, sources `src/unirtos_atcmd_*.c`: datacall, file, ftp, coap, clat ...). If the flashed image is the stock AT firmware, control it from the host via QCOM/serial AT commands; user AT commands extend it via 自定义AT开发指南.

## Missing-an-API protocol

1. `grep -i <keyword> assets/unirtos_qosa_headers.txt` for candidate headers.
2. Read the header in the SDK checkout (`~/.unirtos/sdk/v<version>/<path>`).
3. If absent in docs, mark the usage "unverified" in your output and verify on-target via EPAT logs before delivery.
