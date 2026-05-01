#ifndef SENSOR_DEVICE_HPP
#define SENSOR_DEVICE_HPP

#include <vector>

class SensorDevice
{
public:
    virtual ~SensorDevice() {}
    virtual void setupSensor(int gpio_pins[]) = 0;
    virtual std::vector<float> getReadingOnce() = 0;
};

#endif