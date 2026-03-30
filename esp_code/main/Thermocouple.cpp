#include "esp_log.h"
#include "esp_err.h"

#include "onewire_bus.h"
#include "ds18b20.h"

#include "Thermocouple.hpp"

static const char* TAG = "Thermocouple";

Thermocouple::Thermocouple(std::string name) : name(name)
{
    // Constructor can be used to initialize member variables if needed
    this->bus_handle = nullptr;
    this->sensor_handle = nullptr;
}

Thermocouple::~Thermocouple()
{
    // Clean up resources if needed
    if (sensor_handle)
    {
        ds18b20_del_device(sensor_handle);
    }
    if (bus_handle)
    {
        onewire_del_bus(bus_handle);
    }
}

// Assign the bus and sensor handles
void Thermocouple::setupSensor(int gpio_pin)
{
    onewire_bus_config_t bus_config = {
        .bus_gpio_num = gpio_pin,
        .flags = {
            // enable the internal pull-up resistor in case the external device didn't have one
            .en_pull_up = true,
        }};
    onewire_bus_rmt_config_t rmt_config = {
        // 1byte ROM command + 8byte ROM number + 1byte device command
        .max_rx_bytes = 10,
    };
    ESP_ERROR_CHECK(onewire_new_bus_rmt(&bus_config, &rmt_config, &this->bus_handle));

    // create 1-wire device iterator for device search
    onewire_device_iter_handle_t iter = NULL;
    ESP_ERROR_CHECK(onewire_new_device_iter(this->bus_handle, &iter));
    
    onewire_device_t next_device;
    while (onewire_device_iter_get_next(iter, &next_device) == ESP_OK)
    { // found a new device, let's check if we can upgrade it to a DS18B20
        ds18b20_config_t ds_cfg = {};
        onewire_device_address_t address;
        // check if the device is a DS18B20, if so, assign the ds18b20 handle
        if (ds18b20_new_device_from_enumeration(&next_device, &ds_cfg, &this->sensor_handle) == ESP_OK)
        {
            ds18b20_get_device_address(this->sensor_handle, &address);
            break;
        }
    }

    ESP_ERROR_CHECK(onewire_del_device_iter(iter));
}

float Thermocouple::getTemperature()
{
    return 0.0;
}
