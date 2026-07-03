// This code runs on an Arduino Uno R4 board
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>
#include <DFRobot_ORP_PRO.h>

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

uint16_t samples[SAMPLE_SIZE];
float ph_adc_val;
float do_adc_val;
float orp_adc_val;

WiFiUDP udp;
DFRobot_ORP_PRO orp(2480);

void setup()
{
  Serial.begin(9600);
  delay(1000);

  // wifi connection
  WiFi.begin(SSID, PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
      delay(1000);
      Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
  Serial.print("This device IP Address: ");
  Serial.println(WiFi.localIP());

  // delay(1000);
  // // set up ORP sensor calibration
  // // todo: change to actual shorted voltage
  // orp.setCalibration(orp.calibrate(2480));

  // // set up PH sensor
  // pinMode(PH_LED_PIN, OUTPUT);
  // ph_offset = 0.0;

  // Serial.print("calibration is: ");
  // Serial.print(orp.getCalibration());
  // Serial.println("mV");
}

String makeDataUdp(float reading, String measurement) {
  return "";
}

float aveArray(uint16_t* array, size_t size) {
  if (size <= 5) {
    Serial.println("Array size too small, must be greater than 5");
    return 0.0;
  }
  // filter out min and max and then get average
  uint16_t min, max, sum;
  if (array[0] > array[1]) {
    min = array[1];
    max = array[0];
  } else {
    max = array[1];
    min = array[0];
  }
  sum = array[0] + array[1];
  for (int i = 2; i < size; i++) {
    if (array[i] > max) {
      max = array[i];
    } else if (array[i] < min) {
      min = array[i];
    }
    sum += array[i];
  }
  float ave = float(sum - min - max) / (size - 2);
  return ave;
}

void getSamples(int pin) {
  unsigned long sampling_time = millis();
  int i = 0;
  while (i < SAMPLE_SIZE) {
    if (millis() - sampling_time > SAMPLE_INTERVAL) {
      samples[i] = analogRead(pin);
      i++;
      sampling_time = millis();
    }
  }
}

void loop() {
  String payload;
  // At fixed intervals, read from each sensor and send continuously
  // DO sensor reading
  getSamples(DO_PIN);
  do_adc_val = uint32_t(VREF) * aveArray(samples, SAMPLE_SIZE) / ADC_RES;
  Serial.print("PH Reading:\t" + String(do_adc_val) + "\t");
  // send data to pi for processing
  payload = makeDataUdp(do_adc_val, "DO");
  udp.beginPacket(SERVER_IP, UDP_PORT);
  udp.print(payload);
  udp.endPacket();
  delay(1000);

  // ORP sensor reading
  getSamples(ORP_PIN);
  orp_adc_val = uint32_t(VREF) * aveArray(samples, SAMPLE_SIZE) / ADC_RES;
  Serial.print("ORP Reading:\t" + String(ph_adc_val) + "\t");
  // send data to pi for processing
  payload = makeDataUdp(orp_adc_val, "ORP");
  udp.beginPacket(SERVER_IP, UDP_PORT);
  udp.print(payload);
  udp.endPacket();
  delay(1000);

  // PH sensor reading
  getSamples(PH_PIN);
  ph_adc_val = uint32_t(VREF) * aveArray(samples, SAMPLE_SIZE) / ADC_RES;
  Serial.print("PH Reading:\t" + String(ph_adc_val) + "\t");
  // send data to pi for processing
  payload = makeDataUdp(ph_adc_val, "PH");
  udp.beginPacket(SERVER_IP, UDP_PORT);
  udp.print(payload);
  udp.endPacket();

  delay(60000);
}

