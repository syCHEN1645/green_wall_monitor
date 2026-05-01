#include <stdio.h>
#include <string.h>
#include <vector>
#include <memory>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_wifi.h"
#include "esp_event.h"
#include "nvs_flash.h"
#include "esp_sntp.h"
#include "esp_log.h"
#include "esp_err.h"

#include "SensorDevice.hpp"
#include "DS18B20Device.hpp"
#include "SEN0385Device.hpp"
#include "MqttPublisher.hpp"
#include "config.h"

MqttPublisher mqttPub;

std::vector<std::unique_ptr<SensorDevice>> sensors;

void initialiseSensor() {
    // Use make_unique to manage memory automatically
    auto sensor_1 = std::make_unique<SEN0385Device>("wall_green");
    int args_1[] = {CONFIG_SEN0385_SDA_PIN, CONFIG_SEN0385_SCL_PIN};
    if (sensor_1->setupSensor(args_1) == ESP_OK) {
        sensors.push_back(std::move(sensor_1));
    } else {
        ESP_LOGE("SensorInit", "Failed to initialize SEN0385 sensor");
    }

    auto sensor_2 = std::make_unique<DS18B20Device>("wall_control");
    int args_2[] = {CONFIG_DS18B20_PIN};
    if (sensor_2->setupSensor(args_2) == ESP_OK) {
        sensors.push_back(std::move(sensor_2));
    } else {
        ESP_LOGE("SensorInit", "Failed to initialize DS18B20 sensor");
    }
    
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
        for (auto& s : sensors) {
            std::vector<float> readings = s->getReadingOnce();
            for (size_t i = 0; i < readings.size(); i++) {
                printf("Reading %zu: %.2f\n", i, readings[i]);
                mqttPub.publish("topic", (std::to_string(readings[i])).c_str(), 0, 0);
            }
        }
        vTaskDelay(pdMS_TO_TICKS(DATA_PUBLISH_INTERVAL_FAST_S * 1000));
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