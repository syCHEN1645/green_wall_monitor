#ifndef CONFIG_H
#define CONFIG_H

#define DO_PIN 25
#define ORP_PIN 26
#define PH_PIN 27
#define PH_LED_PIN 13

// reference volage (5V for Uno)
#define VREF 5000
// adc resolution (Uno is by default 10-bit 1024)
#define ADC_RES 1024

#define SSID "ssid"
#define PASSWORD "pswd"
#define SERVER_IP "1.2.3.4"
#define UDP_PORT 5005

#define SAMPLE_SIZE 40
#define SAMPLE_INTERVAL 25

#endif // CONFIG_H