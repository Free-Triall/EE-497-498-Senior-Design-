#include <Wire.h>                 // LCD I2C
#include <LiquidCrystal_I2C.h>
#include <OneWire.h>              // Temp sensor
#include <DallasTemperature.h>

// Temperature sensor
#define ONE_WIRE_BUS 12           // DS18B20 on pin 12
OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

// LCD (0x27)
LiquidCrystal_I2C lcd(0x27, 16, 2); 

// Pins & measurement variables
int analogPin = A0;               // use A0 explicitly
int dtime = 500;                  // us
int raw = 0;
float Vin = 5.0;
float Vout = 0;
float R1 = 1000.0;
float R2 = 0;
float buff = 0;
float avg = 0;
int samples = 5000;
int state = 0;
int button = 0;
int buttonPin = 5;

//  Calibration 
float CalibrationTemp = 21.0;     // reference temperature
float CorrectionFactor = 1.02;    // adjust if needed
float dTemp = 0;

// State 0 = rest
// State 1 = measure
// State 2 = print

void setup() {
  sensors.begin();                // start up temperature library

  pinMode(8, OUTPUT);             // AC drive pins
  pinMode(7, OUTPUT);

  pinMode(12, INPUT);             // thermometer pin as input (DS18B20)
  pinMode(buttonPin, INPUT);      // button with external resistor like in instructable

  Serial.begin(9600);             // start serial

  // LCD init
  lcd.init();                     
  lcd.backlight();                
  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Salinity meter");
  lcd.setCursor(0, 1);
  lcd.print("Press button");
}

void loop() {
  // ---------- REST ----------
  button = digitalRead(buttonPin);
  if (button == HIGH && state == 0) {   // button pressed -> start
    lcd.clear();
    lcd.setCursor(4, 0);
    lcd.print("Starting");
    lcd.setCursor(2, 1);
    lcd.print("measurement");
    state = 1;
  }

  // ---------- MEASURE ----------
  if (state == 1) {
    float tot = 0;
    for (int i = 0; i < samples; i++) {
      digitalWrite(7, HIGH);
      digitalWrite(8, LOW);
      delayMicroseconds(dtime);
      digitalWrite(7, LOW);
      digitalWrite(8, HIGH);
      delayMicroseconds(dtime);

      raw = analogRead(analogPin);
      if (raw) {
        buff = raw * Vin;
        Vout = buff / 1024.0;
        buff = (Vin / Vout) - 1.0;
        R2 = R1 * buff;
        tot += R2;
      }
    }
    avg = tot / samples;

    Serial.print("Average resistance is: ");
    Serial.print(avg);
    Serial.println(" Ohm");

    // Temperature + correction
    sensors.requestTemperatures(); 
    float temp = sensors.getTempCByIndex(0);

    Serial.print("Temperature: ");
    Serial.print(temp);
    Serial.print(" C  |  ");

    dTemp = temp - CalibrationTemp;
    avg = avg * pow(CorrectionFactor, dTemp);

    Serial.print("Corrected resistance is: ");
    Serial.println(avg);

    state = 2;
  }

  // ---------- PRINT ----------
  if (state == 2) {
    lcd.clear();

    if (avg > 2000) {
      Serial.println("This is demineralised water.");
      lcd.setCursor(1, 0);
      lcd.print("Demi water");
    }
    else if (avg > 1000) {
      Serial.println("This is fresh/tap water.");
      lcd.setCursor(1, 0);
      lcd.print("Tap water");
    }
    else if (avg > 190) {
      Serial.println("This is brackish water.");
      lcd.setCursor(0, 0);
      lcd.print("Brackish water");
    }
    else { // avg <= 190
      Serial.println("This is seawater.");
      lcd.setCursor(1, 0);
      lcd.print("Sea water");
    }

    lcd.setCursor(0, 1);
    lcd.print("AVG: ");
    lcd.print(avg, 0);   // integer ohms

    delay(4000);         // show result

    // Back to idle
    lcd.clear();
    lcd.setCursor(0, 0);
    lcd.print("Press button");
    state = 0;
  }
}
