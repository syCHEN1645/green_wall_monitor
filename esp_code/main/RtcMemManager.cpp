#include <stdio.h>
#include <string>
#include "esp_sleep.h"
#include "esp_log.h"

#include "config.h"

struct RtcData {
    // 8 float readings + 1 uint64_t timestamp for influxdb
    float sensor_readings[MEASUREMENT_COUNT];
    uint64_t timestamp;
};

RTC_DATA_ATTR RtcData rtcDataBuffer[RTC_BUFFER_NUM];
RTC_DATA_ATTR size_t rtcDataCount = 0;

class RtcMemManager {
// Send data in app_main
public:
    RtcMemManager() {}

    bool saveToRtc(RtcData& data) {
        // if buffer not full, save data to RTC memory
        if (rtcDataCount < RTC_BUFFER_NUM) {
            rtcDataBuffer[rtcDataCount] = data;
            rtcDataCount++;
            ESP_LOGI("RTC", "RTC buffer usage: %d out of %d, data saved", rtcDataCount, RTC_BUFFER_NUM);
            return true;
        } else {
            ESP_LOGI("RTC", "RTC buffer full %d, send out all existing data", rtcDataCount);
            return false;
        }
    }

    bool saveToRtc(float readings[MEASUREMENT_COUNT], uint64_t timestamp) {
        // if buffer not full, save data to RTC memory
        if (rtcDataCount < RTC_BUFFER_NUM) {
            rtcDataBuffer[rtcDataCount].timestamp = timestamp;
            for (size_t i = 0; i < MEASUREMENT_COUNT; i++) {
                rtcDataBuffer[rtcDataCount].sensor_readings[i] = readings[i];
            }
            rtcDataCount++;
            ESP_LOGI("RTC", "RTC buffer usage: %d out of %d, data saved", rtcDataCount, RTC_BUFFER_NUM);
            return true;
        } else {
            ESP_LOGI("RTC", "RTC buffer full %d, send out all existing data", rtcDataCount);
            return false;
        }
    }

    void resetRtcBuffer() const {
        rtcDataCount = 0;
    }

    bool isBufferFull() const {
        return rtcDataCount >= RTC_BUFFER_NUM;
    }

    const RtcData* getRtcDataBuffer() const {
        return rtcDataBuffer;
    }

    size_t getRtcDataCount() const {
        return rtcDataCount;
    }
};