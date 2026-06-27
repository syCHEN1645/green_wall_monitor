#include <Arduino.h>

#define DO_PIN 25

// reference volage (mv)
#define VREF 5000
//ADC Resolution
#define ADC_RES 1024

uint16_t adc_raw;
uint16_t adc_val;

void setup()
{
  Serial.begin(115200);
}

void loop()
{
  adc_raw = analogRead(DO_PIN);
  adc_val = uint32_t(VREF) * adc_raw / ADC_RES;
  Serial.print("ADC RAW:\t" + String(adc_raw) + "\t");
  Serial.print("ADC Voltage:\t" + String(adc_val) + "\t");

  delay(1000);
}
