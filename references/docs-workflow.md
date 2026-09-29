# Docs Workflow

Offline-first official documentation strategy.

## 1. Offline docs (bundled)

`assets/docs-md/` contains the complete official UniRTOS doc set (zh), 125 markdown pages, synced 2026-09-10, plus `_index.md.txt` (the site catalog). Structure:

| Folder | Content |
| --- | --- |
| `UniRTOS概述/` | introduction, architecture, supported model list |
| `快速上手/` | 开发准备/环境搭建/Hello World/编译工程/烧录固件/日志调试 |
| `系统功能/` | 多线程, 内存堆管理, 同步与通信(信号量/互斥锁/消息队列/事件标志), 定时器, 低功耗, 开关机, 文件系统, 日志, 系统时间, 随机数, NV配置, SECBOOT, FOTA升级, 自定义AT |
| `外设与驱动/` | ADC, Audio, GPIO, IIC, LCD, PWM, RTC, SPI, UART, USB |
| `网络与通信/` | SIM/eSIM/QVSIM/SMS, DataCall拨号, 蜂窝网络, USBNET, 网络协议(Socket/MQTT/HTTP/FTP/SMTP/NTP/Ping/DNS/SSL_TLS/WebSocket), 加解密协议, 定位应用 |
| `应用开发指南/` | 应用程序开发(app contract), 快速连接蜂窝网络, 点亮LED, 程序异常处理, Dump处理, 一键功能, AliYun对接 |
| `开发工具/` | unirtos-cli/QCOM/QFlash/EPAT/FOTA/QMulti_DL/VS Code 教程 |
| `开发板介绍/` | QuecDuino EVB, pico 开发板 |
| `FAQ/` | 环境/硬件/网络/软件开发常见问题 |

Lookup pattern:
1. `grep -rl "qosa_gpio_init" assets/docs-md/` → find the API page.
2. Read the page's `API说明/函数详解` for exact signatures, return codes, and example code.
3. Image placeholders (`{image} ...`) reference webp assets not bundled — ignore; all normative content is text/tables.

## 2. Refresh (re-sync from official site)

```bash
python <skill>/scripts/unirtos_docs_fetch.py --out <skill>/assets/docs-md
```

Downloads `https://docs.quectel.com/zh/UniRTOS/UniRTOS文档/_sources/index.md.txt` + every linked page as markdown. The site is Sphinx-based; `_sources/*.md.txt` is the stable raw-source pattern (also works for en if a `en/` mirror appears). Cache hint: run at most once per session; pages change with SDK releases (check 修订记录 page).

## 3. Online supplements

- Portal (JS-rendered, do not scrape): `https://www.quectel.com.cn/unirtos/docs`
- Docs static site: `https://docs.quectel.com/zh/UniRTOS/UniRTOS文档/index.html`
- GitHub org: `https://github.com/orgs/UniRTOS/repositories` (49 repos: SDK, 45 demos, VS Code extension, manifests) — mainland mirror `https://gitee.com/UniRTOS/` (identical, use when GitHub is blocked)
- Downloads (toolchain/QFlash/EPAT/QCOM/driver): `https://www.quectel.com.cn/download/...` links listed in 快速上手/开发准备
- Forum: `https://forumschinese.quectel.com/c/66-category/66`

## 4. Version pinning

Docs evolve with SDK (修订记录 page tracks changes). When behavior differs between the bundled docs and the installed SDK:
1. Trust the **installed SDK source** (`~/.unirtos/sdk/v<version>/`) for API signatures.
2. Note the divergence in your delivery and refresh the bundled docs.
