// UniRTOS cellular bootstrap template (DataCall).
// Mirrors the official 快速连接蜂窝网络 demo flow:
//   attach wait -> event register -> PDP config -> conn_new -> start -> IP info.
// API reference: assets/docs-md/网络与通信/网卡/蜂窝无线网卡/DataCall拨号/DataCall拨号.md
// Verify exact signatures against ~/.unirtos/sdk/v<version>/qos_components/system/modem/include/qosa_datacall.h

#include "qosa_def.h"
#include "qosa_sys.h"
#include "qosa_log.h"
#include "qosa_datacall.h"
#include "qosa_ip_addr.h"

#define QOS_LOG_TAG   LOG_TAG_APP_NET

#define APP_NET_TASK_STACK_SIZE  (4 * 1024)   // official datacall demo uses 4 KB
#define APP_NET_TASK_PRIO        QOSA_PRIORITY_NORMAL
#define APP_NET_ATTACH_TIMEOUT_S (300)        // official demo: 300 s attach wait

static qosa_task_t g_app_net_task = QOSA_NULL;

// Network event callbacks run in SDK context: do NOT block here.
// Hand events to a msgq and process them in the task loop for real apps.
static void app_net_pdp_change_cb(void *param)
{
    QLOGW("pdp status changed");
}

static void app_net_task_process(void *arg)
{
    qosa_uint8_t         simid = 0;
    qosa_bool_t          is_attached = QOSA_FALSE;
    qosa_pdp_context_t   pdp_ctx = {0};
    qosa_datacall_conn_t conn = QOSA_NULL;
    qosa_datacall_ip_info_t info = {0};

    // 1. Wait for network attach (register to PLMN).
    is_attached = qosa_datacall_wait_attached(simid, APP_NET_ATTACH_TIMEOUT_S);
    if (!is_attached)
    {
        QLOGE("attach wait timeout - check SIM/antenna/APN");
        return;
    }

    // 2. Register network state callbacks before dialing.
    qosa_event_notify_register(QOSA_EVENT_NW_PDN_DEACT, app_net_pdp_change_cb, QOSA_NULL);

    // 3. Configure PDP context: APN + IP type. Zero APN = carrier default.
    memset(&pdp_ctx, 0, sizeof(pdp_ctx));
    // pdp_ctx.apn = "cmnet";  // set explicitly only if the carrier requires it
    qosa_datacall_set_pdp_context(simid, &pdp_ctx);

    // 4. Create and start the datacall connection (blocking dial).
    if (qosa_datacall_conn_new(&conn, simid) != QOSA_OK)
    {
        QLOGE("conn_new failed");
        return;
    }
    if (qosa_datacall_start(conn) != QOSA_OK)
    {
        QLOGE("datacall start failed");
        return;
    }

    // 5. Read IP info.
    if (qosa_datacall_get_ip_info(conn, &info) == QOSA_OK)
    {
        char ip_str[46] = {0};
        qosa_ip_addr_inet_ntop(&info.ip_addr, ip_str, sizeof(ip_str));
        QLOGI("datacall up, ip=%s", ip_str);
    }

    // 6. Business loop goes here (MQTT/socket/cloud).
    while (1)
    {
        qosa_task_sleep_sec(10);
        // optional: qosa_datacall_get_status(conn) health check + redial logic
    }
}

void app_net_init(void)
{
    QLOGV("enter app net init");
    if (g_app_net_task == QOSA_NULL)
    {
        int ret = qosa_task_create(&g_app_net_task, APP_NET_TASK_STACK_SIZE,
                                   APP_NET_TASK_PRIO, "app_net",
                                   app_net_task_process, QOSA_NULL);
        if (ret != QOSA_OK)
        {
            QLOGE("app_net task create failed ret=%d", ret);
        }
    }
}

UNIRTOS_APP_EXPORT(700, "app_net_demo", app_net_init);
