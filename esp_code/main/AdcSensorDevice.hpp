#pragma once

#include <string>
#include <vector>

#include <esp_adc/adc_oneshot.h>
#include <esp_err.h>

#include "SensorDevice.hpp"

class AdcSensorDevice : public SensorDevice
{
public:
	std::string name;

	AdcSensorDevice(std::string name, adc_oneshot_unit_handle_t adc_handle);

	esp_err_t setupSensor(int gpio_pins[]) override;
	virtual float parseAdcValue(int raw_value);
	std::vector<float> getReadingOnce() override;

private:
	adc_unit_t adc_unit;
	adc_channel_t adc_channel;
    adc_oneshot_unit_handle_t adc_handle;
};
