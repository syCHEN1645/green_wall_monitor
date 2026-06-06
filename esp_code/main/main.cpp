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
#include <time.h>
#include "esp_log.h"
#include "esp_err.h"
#include "esp_sleep.h"

#include "SensorDevice.hpp"
#include "DS18B20Device.hpp"
#include "SEN0385Device.hpp"
#include "SEN0308Device.cpp"
#include "WiFiManager.hpp"
#include "MqttPublisher.hpp"
#include "RtcMemManager.cpp"
#include "config.h"

// use smart pointers as placeholder to prevent startup order issues
adc_oneshot_unit_handle_t adc_handle;

std::unique_ptr<WiFiManager> wifiManager;
std::unique_ptr<MqttPublisher> mqttPub;
std::unique_ptr<RtcMemManager> rtcMemManager;

std::vector<std::unique_ptr<SensorDevice>> sensors;

// fixed size of 8 (MEASUREMENT COUNT) in data region
inline constexpr const char* measurement_names[MEASUREMENT_COUNT] = {
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

    // initialise rtc mem manager
    rtcMemManager = std::make_unique<RtcMemManager>();
}

void initialiseSensor() {
    // Use make_unique to manage memory automatically

    // sensor 1: SEN0385
    {
        auto sensor = std::make_unique<SEN0385Device>(SENSOR_NAME_1, CONFIG_SEN0385_I2C_ADDR);
        int gpio_pins[] = {CONFIG_SEN0385_1_SDA_PIN, CONFIG_SEN0385_1_SCL_PIN, int(I2C_NUM_0)};
        // refer to measurement_names array indices
        size_t measurement_indices[] = {0, 1};
        if (sensor->setupSensor(gpio_pins, measurement_indices) == ESP_OK) {
            sensors.push_back(std::move(sensor));
        } else {
            ESP_LOGE("SensorInit", "Failed to initialize %s sensor", SENSOR_NAME_1);
        }
    }

    // sensor 2: DS18B20
    {
        auto sensor = std::make_unique<DS18B20Device>(SENSOR_NAME_2);
        int gpio_pins[] = {CONFIG_DS18B20_1_PIN};
        // refer to measurement_names array indices
        size_t measurement_indices[] = {2};
        if (sensor->setupSensor(gpio_pins, measurement_indices) == ESP_OK) {
            sensors.push_back(std::move(sensor));
        } else {
            ESP_LOGE("SensorInit", "Failed to initialize %s sensor", SENSOR_NAME_2);
        }
    }

    // sensor 3: DS18B20
    {
        auto sensor = std::make_unique<DS18B20Device>(SENSOR_NAME_3);
        int gpio_pins[] = {CONFIG_DS18B20_2_PIN};
        // refer to measurement_names array indices
        size_t measurement_indices[] = {3};
        if (sensor->setupSensor(gpio_pins, measurement_indices) == ESP_OK) {
            sensors.push_back(std::move(sensor));
        } else {
            ESP_LOGE("SensorInit", "Failed to initialize %s sensor", SENSOR_NAME_3);
        }
    }

    // sensor 4: SEN0308
    {
        auto sensor = std::make_unique<SEN0308Device>(SENSOR_NAME_4, adc_handle);
        int gpio_pins[] = {CONFIG_SEN0308_ADC_CHANNEL};
        // refer to measurement_names array indices
        size_t measurement_indices[] = {4};
        if (sensor->setupSensor(gpio_pins, measurement_indices) == ESP_OK) {
            // after running this, sensor points to null, avoid using it after this
            sensors.push_back(std::move(sensor));
        } else {
            ESP_LOGE("SensorInit", "Failed to initialize %s sensor", SENSOR_NAME_4);
        }
    }

    // sensor 5: SEN0385
    {
        auto sensor = std::make_unique<SEN0385Device>(SENSOR_NAME_5, CONFIG_SEN0385_I2C_ADDR);
        int gpio_pins[] = {CONFIG_SEN0385_2_SDA_PIN, CONFIG_SEN0385_2_SCL_PIN, int(I2C_NUM_1)};
        // refer to measurement_names array indices
        size_t measurement_indices[] = {5, 6};
        if (sensor->setupSensor(gpio_pins, measurement_indices) == ESP_OK) {
            sensors.push_back(std::move(sensor));
        } else {
            ESP_LOGE("SensorInit", "Failed to initialize %s sensor", SENSOR_NAME_5);
        }
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

// RtcData getAllSensorDataOnce() {

// }

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
    // check wakeup cause, if first time boot up, set buffer size to 0
    if (esp_sleep_get_wakeup_causes() == ESP_SLEEP_WAKEUP_UNDEFINED) {
        ESP_LOGI("MainLog", "Cold boot detected. Resetting RTC memory tracking index...");
        rtcMemManager->resetRtcBuffer(); // Clear residual RAM garbage safely
    }
    initialiseSensor();

    // 3. Read sensors and keep result in RTC memory
    // Send old data in buffer if buffer is full, then save data
    ESP_LOGI("MainLog", "Processing sensor array data payload...");
    if (rtcMemManager->isBufferFull()) {
        // Send old data in buffer
        // Connect to network architecture
        initialiseWiFi();
        initialiseMqtt();
        // Set Timezone
        setenv("TZ", "CST-8", 1); 
        tzset();

        // Send data in RTC buffer one by one, then reset buffer
        // Each one struct is the max 8 data points read at around the same time
        for (size_t i = 0; i < rtcDataCount; i++) {
            RtcData& data = rtcDataBuffer[i];
            // convert seconds to nanoseconds to match influxdb line protocol format
            uint64_t timestamp = data.timestamp * 1000000000ULL;
            for (size_t j = 0; j < MEASUREMENT_COUNT; j++) {
                // skip all bad readings
                if (data.sensor_readings[j] != BAD_READING) {
                    char topic_name[64];
                    snprintf(topic_name, sizeof(topic_name), "greenwall/%s", measurement_names[j]);
                    char payload[128];
                    // format: measurement_name,<tag_key>=<tag_val> <value_key>=<value_val> timestamp
                    snprintf(
                        payload, sizeof(payload), 
                        "%s,sensor=%s value=%f %llu", 
                        "Box-1", 
                        measurement_names[j], 
                        data.sensor_readings[j],
                        timestamp
                    );
                    // mqttPub->publishLineProtocol(topic_name, payload, 0, 0);
                    ESP_LOGI("MainLog", "Published %s: %s", topic_name, payload);
                }
            }
        }

        // Give the network stack a brief window to flush TCP packets out into the air.
        // If sleep instantly, the radio shuts down mid-transmission.
        vTaskDelay(pdMS_TO_TICKS(1500));
        // Clean up connections elegantly
        mqttPub.reset();
        esp_wifi_stop();
        rtcMemManager->resetRtcBuffer();
    }

    RtcData data;
    time_t now;
    time(&now);
    data.timestamp = static_cast<uint64_t>(now);
    // initialize all readings to BAD_READING by default
    for (size_t i = 0; i < MEASUREMENT_COUNT; i++) {
        data.sensor_readings[i] = BAD_READING;
    }

    for (auto& s : sensors) {
        // each sensor may have multiple measurements
        std::vector<float> readings = s->getReadingOnce();
        for (size_t i = 0; i < readings.size(); i++) {
            // save data into RTC data struct
            std::string str = s->name.c_str() + std::string("/") + s->getMeasurements()[i].c_str();
            for (size_t k = 0; k < MEASUREMENT_COUNT; k++) {
                if (str == measurement_names[k]) {
                    data.sensor_readings[k] = readings[i];
                    ESP_LOGI("MainLog", "Saved %s: %f", str.c_str(), readings[i]);
                    break;
                }
                // did not match any measurement name
                if (k == MEASUREMENT_COUNT - 1) {
                    ESP_LOGW("MainLog", "Measurement name %s not found in buffer", str.c_str());
                }
            }
        }
    }
    // save data to RTC memory buffer
    if (!rtcMemManager->saveToRtc(data)) {
        ESP_LOGW("MainLog", "Fail to save to RTC buffer");
    }

    // 4. Go to Sleep
    ESP_LOGI("MainLog", "Entering Deep Sleep mode for %d seconds...", DATA_PUBLISH_INTERVAL_NORMAL_S);
    
    // Configure timer (Convert seconds to microseconds), ULL means unsigned long long to prevent overflow
    esp_sleep_enable_timer_wakeup(DATA_PUBLISH_INTERVAL_NORMAL_S * 1000000ULL);
    // Power down completely
    esp_deep_sleep_start();
    // The CPU shuts off right here. This line will never be reached!
}
