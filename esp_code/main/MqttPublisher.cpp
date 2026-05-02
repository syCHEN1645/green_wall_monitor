#include "MqttPublisher.hpp"
#include "config.h"
#include "esp_log.h"

MqttPublisher::MqttPublisher() {
    esp_mqtt_client_config_t mqtt_cfg = {};
    mqtt_cfg.broker.address.uri = MQTT_BROKER_URL;
    mqtt_cfg.broker.verification.skip_cert_common_name_check = true;
    client = esp_mqtt_client_init(&mqtt_cfg);
    esp_mqtt_client_register_event(
        client, 
        static_cast<esp_mqtt_event_id_t>(ESP_EVENT_ANY_ID), 
        mqtt_event_handler, 
        NULL
    );
    esp_mqtt_client_start(client);
}

MqttPublisher::~MqttPublisher() {
    esp_mqtt_client_stop(client);
    esp_mqtt_client_destroy(client);
}

void MqttPublisher::mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data) {
    // Handle MQTT events here (connected, disconnected, published, etc.)
    // This is a static method, so it doesn't have access to instance members.
    // You can use handler_args to pass instance-specific data if needed.
    // esp_mqtt_event_handle_t *event = (esp_mqtt_event_handle_t *)event_data;

    switch ((esp_mqtt_event_id_t)event_id) {
        case MQTT_EVENT_CONNECTED:
            ESP_LOGI("MQTT", "Connected");
            break;
        case MQTT_EVENT_DISCONNECTED:
            ESP_LOGI("MQTT", "Disconnected");
            break;
        case MQTT_EVENT_PUBLISHED:
            ESP_LOGI("MQTT", "Published");
            break;
        default:
            ESP_LOGI("MQTT", "Event: %ld", event_id);
            break;
    }
}

void MqttPublisher::publish(const char* topic, const char* data, int qos, int retain) {
    esp_mqtt_client_publish(client, topic, data, 0, qos, retain);
}
