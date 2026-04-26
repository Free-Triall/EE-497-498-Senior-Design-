// Libraries needed
#include <WiFi.h>
#include <HTTPClient.h>
#include "DHT.h" //Calling device DHT.h
#include <OneWire.h>           // Salinity DS18B20 temp sensor added 4/25/2026
#include <DallasTemperature.h> // Salinity DS18B20 temp sensor added 4/25/2026
#include <math.h>              // Salinity math added 4/25/2026

//DHT libs and pins
#define DHTPIN 4     
#define DHTTYPE DHT22 // previously DHT11 but its a different model  

//Pump Pins 
#define PUMP_PIN 18 // added 2/20/2026  
#define PUMP_PIN_2 13 // added 4/10/2026 || second pump

//HC-SR04 pins
#define TRIG_PIN 26 // added 4/12/26
#define ECHO_PIN 27 // added 4/12/26
#define WATER_LOW_CM 15.0  // adjust this after irl tests // added 4/12/26

const int TDS_PIN = 34; // TDS Sensor Stuff added 11/15/2025

// Salinity Sensor Pins added 4/25/2026
#define SAL_DRIVE_A    33  // AC drive pin A
#define SAL_DRIVE_B    25  // AC drive pin B
#define SAL_ANALOG_PIN 32  // analog read pin
#define ONE_WIRE_BUS   23  // DS18B20 data pin

//Wifi Login
const char* ssid = "JoshWifi";
const char* password = "JOSH71903!";

//My FLASK server
const char* serverURL = "http://192.168.4.20:5000/ingest";

DHT dht(DHTPIN, DHTTYPE);

// Salinity sensor objects added 4/25/2026
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature salinityTempSensor(&oneWire);

// Salinity measurement variables added 4/25/2026
int   sal_dtime      = 300;   // microseconds per AC half-cycle
float sal_Vin        = 3.3;
float sal_R1         = 1000.0;
int   sal_samples    = 5000;
float sal_CalTemp    = 21.0;  // reference temp for correction
float sal_CorrFactor = 1.02;  // adjust after irl testing

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

// Website Pump button added 4/11/2025
void checkPumpState() {
  HTTPClient http;
  http.begin("http://192.168.4.20:5000/pump/state");
  int code = http.GET();
  if (code == 200) {
    String body = http.getString();
    // simple string checks, no JSON library needed
    bool fillerOn  = body.indexOf("\"filler\": true")  != -1 || body.indexOf("\"filler\":true")  != -1;
    bool suctionOn = body.indexOf("\"suction\": true") != -1 || body.indexOf("\"suction\":true") != -1;
    digitalWrite(PUMP_PIN,   fillerOn  ? HIGH : LOW);
    digitalWrite(PUMP_PIN_2, suctionOn ? HIGH : LOW);
  }
  http.end();
}

//Water level stuff // added 4/12/26
float readWaterDistanceCM() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
  if (duration == 0) return -1;
  return (duration * 0.0343) / 2.0;
}

// Salinity read function added 4/25/2026
// returns corrected resistance in Ohms, or -1 on failure
float readSalinityOhm() {
  float tot        = 0;
  int validSamples = 0;

  for (int i = 0; i < sal_samples; i++) {
    digitalWrite(SAL_DRIVE_A, HIGH);
    digitalWrite(SAL_DRIVE_B, LOW);
    delayMicroseconds(sal_dtime);
    digitalWrite(SAL_DRIVE_A, LOW);
    digitalWrite(SAL_DRIVE_B, HIGH);
    delayMicroseconds(sal_dtime);

    int raw = analogRead(SAL_ANALOG_PIN);
    if (raw > 0 && raw < 4095) {
      float vout = (raw * sal_Vin) / 4095.0;
      if (vout > 0.001) {
        float r2 = sal_R1 * ((sal_Vin / vout) - 1.0);
        tot += r2;
        validSamples++;
      }
    }
  }

  if (validSamples == 0) return -1;

  // temperature correction using DS18B20 added 4/25/2026
  salinityTempSensor.requestTemperatures();
  float waterTempC = salinityTempSensor.getTempCByIndex(0);
  float avg = (tot / validSamples) * pow(sal_CorrFactor, waterTempC - sal_CalTemp);

  return avg;
}

// Salinity label helper added 4/25/2026
String salinityType(float resistance) {
  if      (resistance > 5000) return "Demineralised";
  else if (resistance > 800)  return "Tap/Fresh";
  else if (resistance > 100)  return "Brackish";
  else                        return "Seawater";
}

//getting into the net
void setup() {
 
  // Water level stuff added 4/12/26
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);

  //DHT22
  Serial.begin(115200);
  dht.begin();
  delay(2000);

  // Pump Stuff added 2/20/2026
  pinMode(PUMP_PIN, OUTPUT); // added 2/20/2026
  //digitalWrite(PUMP_PIN, HIGH); // added 2/20/2026
  //delay(5000); // added 2/20/2026
  //digitalWrite(PUMP_PIN, LOW); // added 2/20/2026
  
  //Pump 2 added 4/10/26
  pinMode(PUMP_PIN_2, OUTPUT); // added 4/10/2026
  //digitalWrite(PUMP_PIN_2, HIGH);
  //delay(5000);
  //digitalWrite(PUMP_PIN_2, LOW);

  // TDS Sensor Stuff added 11/15/2025
  analogReadResolution(12);                    // 0–4095 // TDS Sensor Stuff added 11/15/2025
  analogSetPinAttenuation(TDS_PIN, ADC_11db);  // up to ~3.3 V // TDS Sensor Stuff added 11/15/2025

  // Salinity sensor setup added 4/25/2026
  pinMode(SAL_DRIVE_A, OUTPUT); // added 4/25/2026
  pinMode(SAL_DRIVE_B, OUTPUT); // added 4/25/2026
  salinityTempSensor.begin();   // added 4/25/2026
  analogSetPinAttenuation(SAL_ANALOG_PIN, ADC_11db); // up to ~3.3 V // added 4/25/2026

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

    float waterDistCM = readWaterDistanceCM(); // HC-SR04 stuff added 4/12/2026
    bool waterLow = (waterDistCM > WATER_LOW_CM || waterDistCM < 0); // HC-SR04 stuff added 4/12/2026
    Serial.print("Water Distance: "); // HC-SR04 stuff added 4/12/2026
    Serial.print(waterDistCM); // HC-SR04 stuff added 4/12/2026
    Serial.println(" cm"); // HC-SR04 stuff added 4/12/2026
    
    Serial.print("Temp C: "); // TDS Sensor Stuff added 11/15/2025
    Serial.print(tempC, 2); // TDS Sensor Stuff added 11/15/2025
    Serial.print("  Humidity: "); // TDS Sensor Stuff added 11/15/2025
    Serial.print(humidity, 2); // TDS Sensor Stuff added 11/15/2025
    Serial.print("%  TDS_V: "); // TDS Sensor Stuff added 11/15/2025
    Serial.print(tdsVoltage, 3); // TDS Sensor Stuff added 11/15/2025
    Serial.print(" V  TDS: "); // TDS Sensor Stuff added 11/15/2025
    Serial.print(tdsPPM, 1); // TDS Sensor Stuff added 11/15/2025
    Serial.println(" ppm"); // TDS Sensor Stuff added 11/15/2025

    // Salinity added 4/25/2026
    float salinityOhm    = readSalinityOhm(); // added 4/25/2026
    String salinityLabel = salinityType(salinityOhm); // added 4/25/2026

    // Water temp from DS18B20 for dashboard added 4/25/2026
    salinityTempSensor.requestTemperatures(); // added 4/25/2026
    float waterTempC = salinityTempSensor.getTempCByIndex(0); // added 4/25/2026

    Serial.print("Salinity Resistance: "); // added 4/25/2026
    Serial.print(salinityOhm); // added 4/25/2026
    Serial.print(" Ohm  Type: "); // added 4/25/2026
    Serial.println(salinityLabel); // added 4/25/2026
    Serial.print("Water Temp: "); // added 4/25/2026
    Serial.print(waterTempC, 2); // added 4/25/2026
    Serial.println(" C"); // added 4/25/2026

    // Build JSON payload
    String payload = "{";
    payload += "\"device_id\":\"esp32_dht22\",";
    payload += "\"timestamp\":\"" + String(millis()) + "\",";
    payload += "\"readings\":{";
    payload += "\"temp_c\":" + String(tempC, 2) + ",";
    payload += "\"moisture\":" + String(humidity, 2) + ",";
    //payload += "\"ph\":null,"; // comma added at the end 11/15/2025
    payload += "\"tds_ppm\":" + String(tdsPPM, 1); // TDS Sensor Stuff added 11/15/2025
    payload += ",\"water_dist_cm\":" + String(waterDistCM, 1); // HC-SR04 stuff added 4/12/2026
    payload += ",\"water_low\":" + String(waterLow ? "true" : "false"); // HC-SR04 stuff added 4/12/2026
    payload += ",\"salinity_ohm\":" + String(salinityOhm, 1); // added 4/25/2026
    payload += ",\"salinity_type\":\"" + salinityLabel + "\""; // added 4/25/2026
    payload += ",\"water_temp_c\":" + String(waterTempC, 2); // added 4/25/2026
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
    checkPumpState(); //added 4/11/26
  } else {
    Serial.println("WiFi disconnected, retrying...");
    WiFi.reconnect();
  }

  delay(5000); // send every 5 seconds
}