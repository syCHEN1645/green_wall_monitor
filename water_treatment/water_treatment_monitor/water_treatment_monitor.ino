#include <Arduino.h>
#include <DFRobot_ORP_PRO.h>

#define DO_PIN 25
#define ORP_PIN 26

// reference volage (mv)
#define VREF 5000
//ADC Resolution
#define ADC_RES 1024

uint16_t do_adc_raw;
uint16_t do_adc_val;

uint16_t orp_adc_raw;
uint16_t orp_adc_val;

DFRobot_ORP_PRO orp(2480);

void setup()
{
  Serial.begin(115200);
  // set up ORP sensor calibration
  // todo: change to actual shorted voltage
  orp.setCalibration(orp.calibrate(2480));

  Serial.print("calibration is: ");
  Serial.print(orp.getCalibration());
  Serial.println("mV");
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

  delay(1000);
}
