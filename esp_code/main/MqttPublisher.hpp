#pragma once
#include "mqtt_client.h"

class MqttPublisher {
public:
    MqttPublisher();
    ~MqttPublisher();

    void publishJson(const char* topic, const char* data, int qos, int retain);
    void publishFloat(const char* sensor, const char* measurement, float value, int qos, int retain);
    void publishLineProtocol(const char* topic, const char* payload, int qos, int retain);
    void subscribe(const char* topic, int qos);
    void unsubscribe(const char* topic);
    void disconnect();

private:
    esp_mqtt_client_handle_t client;
    bool connected;
    static void mqtt_event_handler(void *handler_args, esp_event_base_t base, int32_t event_id, void *event_data);
};