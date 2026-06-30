// This code runs on an ESP32 board
#include <Arduino.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <ArduinoJson.h>
#include <DFRobot_ORP_PRO.h>

#define DO_PIN 25
#define ORP_PIN 26
#define PH_PIN 27
#define PH_LED_PIN 13

// reference volage (3.3v or 3300mv for esp32)
#define VREF 3300
// adc resolution (esp32 is by default 10-bit 4096)
#define ADC_RES 4096

#define SSID "ssid"
#define PASSWORD "pswd"
#define SERVER_IP "1.2.3.4"
#define UDP_PORT 5005

#define PH_SAMPLE_SIZE 40
#define PH_SAMPLE_INTERVAL 25

uint16_t ph_samples[PH_SAMPLE_SIZE];
uint16_t ph_adc_raw;
float ph_adc_val;
float ph_offset;

uint16_t do_adc_raw;
uint16_t do_adc_val;

uint16_t orp_adc_raw;
float orp_adc_val;

WiFiUDP udp;
DFRobot_ORP_PRO orp(2480);

void setup()
{
  Serial.begin(9600);
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

  // set up PH sensor
  pinMode(PH_LED_PIN, OUTPUT);
  ph_offset = 0.0;

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

  // PH sensor reading
  unsigned long sampling_time = millis();
  int i = 0;
  while (i < PH_SAMPLE_SIZE) {
    if (millis() - sampling_time > PH_SAMPLE_INTERVAL) {
      ph_adc_raw = analogRead(PH_PIN);
      ph_samples[i] = ph_adc_raw;
      i++;
      sampling_time = millis();
    }
  }
  ph_adc_val = aveArray(ph_samples, PH_SAMPLE_SIZE) * VREF / ADC_RES;
  ph_adc_val = ph_adc_val * 3.5 / 1000 + offset;
  Serial.print("PH Reading:\t" + String(ph_adc_val) + "\t");

  // send data to pi for processing
  String payload = makeDataUdp(do_adc_val, "DO");
  udp.beginPacket(SERVER_IP, UDP_PORT);
  udp.print(payload);
  udp.endPacket();

  delay(60000);
}
