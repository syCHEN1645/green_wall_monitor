# green_wall_monitor
## Hardware
### ESP32
- Chip type: ESP32-D0WD-V3 (revision v3.1)
- Features: Wi-Fi, BT, Dual Core + LP Core

### DFROBOT SEN0385
- SHT31 temperature & humitidy sensor
- https://wiki.dfrobot.com/sen0385/

### DFROBOT SEN0308
- soil humidity sensor
- https://wiki.dfrobot.com/sen0308

### DS18B20
- metal probe temperature sensor

## Software/Firmware
Project is built with ESP-IDF v6.0.0 in VSCode.
### ESP-IDF components
- esp-idf-lib__esp_idf_lib_helpers
- esp-idf-lib__i2cdev
- esp-idf-lib__sht3x
- espressif__ds18b20
- espressif__mqtt
- espressif__onewire_bus

### MQTT broker
- HiveMQ free public MQTT broker

### Database
- InfluxDB OSS
- Telegraf

## Miscellaneous
- HiveMQ connection troubleshoot on ESP-IDF: https://community.hivemq.com/t/trying-to-connect-esp32-idf-example-to-hivehq/3055
