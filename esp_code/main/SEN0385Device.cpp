#include <stdio.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <esp_system.h>
#include <string.h>
#include <esp_err.h>
#include <esp_log.h>

#include "config.h"
#include "SEN0385Device.hpp"

SEN0385Device::SEN0385Device(std::string name, uint8_t addr) : name(name), address(addr) {}

SEN0385Device::~SEN0385Device()
{
    // Clean up resources if needed
}

esp_err_t SEN0385Device::setupSensor(int gpio_pins[])
{
    // Initialize the SHT3x sensor
    // GPIO pins: [SDA, SCL]

    memset(&this->dev, 0, sizeof(sht3x_t));

    if (sht3x_init_desc(&this->dev, this->address, I2C_NUM_0, (gpio_num_t)gpio_pins[0], (gpio_num_t)gpio_pins[1]) != ESP_OK) {
        ESP_LOGE(this->name.c_str(), "Error initializing SHT3x sensor descriptor\n");
        return ESP_FAIL;
    }
    if (sht3x_init(&this->dev) != ESP_OK) {
        ESP_LOGE(this->name.c_str(), "Error initializing SHT3x sensor\n");
        return ESP_FAIL;
    }
    return ESP_OK;
}

std::vector<float> SEN0385Device::getReadingOnce()
{
    std::vector<float> readings(2, 0.0f);
    // temperature
    readings[0] = 0.0f;
    // humidity
    readings[1] = 0.0f;

    esp_err_t ret = sht3x_measure(&this->dev, &readings[0], &readings[1]);
    if (ret != ESP_OK) {
        ESP_LOGE(this->name.c_str(), "Error reading SEN0385 Sensor: %d", ret);
        readings[0] = -999.0f;
        readings[1] = -999.0f;
    }
    ESP_LOGI(this->name.c_str(), "SEN0385 Sensor: %.2f °C, %.2f %%", readings[0], readings[1]);
    return readings;
}
