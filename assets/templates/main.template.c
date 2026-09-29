// UniRTOS minimal app template — task + log + entry registration.
// Layout: put this file in <project>/main/src/main.c, headers in main/inc/.
// Build:   unirtos-cli env-setup && unirtos-cli build -m EG800ZCN_LA

#include "qosa_def.h"     // QOSA base types (qosa_uint8_t, QOSA_NULL, ...)
#include "qosa_sys.h"     // system API (tasks, msgq, sem, mutex, sleep)
#include "qosa_log.h"     // QLOGV/D/I/W/E

// Log tag: shows up in EPAT; keep it short and app-specific.
#define QOS_LOG_TAG   LOG_TAG_APP_MAIN

#include "unirtos_app_init_registry.h"  // UNIRTOS_APP_EXPORT

// Stack sizing: LED-class demo = 1 KB; add 1 KB if you printf-heavy logs or
// call network APIs. Network task example: 4 * 1024.
#define APP_MAIN_TASK_STACK_SIZE  1024
#define APP_MAIN_TASK_PRIO        QOSA_PRIORITY_NORMAL

static qosa_task_t g_app_main_task = QOSA_NULL;

static void app_main_task_process(void *ctx)
{
    int loop_cnt = 0;

    while (1)
    {
        QLOGV("app main loop count=%d", loop_cnt++);
        // TODO: replace with real business logic.
        qosa_task_sleep_ms(1000);
    }
}

// Init must not block: create task(s), then return.
void app_main_init(void)
{
    QLOGV("enter app main init");

    if (g_app_main_task == QOSA_NULL)
    {
        int ret = qosa_task_create(
            &g_app_main_task,
            APP_MAIN_TASK_STACK_SIZE,
            APP_MAIN_TASK_PRIO,
            "app_main",
            app_main_task_process,
            QOSA_NULL);
        if (ret != QOSA_OK)
        {
            QLOGE("app_main task create failed ret=%d", ret);
        }
    }
}

// order_value controls boot sequence (ascending, same value = unstable order).
// Built-in demos use 700 — pick distinct values for dependent apps.
UNIRTOS_APP_EXPORT(700, "app_main_demo", app_main_init);
