#ifndef DS18B20DEVICE_HPP
#define DS18B20DEVICE_HPP

#include <string>
#include "ds18b20.h"
#include "onewire_bus.h"
#include "SensorDevice.hpp"
#include "config.h"

class DS18B20Device : public SensorDevice
{
public:
    static const char* TAG;
    
    DS18B20Device(std::string name);
    ~DS18B20Device();
    esp_err_t setupSensor(int gpio_pins[], size_t measurement_indices[]) override;
    std::vector<float> getReadingOnce() override;
    const std::vector<std::string>& getMeasurements() const override;
    
private:
    static const std::vector<std::string> measurements;
    onewire_bus_handle_t bus_handle;
    ds18b20_device_handle_t sensor_handle;
};

#endif