#include <string>
#include <freertos/FreeRTOS.h>
#include <freertos/task.h>
#include <esp_adc/adc_oneshot.h>
#include <esp_log.h>

#include "AdcSensorDevice.hpp"

AdcSensorDevice::AdcSensorDevice(std::string name, adc_oneshot_unit_handle_t adc_handle)
{
    this->name = name;
    this->adc_unit = ADC_UNIT_1;
    this->adc_handle = adc_handle;
}

esp_err_t AdcSensorDevice::setupSensor(int gpio_pins[]) {
    this->adc_channel = static_cast<adc_channel_t>(gpio_pins[0]);
    // ADC channel configuration
    adc_oneshot_chan_cfg_t channel_config = {
        .atten = ADC_ATTEN_DB_12,
        .bitwidth = ADC_BITWIDTH_12,
    };
    esp_err_t err = adc_oneshot_config_channel(this->adc_handle, this->adc_channel, &channel_config);
    if (err != ESP_OK) {
        ESP_LOGE(this->name.c_str(), "Failed to configure ADC channel %d: %s", this->adc_channel, esp_err_to_name(err));
        adc_oneshot_del_unit(this->adc_handle);
        return err;
    }

    return ESP_OK;
}

float AdcSensorDevice::parseAdcValue(int raw_value) {
    return 0.0f;
}

std::vector<float> AdcSensorDevice::getReadingOnce() {
    int adc_value = 0;
    if (adc_unit == ADC_UNIT_1) {
        esp_err_t err = adc_oneshot_read(this->adc_handle, this->adc_channel, &adc_value);
        if (err != ESP_OK) {
            ESP_LOGE(this->name.c_str(), "Failed to read from ADC channel %d: %s", this->adc_channel, esp_err_to_name(err));
            return {-999.0f};
        }
        ESP_LOGI(this->name.c_str(), "Raw ADC value: %d", adc_value);
    } else if (adc_unit == ADC_UNIT_2) {
        // Note: ADC2 is shared with Wi-Fi, so it may not be available when Wi-Fi is active
        ESP_LOGE(this->name.c_str(), "Avoid using ADC_UNIT_2");
        return {-999.0f};
    } else {
        ESP_LOGE(this->name.c_str(), "Invalid ADC unit: %d", this->adc_unit);
        return {-999.0f};
    }

    // Convert raw value to voltage (assuming 3.3V reference and 12-bit resolution)
    float val = parseAdcValue(adc_value);
    ESP_LOGI(this->name.c_str(), "Parsed ADC value: %.2f", val);
    return {val};
}