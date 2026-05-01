// mqtt broker configuration
#define MQTT_BROKER_URL "mqtt://your_broker_url"
#define MQTT_BROKER_PORT 1883
#define MQTT_USERNAME "your_username"
#define MQTT_PASSWORD "your_password"

// sensor task configuration
#define DATA_PUBLISH_INTERVAL_NORMAL_S 60
#define DATA_PUBLISH_INTERVAL_FAST_S 10
#define DATA_PUBLISH_INTERVAL_SLOW_S 300
#define DATA_PUBLISH_INTERVAL_PAUSE_S 0

// PIN and address configuration for sensors
#define CONFIG_SEN0385_I2C_ADDR 0x44
#define CONFIG_DS18B20_PIN 33
#define CONFIG_SEN0385_SDA_PIN 21
#define CONFIG_SEN0385_SCL_PIN 22
