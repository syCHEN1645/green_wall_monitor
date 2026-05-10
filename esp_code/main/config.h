// WiFi configuration
// #define WIFI_SSID "Singtel8900-E948"
// #define WIFI_PASSWORD "0002550088"
#define WIFI_SSID "csy"
#define WIFI_PASSWORD "55555555"
#define WIFI_MAX_RETRY 5

// mqtt broker configuration
#define MQTT_BROKER_URL "mqtts://8d63bda53c1747e293147012b1f1012f.s1.eu.hivemq.cloud:8883"
#define MQTT_BROKER_PORT 8883
#define MQTT_USERNAME "greenwall"
#define MQTT_PASSWORD "Greenwall123"

// sensor task configuration
#define DATA_PUBLISH_INTERVAL_NORMAL_S 60
#define DATA_PUBLISH_INTERVAL_FAST_S 10
#define DATA_PUBLISH_INTERVAL_SLOW_S 300
#define DATA_PUBLISH_INTERVAL_PAUSE_S 0

// PIN and address configuration for sensors
#define CONFIG_SEN0385_I2C_ADDR 0x44
#define CONFIG_SEN0385_1_SDA_PIN 21
#define CONFIG_SEN0385_1_SCL_PIN 22
#define CONFIG_SEN0385_2_SDA_PIN 12
#define CONFIG_SEN0385_2_SCL_PIN 13

#define CONFIG_DS18B20_1_PIN 32
#define CONFIG_DS18B20_2_PIN 33

#define CONFIG_SEN0308_ADC_CHANNEL 7
