#include "AdcSensorDevice.hpp"
#include "config.h"

class SEN0308Device : public AdcSensorDevice
{
private:
    static const std::vector<std::string> measurements;
    // calibration parameters representing the expected raw ADC values for 0% and 100% soil moisture
    float dry_limit = 2700.0f;
    float wet_limit = 30.0f;

public:
    using AdcSensorDevice::AdcSensorDevice;

    const std::vector<std::string>& getMeasurements() const override {
        return this->measurements;
    }

    float parseAdcValue(int raw_value)
    {
        float res = 100 * (1.0f - (float(raw_value) - this->wet_limit) / (this->dry_limit - this->wet_limit));
        return res;
    }
};

const std::vector<std::string> SEN0308Device::measurements = {SENSOR_MEASUREMENT_SOIL_MOISTURE};
