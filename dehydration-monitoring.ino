#include <DHT.h>

// ----- Pin Definitions -----
#define DHTPIN 2          // DHT11 connected to digital pin 2
#define DHTTYPE DHT11
const int lm35Pin = A0;   // LM35 output to A0
const int gsrPin = A1;    // GSR signal (TP4) to A1

// ----- Initialize DHT sensor -----
DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(9600);
  dht.begin();
  delay(1000);
  Serial.println("🔍 Starting Hydration Monitoring System...");
}

void loop() {
  // ----- Read LM35 (Body Temp) -----
  int lm35Value = analogRead(lm35Pin);
  float voltage = lm35Value * (5.0 / 1023.0);
  float bodyTempC = voltage * 100.0; // 10mV per °C

  // ----- Read DHT11 -----
  float humidity = dht.readHumidity();
  float envTempC = dht.readTemperature();

  // ----- Read GSR -----
  int gsrValue = analogRead(gsrPin);

  // ----- Display Values -----
  Serial.print("Body Temp = ");
  Serial.print(bodyTempC, 2); // 2 decimal places
  Serial.println(" C");

  Serial.print("GSR = ");
  Serial.println(gsrValue);

  Serial.print("Env Temp = ");
  Serial.print(envTempC, 2);
  Serial.println(" C");

  Serial.print("Humidity = ");
  Serial.print(humidity, 2);
  Serial.println("%");

  delay(2000);  // Wait 2 seconds before next reading
}