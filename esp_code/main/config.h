// mqtt broker configuration
const char* MQTT_BROKER_URL = "mqtt://your_broker_url";
const int MQTT_BROKER_PORT = 1883;
const char* MQTT_USERNAME = "your_username";
const char* MQTT_PASSWORD = "your_password";

// sensor task configuration
const int DATA_PUBLISH_INTERVAL_NORMAL_S = 60;
const int DATA_PUBLISH_INTERVAL_FAST_S = 10;
const int DATA_PUBLISH_INTERVAL_SLOW_S = 300;
const int DATA_PUBLISH_INTERVAL_PAUSE_S = 0;
