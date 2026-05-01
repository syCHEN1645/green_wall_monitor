#include <stdio.h>
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "esp_sntp.h"

#include "DS18B20Device.hpp"
#include "MqttPublisher.hpp"
#include "config.h"

// in future change to other data structure for easier add and remove sensors
List<DS18B20Device> sensors;
MqttPublisher mqttPub;

void initialiseSensor()
{
    // group green wall
    DS18B20Device wallGreen("wall_green");
    wallGreen.setupSensor(32);
    sensors.push_back(wallGreen);

    // group control wall
    DS18B20Device wallControl("wall_control");
    sensors.push_back(wallControl);
    wallControl.setupSensor(33);
}

void initialiseWiFi() {
    return;
}

void initialiseMqtt() {
    // mqtt client
    mqttPub = MqttPublisher();
}

void sensor_task(void *pvParameters) {
    while (1) {
        float t1 = sensors[0].getTemperature();
        float t2 = sensors[1].getTemperature();
        
        // publish to mqtt here, decide topic and payload format later
        printf("Green Wall: %.2f, Control Wall: %.2f\n", t1, t2);
        mqttPub.publish("green_wall/temperature", (std::to_string(t1) + "," + std::to_string(t2)).c_str(), 0, 0);

        vTaskDelay(pdMS_TO_TICKS(DATA_PUBLISH_INTERVAL_NORMAL_S * 1000)); 
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
    initialiseWiFi();
    initialiseMqtt();
    initialiseSensor();
    
    // 3. Set Timezone (Your UTC-8 logic)
    setenv("TZ", "CST-8", 1); // "CST-8" is often used for Singapore/China
    tzset();

    // 4. Start the main logic task
    xTaskCreate(sensor_task, "sensor_task", 4096, NULL, 5, NULL);
}