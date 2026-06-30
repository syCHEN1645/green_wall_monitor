// This code runs on an ESP32 board
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>
#include <DFRobot_ORP_PRO.h>

#define DO_PIN 25
#define ORP_PIN 26

// reference volage (3.3v or 3300mv for esp32)
#define VREF 3300
// adc resolution (esp32 is by default 10-bit 4096)
#define ADC_RES 4096

#define SSID "ssid"
#define PASSWORD "pswd"
#define SERVER_IP "1.2.3.4"
#define UDP_PORT 5005

uint16_t do_adc_raw;
uint16_t do_adc_val;

uint16_t orp_adc_raw;
uint16_t orp_adc_val;

WiFiUDP udp;
DFRobot_ORP_PRO orp(2480);

void setup()
{
  Serial.begin(115200);
  delay(1000);

  WiFi.begin(SSID, PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
      delay(1000);
      Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
  Serial.print("ESP32 IP Address: ");
  Serial.println(WiFi.localIP());

  delay(1000);
  // set up ORP sensor calibration
  // todo: change to actual shorted voltage
  orp.setCalibration(orp.calibrate(2480));

  Serial.print("calibration is: ");
  Serial.print(orp.getCalibration());
  Serial.println("mV");
}

String makeHandShakeUdp(int num_points, int interval_min) {
  return "";
}

String makeDataUdp(float reading, String measurement) {
  return "";
}

void loop()
{
  // DO sensor reading
  do_adc_raw = analogRead(DO_PIN);
  do_adc_val = uint32_t(VREF) * do_adc_raw / ADC_RES;
  Serial.print("DO ADC RAW:\t" + String(do_adc_raw) + "\t");
  Serial.print("DO ADC Voltage:\t" + String(do_adc_val) + "\t");

  // ORP sensor reading
  orp_adc_raw = analogRead(ORP_PIN);
  orp_adc_val = uint32_t(VREF) * orp_adc_raw / ADC_RES;
  float orp_reading = orp.getORP(orp_adc_val);
  Serial.print("ORP RAW:\t" + String(orp_adc_raw) + "\t");
  Serial.print("ORP Voltage:\t" + String(orp_adc_val) + "\t");
  Serial.print("ORP Reading:\t" + String(orp_reading) + "\t");

  // send data to pi for processing
  String payload = makeDataUdp(do_adc_val, "DO");
  udp.beginPacket(SERVER_IP, UDP_PORT);
  udp.print(payload);
  udp.endPacket();

  delay(1000);
}
