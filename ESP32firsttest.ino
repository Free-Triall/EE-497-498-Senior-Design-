// Libraries needed
#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h" //Calling device DHT.h

// Salinity Sensor Stuff added 3/20/2026 might delete
//#include <Wire.h>
//#include <LiquidCrystal_I2C.h>
//#include <OneWire.h>
//#include <DallasTemperature.h>

#define DHTPIN 4 
// previously DHT11 but its a different model       
#define DHTTYPE DHT22 
#define PUMP_PIN 18 // added 2/20/2026  


// TDS Sensor Stuff added 11/15/2025
const int TDS_PIN = 34;

// Salinity Sensor Stuff added 3/20/2026
//const int salinityAnalogPin = 35;
//const int salinityDrivePin1 = 25;
//const int salinityDrivePin2 = 26;
//#define ONE_WIRE_BUS 14
//OneWire oneWire(ONE_WIRE_BUS);
//DallasTemperature sensors(&oneWire);

//Wifi Login
const char* ssid = "w";
const char* password = "w";

//My FLASK server
const char* serverURL = "w"; // Flask IP address

DHT dht(DHTPIN, DHTTYPE);

// TDS Sensor Stuff added 11/15/2025
// average ADC readings and convert to volts
float readAveragedVoltage(int pin, int samples = 20) {
  uint32_t sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delay(5);
  }
  float avg = sum / (float)samples;
  // 12-bit ADC, 0–4095 counts, ~3.3 V full scale
  return (avg / 4095.0f) * 3.3f;
}

// convert volts TDS ppm; calibrate later
float voltsToTDSppm(float v, float waterTempC = 25.0f) {
  // keep voltage in a sane range
  if (v < 0.0f) v = 0.0f;
  if (v > 3.0f) v = 3.0f;

  // temperature compensation (about 2% per °C from 25 °C)
  float tempCoef = 1.0f + 0.02f * (waterTempC - 25.0f);
  float vComp = v / tempCoef;
  
  // polynomial from TDS module docs, already in ppm after *0.5
  float tds = (133.42f * vComp * vComp * vComp
             - 255.86f * vComp * vComp
             + 857.39f * vComp) * 0.5f;

  return tds; // ppm
}

// TDS Sensor Stuff added 11/15/2025

// LCD Salinity Sensor Stuff added 3/24/2026
//LiquidCrystal_I2C lcd(0x27, 16, 2);

// Salinity Sensor Stuff added 3/20/2026
//float measureSalinityResistance(int samples = 5000) { 
  //const int dtime = 500;
  //const float Vin = 3.3;
  //const float R1 = 1000.0;

  //float tot = 0;
  //int validSamples = 0;

// Salinity Sensor Stuff added 3/20/2026
  //for (int i = 0; i < samples; i++) {
  //  digitalWrite(salinityDrivePin1, HIGH);
  //  digitalWrite(salinityDrivePin2, LOW);
  //  delayMicroseconds(dtime);

  //  digitalWrite(salinityDrivePin1, LOW);
  //  digitalWrite(salinityDrivePin2, HIGH);
  //  delayMicroseconds(dtime);

  //  int raw = analogRead(salinityAnalogPin);

  //  if (raw > 0) {
  //    float Vout = (raw / 4095.0) * Vin;
  //    if (Vout > 0.001 && Vout < Vin) {
  //      float buffer = (Vin / Vout) - 1.0;
  //      float R2 = R1 * buffer;
  //      tot += R2;
  //      validSamples++;
  //    }
  //  }
  //}

  //if (validSamples == 0) return -1.0;
  //return tot / validSamples;
//} // Salinity Sensor Stuff added 3/20/2026

//getting into the net
void setup() {
  //sensors.begin(); //aded today

  Serial.begin(115200);
  dht.begin();
  delay(2000);

  // LCD Salinity Sensor Stuff added 3/24/2026
  //Wire.begin(22, 23);
  //lcd.init();
  //lcd.backlight();
  //lcd.clear();
  //lcd.setCursor(0, 0);
  //lcd.print("Starting...");

  // Pump Stuff added 2/20/2026
  pinMode(PUMP_PIN, OUTPUT); // added 2/20/2026
  //digitalWrite(PUMP_PIN, HIGH); // added 2/20/2026
  //delay(5000); // added 2/20/2026
  //digitalWrite(PUMP_PIN, LOW); // added 2/20/2026

  // TDS Sensor Stuff added 11/15/2025
  analogReadResolution(12);                    // 0–4095 // TDS Sensor Stuff added 11/15/2025
  analogSetPinAttenuation(TDS_PIN, ADC_11db);  // up to ~3.3 V // TDS Sensor Stuff added 11/15/2025

  //analogSetPinAttenuation(salinityAnalogPin, ADC_11db); // Salinity Sensor Stuff added 3/20/2026
  //pinMode(salinityDrivePin1, OUTPUT); // Salinity Sensor Stuff added 3/20/2026
  //pinMode(salinityDrivePin2, OUTPUT); // Salinity Sensor Stuff added 3/20/2026

  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected to WiFi!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (WiFi.status() == WL_CONNECTED) {
    float tempC = dht.readTemperature();
    float humidity = dht.readHumidity();

    if (isnan(tempC) || isnan(humidity)) {
      Serial.println("Failed to read from DHT sensor!");
      delay(2500);
      return;
    }

    float tdsVoltage = readAveragedVoltage(TDS_PIN); // TDS Sensor Stuff added 11/15/2025
    float tdsPPM = voltsToTDSppm(tdsVoltage, tempC); // TDS Sensor Stuff added 11/15/2025

    // Salinity Sensor Stuff added 3/20/2026
    //float salinityResistance = measureSalinityResistance(); // Salinity Sensor Stuff added 3/20/2026

    // LCD Salinity Sensor Stuff added 3/20/2026
    //lcd.clear();

    //lcd.setCursor(0, 0);
    //lcd.print("S:");
    //lcd.print(salinityResistance, 0);
    //lcd.print(" ohm");

    //lcd.setCursor(0, 1);
    //lcd.print("T:");
    //lcd.print(tempC, 1);
    //lcd.print(" C");

    //Serial.print("TDS: "); // probably delete
    //Serial.print(tdsPPM, 1); // probably delete
    //Serial.print("  Salinity Resistance: "); // Salinity Sensor Stuff added 3/20/2026
    //Serial.print(salinityResistance, 1); // Salinity Sensor Stuff added 3/20/2026
    //Serial.println(" ohms"); // Salinity Sensor Stuff added 3/20/2026
    //Serial.println(analogRead(35)); // added today 
    
    Serial.print("Temp C: "); // TDS Sensor Stuff added 11/15/2025
    Serial.print(tempC, 2); // TDS Sensor Stuff added 11/15/2025
    Serial.print("  Humidity: "); // TDS Sensor Stuff added 11/15/2025
    Serial.print(humidity, 2); // TDS Sensor Stuff added 11/15/2025
    Serial.print("%  TDS_V: "); // TDS Sensor Stuff added 11/15/2025
    Serial.print(tdsVoltage, 3); // TDS Sensor Stuff added 11/15/2025
    Serial.print(" V  TDS: "); // TDS Sensor Stuff added 11/15/2025
    Serial.print(tdsPPM, 1); // TDS Sensor Stuff added 11/15/2025
    Serial.println(" ppm"); // TDS Sensor Stuff added 11/15/2025

    // Build JSON payload
    String payload = "{";
    payload += "\"device_id\":\"esp32_dht22\",";
    payload += "\"timestamp\":\"" + String(millis()) + "\",";
    payload += "\"readings\":{";
    payload += "\"temp_c\":" + String(tempC, 2) + ",";
    payload += "\"moisture\":" + String(humidity, 2) + ",";
    payload += "\"ph\":null,"; // comma added at the end 11/15/2025
    payload += "\"tds_ppm\":" + String(tdsPPM, 1); // TDS Sensor Stuff added 11/15/2025
    payload += "}}";

    Serial.println("Posting data to server...");
    Serial.println(payload);

    HTTPClient http;
    http.begin(serverURL);
    http.addHeader("Content-Type", "application/json");

    int httpResponseCode = http.POST(payload);

    if (httpResponseCode > 0) {
      Serial.print("Server response code: ");
      Serial.println(httpResponseCode);
      Serial.println(http.getString());
    } else {
      Serial.print("Error sending POST: ");
      Serial.println(httpResponseCode);
    }

    http.end();
  } else {
    Serial.println("WiFi disconnected, retrying...");
    WiFi.reconnect();
  }

  delay(5000); // send every 5 seconds
}
