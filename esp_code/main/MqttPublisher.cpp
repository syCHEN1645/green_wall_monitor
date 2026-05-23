#include "MqttPublisher.hpp"
#include "config.h"
#include "esp_log.h"
#include "esp_crt_bundle.h"
#include <cstring>
#include <string>

namespace {
const char *TAG = "MQTT";

bool is_mqtts_uri(const char *uri)
{
    return uri && std::strncmp(uri, "mqtts://", 8) == 0;
}
}

MqttPublisher::MqttPublisher() {
    esp_mqtt_client_config_t mqtt_cfg = {};
    mqtt_cfg.broker.address.uri = MQTT_BROKER_URL;
    mqtt_cfg.credentials.username = MQTT_USERNAME;
    mqtt_cfg.credentials.authentication.password = MQTT_PASSWORD;

    // For mqtts:// endpoints, use ESP-IDF root certificate bundle for server verification.
    if (is_mqtts_uri(MQTT_BROKER_URL)) {
        mqtt_cfg.broker.verification.crt_bundle_attach = esp_crt_bundle_attach;
    }

    connected = false;
    client = esp_mqtt_client_init(&mqtt_cfg);
    if (!client) {
        ESP_LOGE(TAG, "Failed to initialize MQTT client");
        return;
    }

    esp_mqtt_client_register_event(
        client, 
        static_cast<esp_mqtt_event_id_t>(ESP_EVENT_ANY_ID), 
        mqtt_event_handler, 
        this
    );
    esp_mqtt_client_start(client);
    ESP_LOGI(TAG, "Waiting for secure broker handshake...");
    while (!connected) {
        vTaskDelay(pdMS_TO_TICKS(50)); 
    }
    ESP_LOGI(TAG, "Broker link established successfully inside constructor.");
}

MqttPublisher::~MqttPublisher() {
    connected = false;
    if (client) {
        esp_mqtt_client_stop(client);
        esp_mqtt_client_destroy(client);
        client = nullptr;
    }
}

void MqttPublisher::mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data) {
    (void)base;
    MqttPublisher *self = static_cast<MqttPublisher *>(handler_args);
    auto *event = static_cast<esp_mqtt_event_handle_t>(event_data);

    switch ((esp_mqtt_event_id_t)event_id) {
        case MQTT_EVENT_BEFORE_CONNECT:
            ESP_LOGI(TAG, "Connecting...");
            break;
        case MQTT_EVENT_CONNECTED:
            if (self) {
                self->connected = true;
            }
            ESP_LOGI(TAG, "Connected");
            break;
        case MQTT_EVENT_DISCONNECTED:
            if (self) {
                self->connected = false;
            }
            ESP_LOGI(TAG, "Disconnected");
            break;
        case MQTT_EVENT_PUBLISHED:
            ESP_LOGI(TAG, "Published");
            break;
        case MQTT_EVENT_ERROR:
            if (event && event->error_handle) {
                ESP_LOGE(TAG, "MQTT error type=%d, esp_tls_last_esp_err=0x%x, esp_tls_stack_err=0x%x", 
                         event->error_handle->error_type,
                         event->error_handle->esp_tls_last_esp_err,
                         event->error_handle->esp_tls_stack_err);
            } else {
                ESP_LOGE(TAG, "MQTT error");
            }
            break;
        default:
            ESP_LOGI(TAG, "Event: %ld", event_id);
            break;
    }
}

void MqttPublisher::publishJson(const char* topic, const char* data, int qos, int retain) {
    if (!client) {
        ESP_LOGE(TAG, "MQTT client is not initialized");
        return;
    }
    if (!connected) {
        ESP_LOGW(TAG, "Skip publish while MQTT disconnected");
        return;
    }

    int msg_id = esp_mqtt_client_publish(client, topic, data, 0, qos, retain);
    if (msg_id < 0) {
        ESP_LOGE(TAG, "Publish failed");
    }
}

void MqttPublisher::publishFloat(const char* sensor, const char* measurement, float value, int qos, int retain) {
    if (!client) {
        ESP_LOGE(TAG, "MQTT client is not initialized");
        return;
    }
    if (!connected) {
        ESP_LOGW(TAG, "Skip publish while MQTT disconnected");
        return;
    }
    
    char topic[128];
    snprintf(topic, sizeof(topic), "greenwall/%s/%s", sensor, measurement);

    char value_str[32];
    snprintf(value_str, sizeof(value_str), "%.2f", value);

    int msg_id = esp_mqtt_client_publish(client, topic, value_str, 0, qos, retain);
    if (msg_id < 0) {
        ESP_LOGE(TAG, "Publish failed");
    }
}
