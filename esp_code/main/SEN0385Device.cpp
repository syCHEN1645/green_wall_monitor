#include <stdio.h>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <esp_system.h>
#include <string.h>
#include <esp_err.h>

#include "config.h"
#include "SEN0385Device.hpp"

SEN0385Device::SEN0385Device(std::string name, uint8_t addr) : name(name), address(addr) {}

SEN0385Device::~SEN0385Device()
{
    // Clean up resources if needed
}

void SEN0385Device::setupSensor(int gpio_pins[])
{
    // Initialize the SHT3x sensor
    // GPIO pins: [SDA, SCL]
    ESP_ERROR_CHECK(i2cdev_init());
    memset(&this->dev, 0, sizeof(sht3x_t));

    ESP_ERROR_CHECK(sht3x_init_desc(&this->dev, this->address, I2C_NUM_0, (gpio_num_t)gpio_pins[0], (gpio_num_t)gpio_pins[1]));
    ESP_ERROR_CHECK(sht3x_init(&this->dev));
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
        printf("Error reading SEN0385 Sensor: %d\n", ret);
        readings[0] = -999.0f;
        readings[1] = -999.0f;
    }
    printf("SEN0385 Sensor: %.2f °C, %.2f %%\n", readings[0], readings[1]);
    return readings;
}

// void task(void *pvParameters)
// {
//     float temperature;
//     float humidity;

//     TickType_t last_wakeup = xTaskGetTickCount();

//     while (1)
//     {
//         // perform one measurement and do something with the results
//         ESP_ERROR_CHECK(sht3x_measure(&dev, &temperature, &humidity));
//         printf("SHT3x Sensor: %.2f °C, %.2f %%\n", temperature, humidity);

//         // wait until 5 seconds are over
//         vTaskDelayUntil(&last_wakeup, pdMS_TO_TICKS(5000));
//     }
// }