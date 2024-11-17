#include <Wire.h>           // Library for I2C communication
#include <RTClib.h>         // Library for RTC DS3231
#include <HardwareSerial.h> // Include the HardwareSerial library

const int trigPin = 5;
const int echoPin = 16;
#define SOUND_SPEED 0.034
#define CM_TO_INCH 0.393701
long duration;
float distanceCm;
float distanceInch;

#define BUTTON_PIN 4        // Pin for the button
#define BUZZER_PIN 3        // Pin for the buzzer
#define AO_PIN 10           // Pin for the light sensor

RTC_DS3231 rtc;             // Create an instance of the RTC DS3231 class

#define SDA_PIN 21    // Define SDA pin
#define SCL_PIN 20    // Define SCL pin

int lastButtonState = HIGH; // Previous state of the button
int count = 1;              // Default medication frequency

void setup() {
  Serial.begin(115200);     // Initialize serial communication
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);  // Set the button pin as input with internal pull-up resistor
  pinMode(BUZZER_PIN, OUTPUT);        // Set the buzzer pin as output
  Wire.begin(SDA_PIN, SCL_PIN);   // Initialize the I2C bus with SDA and SCL pins
  rtc.begin();                    // Initialize the RTC module
}

void loop() {
  // Ultrasonic Sensor
  digitalWrite(trigPin, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin, LOW);
  duration = pulseIn(echoPin, HIGH);
  distanceCm = duration * SOUND_SPEED / 2;
  distanceInch = distanceCm * CM_TO_INCH;

  // Button Functionality
  int buttonState = digitalRead(BUTTON_PIN); // Read the state of the button
  if (buttonState == LOW && lastButtonState == HIGH) {
    count++;
    if (count > 5) {    // Maximum count, reset to default
      count = 1;
      Serial.println("Medication frequency reset to default.");
    } else {
      Serial.print("Medication frequency set to ");
      Serial.print(count);
      Serial.println(" times per day.");
    }
  }
  lastButtonState = buttonState; // Update lastButtonState

  // RTC Alarm
  DateTime now = rtc.now(); // Get current time from RTC
  int hour = now.hour();    // Get current hour
  // Check if it's time for medication
  switch (count) {
    case 1:
      if (hour == 12) {
        activateBuzzer(); // Activate the buzzer
        delay(1000);      // Buzzer sound duration
      }
      break;
    case 2:
      if (hour == 12 || hour == 0) {
        activateBuzzer(); // Activate the buzzer
        delay(1000);      // Buzzer sound duration
      }
      break;
    case 3:
      if (hour == 8 || hour == 16 || hour == 0) {
        activateBuzzer(); // Activate the buzzer
        delay(1000);      // Buzzer sound duration
      }
      break;
    case 4:
      if (hour == 6 || hour == 12 || hour == 18 || hour == 0) {
        activateBuzzer(); // Activate the buzzer
        delay(1000);      // Buzzer sound duration
      }
      break;
    case 5:
      if (hour % 4 == 0) {
        activateBuzzer(); // Activate the buzzer
        delay(1000);      // Buzzer sound duration
      }
      break;
  }

  // Light Sensor
  int lightValue = analogRead(AO_PIN);

  // Send sensor data over serial
  Serial.print(distanceCm);
  Serial.print(",");
  Serial.print(lightValue);
  Serial.println();

  delay(1000);
}

// Function to activate the buzzer
void activateBuzzer() {
  digitalWrite(BUZZER_PIN, HIGH); // Turn on the buzzer
}
