#ifndef SEN0385DEVICE_HPP
#define SEN0385DEVICE_HPP

#include <string>
#include "sht3x.h"

#include "config.h"
#include "SensorDevice.hpp"

class SEN0385Device : public SensorDevice
{
public:
    SEN0385Device(std::string name, uint8_t addr = 0x44);
    ~SEN0385Device();
    esp_err_t setupSensor(int gpio_pins[], size_t measurement_indices[]) override;
    std::vector<float> getReadingOnce() override;
    const std::vector<std::string>& getMeasurements() const override;
private:
    static const std::vector<std::string> measurements;
    sht3x_t dev;
    uint8_t address;
    bool descriptor_initialized;
};
#endif