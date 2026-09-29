// UniRTOS MQTT uplink template (qcm_mqtt component).
// API sequence per official docs + SDK header qcm_mqtt.h:
//   default_config -> create -> init(cb) -> open(addr,port) -> connect
//   -> subscribe -> [wait_read_cnt / read message] -> publish -> disconnect -> close
//
// IMPORTANT — verify before building:
// 1. Field names of qcm_mqtt_config_t / qcm_mqtt_pub_config_t / qcm_mqtt_sub_config_t
//    against ~/.unirtos/sdk/v<version>/qos_components/components/qcm_mqtt/public/qcm_mqtt.h
// 2. Config struct notes (from SDK header, v1.0.x):
//    version: QCM_MQTT_VERSION_V3 (3.1) / QCM_MQTT_VERSION_V4 (3.1.1); MQTT5 needs CONFIG_QCM_MQTT5_FUNC
//    sim_id (default 0), pdp_cid (default QOSA_PDP_CID_MIN), kalive_time (default 120 s),
//    clean_session, will_flag/will_topic/will_message, ssl_enable/ssl_config under CONFIG_QCM_VTLS_FUNC
// 3. Max 6 concurrent clients (QCM_MQTT_MAX_CLIENT_CNT), max 5 topics per subscribe.
//
// Requires an active datacall first — pair with net_datacall_template.c.
// Full doc: assets/docs-md/网络与通信/网络协议/MQTT/MQTT.md

#include "qosa_def.h"
#include "qosa_sys.h"
#include "qosa_log.h"
#include "qcm_mqtt.h"

#define QOS_LOG_TAG   LOG_TAG_APP_MQTT

#define APP_MQTT_TASK_STACK_SIZE  (6 * 1024)  // TLS/QoS headroom over the 4 KB net baseline
#define APP_MQTT_TASK_PRIO        QOSA_PRIORITY_NORMAL

#define MQTT_BROKER_ADDR  "your.broker.host"  // TODO
#define MQTT_BROKER_PORT  1883                // 8883 for TLS
#define MQTT_PUB_TOPIC    "app/uplink"        // TODO

static qosa_task_t g_app_mqtt_task = QOSA_NULL;

// Event callback runs in component context: never block, never publish from here.
static void app_mqtt_event_cb(qcm_mqtt_client_event_e event_id, void *evt_param, void *user_param)
{
    QLOGW("mqtt event=%d", (int)event_id);
    // handle CONNOK/DISCONN/PUB/SUB events per qcm_mqtt_client_event_e enum
}

static void app_mqtt_task_process(void *arg)
{
    qcm_mqtt_config_t cfg = {0};

    // 1. Fill defaults, then override the fields you care about.
    qcm_mqtt_client_default_config(&cfg);
    // cfg.version = QCM_MQTT_VERSION_V4;
    // cfg.sim_id = 0;
    // cfg.kalive_time = 120;

    // 2. Create + init a client slot (returns an id < QCM_MQTT_MAX_CLIENT_CNT).
    qosa_uint8_t cli = qcm_mqtt_client_create();
    if (qcm_mqtt_client_init(cli, &cfg, app_mqtt_event_cb, QOSA_NULL) != QOSA_OK)
    {
        QLOGE("mqtt init failed");
        return;
    }

    // 3. Open transport to the broker, then connect (needs datacall up).
    if (qcm_mqtt_client_open(cli, MQTT_BROKER_ADDR, MQTT_BROKER_PORT) != QOSA_OK)
    {
        QLOGE("mqtt open failed");
        return;
    }
    // connect() takes the client-id/username/password params — check the exact
    // prototype in qcm_mqtt.h for your SDK version before building.
    // qcm_mqtt_client_connect(cli, "client-id", "user", "pass", ...);

    // 4. Subscribe (optional): fill qcm_mqtt_sub_config_t (topic + qos), then
    //    qcm_mqtt_client_subscribe(cli, &sub_info);

    // 5. Uplink loop.
    qcm_mqtt_pub_config_t pub = {0};
    // pub.topic = MQTT_PUB_TOPIC; pub.qos = ...; pub.payload/len = ...
    int cnt = 0;
    while (1)
    {
        // pub.payload = ...; publish via qcm_mqtt_client_publish(cli, &pub);
        QLOGV("mqtt uplink tick %d", cnt++);
        qosa_task_sleep_sec(30);
    }

    // 6. Teardown on exit paths: qcm_mqtt_client_disconnect(cli, &disc_info);
    //    then qcm_mqtt_client_close(cli);
}

void app_mqtt_init(void)
{
    QLOGV("enter app mqtt init");
    if (g_app_mqtt_task == QOSA_NULL)
    {
        int ret = qosa_task_create(&g_app_mqtt_task, APP_MQTT_TASK_STACK_SIZE,
                                   APP_MQTT_TASK_PRIO, "app_mqtt",
                                   app_mqtt_task_process, QOSA_NULL);
        if (ret != QOSA_OK)
        {
            QLOGE("app_mqtt task create failed ret=%d", ret);
        }
    }
}

UNIRTOS_APP_EXPORT(700, "app_mqtt_demo", app_mqtt_init);
