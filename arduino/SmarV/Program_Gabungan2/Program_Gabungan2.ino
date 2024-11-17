#include <Wire.h>           // Library for I2C communication
#include <RTClib.h>         // Library for RTC DS3231
#include <HardwareSerial.h> // Include the HardwareSerial library
#include "pitches.h"

const int trigPin = 17;
const int echoPin = 18;
#define SOUND_SPEED 0.034
#define CM_TO_INCH 0.393701
long duration;
float distanceCm;
float distanceInch;

#define BUTTON_PIN 4        // Pin for the button
#define BUZZER_PIN 38       // Pin for the buzzer
#define AO_PIN 5           // Pin for the light sensor

RTC_DS3231 rtc;             // Create an instance of the RTC DS3231 class

#define SDA_PIN 8    // Define SDA pin
#define SCL_PIN 9    // Define SCL pin

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
  
  playMelody(); // Play the melody when the ESP32 is powered on
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
    if (count > 4) {    // Maximum count, reset to default
      count = 1;
      Serial.println("Medication frequency reset to default.");
    } else {
      Serial.print("Medication frequency set to ");
      Serial.print(count);
      Serial.println(" times per day.");
    }
    playBuzzer(count);  // Play buzzer based on count
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
      }
      break;
    case 2:
      if (hour == 12 || hour == 0) {
        activateBuzzer(); // Activate the buzzer
      }
      break;
    case 3:
      if (hour == 8 || hour == 16 || hour == 0) {
        activateBuzzer(); // Activate the buzzer
      }
      break;
    case 4:
      if (hour == 6 || hour == 12 || hour == 18 || hour == 0) {
        activateBuzzer(); // Activate the buzzer
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

// Function to activate the buzzer and play a melody
void activateBuzzer() {
  for (int i = 0; i < 3; i++) {  // Three beeps
    tone(BUZZER_PIN, 1000);      // Frequency of beep
    delay(200);                  // Duration of beep
    noTone(BUZZER_PIN);          // Stop beep
    delay(200);                  // Pause between beeps
  }
}

// Function to play melody when the ESP32 is powered on
void playMelody() {
  int melody[] = { NOTE_C4, NOTE_G3, NOTE_G3, NOTE_A3, NOTE_G3, 0, NOTE_B3, NOTE_C4 };
  int noteDurations[] = { 4, 8, 8, 4, 4, 4, 4, 4 };

  for (int thisNote = 0; thisNote < 8; thisNote++) {
    int noteDuration = 1000 / noteDurations[thisNote];
    tone(BUZZER_PIN, melody[thisNote], noteDuration);

    int pauseBetweenNotes = noteDuration * 1.30;
    delay(pauseBetweenNotes);
    noTone(BUZZER_PIN);
  }
}

// Function to play buzzer based on count
void playBuzzer(int count) {
  for (int i = 0; i < count; i++) {
    tone(BUZZER_PIN, 1000); // Frequency of beep
    delay(200);             // Duration of beep
    noTone(BUZZER_PIN);     // Stop beep
    delay(200);             // Pause between beeps
  }
}
