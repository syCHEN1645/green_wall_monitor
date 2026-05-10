#include "AdcSensorDevice.hpp"

class SEN0308Device : public AdcSensorDevice
{
private:
    // calibration parameters representing the expected raw ADC values for 0% and 100% soil moisture
    float dry_limit = 2700.0f;
    float wet_limit = 30.0f;

public:
    using AdcSensorDevice::AdcSensorDevice;

    float parseAdcValue(int raw_value)
    {
        float res = 1.0f - (float(raw_value) - this->wet_limit) / (this->dry_limit - this->wet_limit);
        return res;
    }
};
