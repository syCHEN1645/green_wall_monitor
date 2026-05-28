#include "esp_log.h"
#include "esp_err.h"
#include "freertos/FreeRTOS.h"

#include "onewire_bus.h"
#include "ds18b20.h"

#include "DS18B20Device.hpp"

const char* DS18B20Device::TAG = "DS18B20_Sensor";

const std::vector<std::string> DS18B20Device::measurements = {
    SENSOR_MEASUREMENT_WALL_TEMP
};

DS18B20Device::DS18B20Device(std::string name)
{
    this->name = name;
    this->bus_handle = nullptr;
    this->sensor_handle = nullptr;
}

DS18B20Device::~DS18B20Device()
{
    if (sensor_handle) {
        ds18b20_del_device(sensor_handle);
        sensor_handle = nullptr;
    }
    if (bus_handle) {
        onewire_bus_del(bus_handle);
        bus_handle = nullptr;
    }
}

const std::vector<std::string>& DS18B20Device::getMeasurements() const
{
    return this->measurements;
}

// Assign the bus and sensor handles
esp_err_t DS18B20Device::setupSensor(int gpio_pin[])
{
    onewire_bus_config_t bus_config = {
        .bus_gpio_num = gpio_pin[0],
        .flags = {
            // enable the internal pull-up resistor in case the external device didn't have one
            .en_pull_up = true,
        }};
    onewire_bus_rmt_config_t rmt_config = {
        // 1byte ROM command + 8byte ROM number + 1byte device command
        .max_rx_bytes = 10,
    };
    if (onewire_new_bus_rmt(&bus_config, &rmt_config, &this->bus_handle) != ESP_OK) {
        ESP_LOGE(this->name.c_str(), "Failed to create 1-wire bus on GPIO %d", gpio_pin[0]);
        return ESP_FAIL;
    }

    // create 1-wire device iterator for device search
    onewire_device_iter_handle_t iter = NULL;
    if (onewire_new_device_iter(this->bus_handle, &iter) != ESP_OK) {
        ESP_LOGE(this->name.c_str(), "Failed to create 1-wire device iterator\n");
        onewire_bus_del(this->bus_handle);
        this->bus_handle = nullptr;
        return ESP_FAIL;
    }
    
    onewire_device_t next_device;
    esp_err_t search_result = ESP_OK;
    while ((search_result = onewire_device_iter_get_next(iter, &next_device)) == ESP_OK) { // found a new device, let's check if we can upgrade it to a DS18B20
        ds18b20_config_t ds_cfg = {};
        onewire_device_address_t address;
        // check if the device is a DS18B20, if so, assign the ds18b20 handle
        if (ds18b20_new_device_from_enumeration(&next_device, &ds_cfg, &this->sensor_handle) == ESP_OK) {
            ds18b20_get_device_address(this->sensor_handle, &address);
            ESP_LOGI(this->name.c_str(), "Found DS18B20 at address: %016llX", address);
            break;
        }
    }

    if (search_result != ESP_ERR_NOT_FOUND && search_result != ESP_OK) {
        ESP_LOGE(this->name.c_str(), "1-wire search failed: %s", esp_err_to_name(search_result));
    }

    if (onewire_del_device_iter(iter) != ESP_OK) {
        ESP_LOGE(this->name.c_str(), "Failed to delete 1-wire device iterator");
        onewire_bus_del(this->bus_handle);
        this->bus_handle = nullptr;
        return ESP_FAIL;
    }

    if (!this->sensor_handle) {
        ESP_LOGE(this->name.c_str(), "No DS18B20 found on GPIO %d", gpio_pin[0]);
        onewire_bus_del(this->bus_handle);
        this->bus_handle = nullptr;
        return ESP_FAIL;
    }

    return ESP_OK;
}

std::vector<float> DS18B20Device::getReadingOnce()
{
    std::vector<float> temperature(1, -127.0);
    if (!this->sensor_handle) {
        ESP_LOGE(this->name.c_str(), "Sensor not initialized");
        return temperature;
    }

    if (ds18b20_trigger_temperature_conversion(this->sensor_handle) != ESP_OK) {
        ESP_LOGE(this->name.c_str(), "Failed to trigger temperature conversion");
        return temperature;
    }

    // wait for conversion to complete, typically 750ms for 12 bit resolution
    vTaskDelay(pdMS_TO_TICKS(800));
    if (ds18b20_get_temperature(this->sensor_handle, &temperature[0]) != ESP_OK) {
        ESP_LOGE(this->name.c_str(), "Failed to read temperature");
        return temperature;
    }

    return temperature;
}
