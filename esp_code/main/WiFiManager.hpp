#pragma once

#include <string>
#include "esp_wifi.h"
#include "esp_event.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"

class WiFiManager {
public:
    WiFiManager();
    esp_err_t setupWiFi();
    esp_err_t connect(const std::string& ssid, const std::string& pass);
    bool isConnected();
    void waitForConnection();

private:
    static void event_handler(
        void* arg, 
        esp_event_base_t event_base, 
        int32_t event_id, 
        void* event_data
    );
    
    static EventGroupHandle_t s_wifi_event_group;
    static const int WIFI_CONNECTED_BIT = BIT0;
    static const int WIFI_FAIL_BIT = BIT1;
    static int s_retry_num;
};
