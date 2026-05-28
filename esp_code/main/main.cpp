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
#include "esp_sleep.h"

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

// fixed size of 8 (MEASUREMENT COUNT)
const std::vector<std::string> measurement_names = {
    SENSOR_NAME_1 "/" SENSOR_MEASUREMENT_AIR_TEMP,
    SENSOR_NAME_1 "/" SENSOR_MEASUREMENT_AIR_HUMIDITY,
    SENSOR_NAME_2 "/" SENSOR_MEASUREMENT_WALL_TEMP,
    SENSOR_NAME_3 "/" SENSOR_MEASUREMENT_WALL_TEMP,
    SENSOR_NAME_4 "/" SENSOR_MEASUREMENT_SOIL_MOISTURE,
    SENSOR_NAME_5 "/" SENSOR_MEASUREMENT_AIR_TEMP,
    SENSOR_NAME_5 "/" SENSOR_MEASUREMENT_AIR_HUMIDITY,
    PLACEHOLDER
};

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
    auto sensor_1 = std::make_unique<SEN0385Device>(SENSOR_NAME_1, CONFIG_SEN0385_I2C_ADDR);
    int args_1[] = {CONFIG_SEN0385_1_SDA_PIN, CONFIG_SEN0385_1_SCL_PIN, int(I2C_NUM_0)};
    if (sensor_1->setupSensor(args_1) == ESP_OK) {
        sensors.push_back(std::move(sensor_1));
    } else {
        ESP_LOGE("SensorInit", "Failed to initialize %s sensor", SENSOR_NAME_1);
    }

    auto sensor_2 = std::make_unique<DS18B20Device>(SENSOR_NAME_2);
    int args_2[] = {CONFIG_DS18B20_1_PIN};
    if (sensor_2->setupSensor(args_2) == ESP_OK) {
        sensors.push_back(std::move(sensor_2));
    } else {
        ESP_LOGE("SensorInit", "Failed to initialize %s sensor", SENSOR_NAME_2);
    }

    auto sensor_3 = std::make_unique<DS18B20Device>(SENSOR_NAME_3);
    int args_3[] = {CONFIG_DS18B20_2_PIN};
    if (sensor_3->setupSensor(args_3) == ESP_OK) {
        sensors.push_back(std::move(sensor_3));
    } else {
        ESP_LOGE("SensorInit", "Failed to initialize %s sensor", SENSOR_NAME_3);
    }

    auto sensor_4 = std::make_unique<SEN0308Device>(SENSOR_NAME_4, adc_handle);
    int args_4[] = {CONFIG_SEN0308_ADC_CHANNEL};
    // sensor_4->setupSensor(args_4);
    if (sensor_4->setupSensor(args_4) == ESP_OK) {
        // after running this, sensor_4 points to null, avoid using it after this
        sensors.push_back(std::move(sensor_4));
    } else {
        ESP_LOGE("SensorInit", "Failed to initialize %s sensor", SENSOR_NAME_4);
    }

    auto sensor_5 = std::make_unique<SEN0385Device>(SENSOR_NAME_5, CONFIG_SEN0385_I2C_ADDR);
    int args_5[] = {CONFIG_SEN0385_2_SDA_PIN, CONFIG_SEN0385_2_SCL_PIN, int(I2C_NUM_1)};
    if (sensor_5->setupSensor(args_5) == ESP_OK) {
        sensors.push_back(std::move(sensor_5));
    } else {
        ESP_LOGE("SensorInit", "Failed to initialize %s sensor", SENSOR_NAME_5);
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
                mqttPub->publishFloat(s->name.c_str(), s->getMeasurements()[i].c_str(), readings[i], 0, 0);
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

    // 2. Fire up essential hardware and sensors
    initialiseHardware();
    initialiseSensor();

    // 3. Connect to network architecture
    initialiseWiFi();
    initialiseMqtt();
    
    // 4. Set Timezone
    setenv("TZ", "CST-8", 1); 
    tzset();

    // 5. Read sensors and publish immediately
    ESP_LOGI("MainLog", "Processing sensor array data payload...");
    for (auto& s : sensors) {
        std::vector<float> readings = s->getReadingOnce();
        for (size_t i = 0; i < readings.size(); i++) {
            mqttPub->publishFloat(s->name.c_str(), s->getMeasurements()[i].c_str(), readings[i], 0, 0);
            ESP_LOGI("MainLog", "Published %s: %f", s->name.c_str(), readings[i]);
        }
    }

    // 6. Give the network stack a brief window to flush TCP packets out into the air.
    // If sleep instantly, the radio shuts down mid-transmission.
    vTaskDelay(pdMS_TO_TICKS(1500)); 

    // 7. Clean up connections elegantly
    mqttPub.reset();
    esp_wifi_stop(); 

    // 8. Go to Sleep
    ESP_LOGI("MainLog", "Entering Deep Sleep mode for %d seconds...", DATA_PUBLISH_INTERVAL_NORMAL_S);
    
    // Configure timer (Convert seconds to microseconds), ULL means unsigned long long to prevent overflow
    esp_sleep_enable_timer_wakeup(DATA_PUBLISH_INTERVAL_NORMAL_S * 1000000ULL);
    
    // Power down completely
    esp_deep_sleep_start();

    // The CPU shuts off right here. This line will never be reached!
}
