// Libraries needed
#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h" //Calling device DHT.h

#define DHTPIN 4        
#define DHTTYPE DHT11   

// TDS Sensor Stuff added 11/15/2025
const int TDS_PIN = 34;

//Wifi Login
const char* ssid = "";
const char* password = "";

//My FLASK server
const char* serverURL = ""; // Flask URL

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

// TDS Sensor Stuff added 11/15/2025X

//getting into the net
void setup() {
  Serial.begin(115200);
  dht.begin();

  // TDS Sensor Stuff added 11/15/2025
  analogReadResolution(12); // 0–4095 // TDS Sensor Stuff added 11/15/2025
  analogSetPinAttenuation(TDS_PIN, ADC_11db); // up to ~3.3 V // TDS Sensor Stuff added 11/15/2025

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
      delay(2000);
      return;
    }

    float tdsVoltage = readAveragedVoltage(TDS_PIN); // TDS Sensor Stuff added 11/15/2025
    float tdsPPM = voltsToTDSppm(tdsVoltage, tempC); // TDS Sensor Stuff added 11/15/2025

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
    payload += "\"device_id\":\"esp32_dht11\",";
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
