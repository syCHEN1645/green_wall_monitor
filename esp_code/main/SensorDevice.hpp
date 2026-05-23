#ifndef SENSOR_DEVICE_HPP
#define SENSOR_DEVICE_HPP

#include <vector>
#include <esp_err.h>

class SensorDevice
{
public:
    std::string name;
    virtual esp_err_t setupSensor(int gpio_pins[]) = 0;
    virtual const std::vector<std::string>& getMeasurements() const = 0;
    virtual std::vector<float> getReadingOnce() = 0;
};

#endif