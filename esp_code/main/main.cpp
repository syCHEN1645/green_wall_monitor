#include <stdio.h>
#include <string>
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
#include "SEN0308Device.cpp"
#include "WiFiManager.hpp"
#include "MqttPublisher.hpp"
#include "config.h"

// use smart pointers as placeholder to prevent startup order issues
adc_oneshot_unit_handle_t adc_handle;

std::unique_ptr<WiFiManager> wifiManager;
std::unique_ptr<MqttPublisher> mqttPub;

std::vector<std::unique_ptr<SensorDevice>> sensors;

void initialiseHardware() {
    if (i2cdev_init() != ESP_OK) {
        ESP_LOGE("HardwareInit", "Error initializing I2C");
    }
    ESP_LOGI("HardwareInit", "Initialized I2C");

    // initialize ADC unit
    adc_oneshot_unit_init_cfg_t init_config = {
        .unit_id = ADC_UNIT_1,
        .clk_src = ADC_RTC_CLK_SRC_DEFAULT,
        .ulp_mode = ADC_ULP_MODE_DISABLE,
    };
    esp_err_t err = adc_oneshot_new_unit(&init_config, &adc_handle);
    if (err != ESP_OK) {
        ESP_LOGE("HardwareInit", "Failed to initialize ADC unit %d: %s", ADC_UNIT_1, esp_err_to_name(err));
    }
    ESP_LOGI("HardwareInit", "Initialized ADC");   
}

void initialiseSensor() {
    // Use make_unique to manage memory automatically
    auto sensor_1 = std::make_unique<SEN0385Device>("air_temp_1", CONFIG_SEN0385_I2C_ADDR);
    int args_1[] = {CONFIG_SEN0385_1_SDA_PIN, CONFIG_SEN0385_1_SCL_PIN, int(I2C_NUM_0)};
    if (sensor_1->setupSensor(args_1) == ESP_OK) {
        sensors.push_back(std::move(sensor_1));
    } else {
        ESP_LOGE("SensorInit", "Failed to initialize air_temp_1 sensor");
    }

    // auto sensor_2 = std::make_unique<DS18B20Device>("water_temp_1");
    // int args_2[] = {CONFIG_DS18B20_1_PIN};
    // if (sensor_2->setupSensor(args_2) == ESP_OK) {
    //     sensors.push_back(std::move(sensor_2));
    // } else {
    //     ESP_LOGE("SensorInit", "Failed to initialize water_temp_1 sensor");
    // }

    // auto sensor_3 = std::make_unique<DS18B20Device>("water_temp_2");
    // int args_3[] = {CONFIG_DS18B20_2_PIN};
    // if (sensor_3->setupSensor(args_3) == ESP_OK) {
    //     sensors.push_back(std::move(sensor_3));
    // } else {
    //     ESP_LOGE("SensorInit", "Failed to initialize water_temp_2 sensor");
    // }

    auto sensor_4 = std::make_unique<SEN0308Device>("soil_moisture_1", adc_handle);
    int args_4[] = {CONFIG_SEN0308_ADC_CHANNEL};
    // sensor_4->setupSensor(args_4);
    if (sensor_4->setupSensor(args_4) == ESP_OK) {
        // after running this, sensor_4 points to null, avoid using it after this
        sensors.push_back(std::move(sensor_4));
    } else {
        ESP_LOGE("SensorInit", "Failed to initialize soil_moisture_1 sensor");
    }

    auto sensor_5 = std::make_unique<SEN0385Device>("air_temp_2", CONFIG_SEN0385_I2C_ADDR);
    int args_5[] = {CONFIG_SEN0385_2_SDA_PIN, CONFIG_SEN0385_2_SCL_PIN, int(I2C_NUM_1)};
    if (sensor_5->setupSensor(args_5) == ESP_OK) {
        sensors.push_back(std::move(sensor_5));
    } else {
        ESP_LOGE("SensorInit", "Failed to initialize air_temp_2 sensor");
    }

}

void initialiseWiFi() {
    wifiManager = std::make_unique<WiFiManager>();
    wifiManager->setupWiFi();
    wifiManager->connect(WIFI_SSID, WIFI_PASSWORD);
    wifiManager->waitForConnection();
}

void initialiseMqtt() {
    // mqtt client
    mqttPub = std::make_unique<MqttPublisher>();
}

void sensor_task(void *pvParameters) {
    while (1) {
        for (auto& s : sensors) {
            std::vector<float> readings = s->getReadingOnce();
            for (size_t i = 0; i < readings.size(); i++) {
                printf("Reading %zu: %.2f\n" , i, readings[i]);
                mqttPub->publish("topic", (std::to_string(readings[i])).c_str(), 0, 0);
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

    initialiseHardware();

    // 2. Network / SNTP Initialization (Equivalent to your setup())
    // Note: You'll need a standard Wi-Fi helper here 
    initialiseWiFi();
    vTaskDelay(pdMS_TO_TICKS(1000)); // Wait a bit for Wi-Fi to stabilize
    initialiseMqtt();
    initialiseSensor();
    
    // 3. Set Timezone (Your UTC-8 logic)
    setenv("TZ", "CST-8", 1); // "CST-8" is often used for Singapore/China
    tzset();

    // 4. Start the main logic task
    xTaskCreate(sensor_task, "sensor_task", 4096, NULL, 5, NULL);
}
