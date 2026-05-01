#include "esp_log.h"
#include <string.h>

#include "WiFiManager.hpp"
#include "config.h"

// Static member definitions
EventGroupHandle_t WiFiManager::s_wifi_event_group;
int WiFiManager::s_retry_num = 0;
static const char *TAG = "WiFiManager";

WiFiManager::WiFiManager() {
    s_wifi_event_group = xEventGroupCreate();
}

esp_err_t WiFiManager::setupWiFi() {
    // 1. Initialize the underlying TCP/IP stack
    if (esp_netif_init() != ESP_OK) {
        ESP_LOGE(TAG, "Error initializing TCP/IP stack");
        return ESP_FAIL;
    }

    // 2. Create the default event loop (if not already created)
    if (esp_event_loop_create_default() != ESP_OK) {
        ESP_LOGE(TAG, "Error creating default event loop");
        return ESP_FAIL;
    }

    // 3. Create default Wi-Fi station
    if (esp_netif_create_default_wifi_sta() == NULL) {
        ESP_LOGE(TAG, "Error creating default Wi-Fi station");
        return ESP_FAIL;
    }

    // 4. Initialize Wi-Fi with default config
    wifi_init_config_t cfg = WIFI_INIT_CONFIG_DEFAULT();
    if (esp_wifi_init(&cfg) != ESP_OK) {
        ESP_LOGE(TAG, "Error initializing Wi-Fi");
        return ESP_FAIL;
    }

    // 5. Register the event handler
    if (esp_event_handler_instance_register(
        WIFI_EVENT,
        ESP_EVENT_ANY_ID,
        &WiFiManager::event_handler,
        NULL, NULL) != ESP_OK
    ) {
        ESP_LOGE(TAG, "Error registering Wi-Fi event handler");
        return ESP_FAIL;
    }
    if (esp_event_handler_instance_register(
        IP_EVENT,
        IP_EVENT_STA_GOT_IP,
        &WiFiManager::event_handler,
        NULL, NULL) != ESP_OK
    ) {
        ESP_LOGE(TAG, "Error registering IP event handler");
        return ESP_FAIL;
    }

    return ESP_OK;
}

esp_err_t WiFiManager::connect(const std::string& ssid, const std::string& pass) {
    wifi_config_t wifi_config = {};
    strncpy((char*)wifi_config.sta.ssid, ssid.c_str(), sizeof(wifi_config.sta.ssid));
    strncpy((char*)wifi_config.sta.password, pass.c_str(), sizeof(wifi_config.sta.password));
    
    // Set some modern security defaults
    wifi_config.sta.threshold.authmode = WIFI_AUTH_WPA2_PSK;

    if (esp_wifi_set_mode(WIFI_MODE_STA) != ESP_OK) {
        ESP_LOGE(TAG, "Error setting Wi-Fi mode");
        return ESP_FAIL;
    }
    if (esp_wifi_set_config(WIFI_IF_STA, &wifi_config) != ESP_OK) {
        ESP_LOGE(TAG, "Error setting Wi-Fi configuration");
        return ESP_FAIL;
    }
    if (esp_wifi_start() != ESP_OK) {
        ESP_LOGE(TAG, "Error starting Wi-Fi");
        return ESP_FAIL;
    }

    ESP_LOGI(TAG, "wifi_init_sta finished.");
    return ESP_OK;
}

void WiFiManager::event_handler(void* arg, esp_event_base_t event_base, int32_t event_id, void* event_data) {
    if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_START) {
        esp_wifi_connect();
    } else if (event_base == WIFI_EVENT && event_id == WIFI_EVENT_STA_DISCONNECTED) {
        if (s_retry_num < WIFI_MAX_RETRY) {
            esp_wifi_connect();
            s_retry_num++;
            ESP_LOGI(TAG, "retry to connect to the AP");
        } else {
            xEventGroupSetBits(s_wifi_event_group, WIFI_FAIL_BIT);
        }
    } else if (event_base == IP_EVENT && event_id == IP_EVENT_STA_GOT_IP) {
        ip_event_got_ip_t* event = (ip_event_got_ip_t*) event_data;
        ESP_LOGI(TAG, "got ip:" IPSTR, IP2STR(&event->ip_info.ip));
        s_retry_num = 0;
        xEventGroupSetBits(s_wifi_event_group, WIFI_CONNECTED_BIT);
    }
}

void WiFiManager::waitForConnection() {
    // Wait for the CONNECTED_BIT to be set by the event_handler, pause main task until then
    xEventGroupWaitBits(s_wifi_event_group, WIFI_CONNECTED_BIT, pdFALSE, pdTRUE, portMAX_DELAY);
    ESP_LOGI(TAG, "Wi-Fi Connected successfully!");
}