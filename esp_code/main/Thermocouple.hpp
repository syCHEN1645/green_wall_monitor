#ifndef THERMOCOUPLE_HPP
#define THERMOCOUPLE_HPP

#include <string>
#include "ds18b20.h"
#include "onewire_bus.h"

class Thermocouple {
public:
    std::string name;
    Thermocouple(std::string name);
    ~Thermocouple();
    void setupSensor(int gpio_pin);
    float getTemperature();

private:
    onewire_bus_handle_t bus_handle;
    ds18b20_device_handle_t sensor_handle;
};

#endif