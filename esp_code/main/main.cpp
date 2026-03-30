#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "esp_sntp.h"

#include "Thermocouple.hpp"
#include "config.h"

void sensor_task(void *pvParameters) {
    Thermocouple solar("solar");
    Thermocouple compare("compare");
    
    solar.setupSensor(32);
    compare.setupSensor(33);

    while (1) {
        float t1 = solar.getTemperature();
        float t2 = compare.getTemperature();
        
        printf("Solar: %.2f, Compare: %.2f\n", t1, t2);

        vTaskDelay(pdMS_TO_TICKS(10000)); 
    }
}

extern "C" void app_main(void) {
    // 1. Initialize NVS (Required for Wi-Fi)
    esp_err_t ret = nvs_flash_init();
    if (ret == ESP_ERR_NVS_NO_FREE_PAGES || ret == ESP_ERR_NVS_NEW_VERSION_FOUND) {
        ESP_ERROR_CHECK(nvs_flash_erase());
        ret = nvs_flash_init();
    }
    ESP_ERROR_CHECK(ret);

    // 2. Network / SNTP Initialization (Equivalent to your setup())
    // Note: You'll need a standard Wi-Fi helper here 
    
    // 3. Set Timezone (Your UTC-8 logic)
    setenv("TZ", "CST-8", 1); // "CST-8" is often used for Singapore/China
    tzset();

    // 4. Start the main logic task
    xTaskCreate(sensor_task, "sensor_task", 4096, NULL, 5, NULL);
}