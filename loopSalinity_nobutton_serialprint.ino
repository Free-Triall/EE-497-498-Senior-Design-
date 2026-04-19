#include <Wire.h>                 // LCD I2C
#include <LiquidCrystal_I2C.h>
#include <OneWire.h>              // Temp sensor
#include <DallasTemperature.h>
#include <math.h>

// Temperature sensor
#define ONE_WIRE_BUS 23           // DS18B20 on pin 12 //originally 12
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// LCD (0x27)
LiquidCrystal_I2C lcd(0x27, 16, 2); 

// Pins & measurement variables
int analogPin = 32;               // use A0 explicitly (originally)
int dtime = 300;                  // microsec
int raw = 0;
float Vin = 3.3;                  //originally 5 V
float Vout = 0;
float R1 = 1000.0;
float R2 = 0;
float buff = 0;
float avg = 0;
int samples = 5000;
int button = 0;
int buttonPin = 27; //originally 5

bool running = true;
bool buttonPress = LOW;
float tempC = 0;

//  Calibration 
float CalibrationTemp = 21.0;     // reference temperature
float CorrectionFactor = 1.02;    // adjust if needed
float dTemp = 0;

// State 0 = rest
// State 1 = measure
// State 2 = print

void setup() {
  sensors.begin();                // start up temperature library

  pinMode(4, OUTPUT);             // AC drive pins //originally 8
  pinMode(18, OUTPUT);            // originally 7

  pinMode(ONE_WIRE_BUS, INPUT);   // thermometer pin as input (DS18B20) // originally 12
  pinMode(buttonPin, INPUT);      // button with external resistor like in instructable

  Serial.begin(9600);             // start serial
  delay(1000);                    // give time for Serial Monitor

  Serial.println("=== Salinity Meter Started ===");

  // LCD init
  lcd.init();
  lcd.backlight();
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Salinity meter");
  lcd.setCursor(0, 1);
  lcd.print("Measuring...    ");
}

void loop() {
  // ---------- MEASURE ----------
  if (running) {
    float tot = 0;
    int validSamples = 0;

    for (int i = 0; i < samples; i++) {
      digitalWrite(18, HIGH);           // originally 7
      digitalWrite(4, LOW);
      delayMicroseconds(dtime);
      digitalWrite(18, LOW);            // originally 7
      digitalWrite(4, HIGH);
      delayMicroseconds(dtime);

      raw = analogRead(analogPin);
      if (raw > 0 && raw < 4095) {
        buff = raw * Vin;
        Vout = buff / 4095.0; //originally /1024

        if (Vout > 0.001) {
          buff = (Vin / Vout) - 1.0;
          R2 = R1 * buff;
          tot += R2;
          validSamples++;
        }
      }
    }

    if (validSamples > 0) {
      avg = tot / validSamples;
    }

    // Temperature + correction
    sensors.requestTemperatures(); 
    tempC = sensors.getTempCByIndex(0);

    dTemp = tempC - CalibrationTemp;
    avg = avg * pow(CorrectionFactor, dTemp);

    // ---------- SERIAL PRINT ----------
    Serial.println("----------------------------");
    Serial.print("Temperature: ");
    Serial.print(tempC);
    Serial.println(" C");

    Serial.print("Corrected Resistance: ");
    Serial.print(avg);
    Serial.println(" Ohm");

    if (avg > 5000) {
      Serial.println("Water Type: Demineralised");
    }
    else if (avg > 800) {
      Serial.println("Water Type: Tap/Fresh");
    }
    else if (avg > 100) {
      Serial.println("Water Type: Brackish");
    }
    else { // avg <= 100
      Serial.println("Water Type: Seawater");
    }

    // ---------- PRINT ----------
    lcd.clear();

    if (avg > 5000) {
      lcd.setCursor(1, 0);
      lcd.print("Demi water");
    }
    else if (avg > 800) {
      lcd.setCursor(1, 0);
      lcd.print("Tap water");
    }
    else if (avg > 100) {
      lcd.setCursor(0, 0);
      lcd.print("Brackish water");
    }
    else { // avg <= 100
      lcd.setCursor(1, 0);
      lcd.print("Sea water");
    }

    lcd.setCursor(0, 1);
    lcd.print(tempC, 1);
    lcd.print((char)223);
    lcd.print("C ");
    lcd.print(avg, 0);

    delay(1000);         // show result / update once per second
  }
}