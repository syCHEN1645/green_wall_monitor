#include <stdio.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <esp_system.h>
#include <string.h>
#include <esp_err.h>
#include <esp_log.h>
#include <i2cdev.h>

#include "config.h"
#include "SEN0385Device.hpp"

const std::vector<std::string> SEN0385Device::measurements = {
    SENSOR_MEASUREMENT_AIR_TEMP, 
    SENSOR_MEASUREMENT_AIR_HUMIDITY
};

SEN0385Device::SEN0385Device(std::string name, uint8_t addr)
{
    this->name = name;
    this->address = addr;
    this->descriptor_initialized = false;
}

SEN0385Device::~SEN0385Device()
{
    if (this->descriptor_initialized) {
        sht3x_free_desc(&this->dev);
        this->descriptor_initialized = false;
    }
}

esp_err_t SEN0385Device::setupSensor(int gpio_pins[])
{
    // Initialize the SHT3x sensor
    // GPIO pins: 0 SDA, 1 SCK, 2 port
    memset(&this->dev, 0, sizeof(sht3x_t));

    if (sht3x_init_desc(&this->dev, this->address, (i2c_port_t)gpio_pins[2], (gpio_num_t)gpio_pins[0], (gpio_num_t)gpio_pins[1]) != ESP_OK) {
        ESP_LOGE(this->name.c_str(), "Error initializing SHT3x sensor descriptor");
        return ESP_FAIL;
    }
    this->descriptor_initialized = true;

    // 100 kHz is more tolerant for longer wires/noisy setups than 1 MHz default in this driver.
    this->dev.i2c_dev.cfg.master.clk_speed = 100000;
    this->dev.i2c_dev.cfg.sda_pullup_en = GPIO_PULLUP_ENABLE;
    this->dev.i2c_dev.cfg.scl_pullup_en = GPIO_PULLUP_ENABLE;

    if (sht3x_init(&this->dev) != ESP_OK) {
        ESP_LOGE(this->name.c_str(), "Error initializing SHT3x sensor\n");
        sht3x_free_desc(&this->dev);
        this->descriptor_initialized = false;
        return ESP_FAIL;
    }
    return ESP_OK;
}

const std::vector<std::string>& SEN0385Device::getMeasurements() const
{
    return this->measurements;
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
