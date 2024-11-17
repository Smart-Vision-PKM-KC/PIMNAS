#include <Wire.h>           // Library for I2C communication
#include <RTClib.h>         // Library for RTC DS3231
#include <HardwareSerial.h> // Include the HardwareSerial library
#include "pitches.h"
#include <Preferences.h>    // Include the Preferences library
#include <WiFi.h>    
#include <HTTPClient.h>
#include <UrlEncode.h>

const char* ssid = "Xiaomi12";
const char* password = "1sampai100";
String phoneNumber = "+628157634608";
String apiKey = "8088026";

const int trigPin = 17;
const int echoPin = 18;
#define SOUND_SPEED 0.034
#define CM_TO_INCH 0.393701
long duration;
float distanceCm;
float distanceInch;

#define BUTTON_PIN 4        // Pin for the button
#define BUZZER_PIN 38       // Pin for the buzzer
#define AO_PIN 5            // Pin for the light sensor

RTC_DS3231 rtc;             // Create an instance of the RTC DS3231 class

#define SDA_PIN 8           // Define SDA pin
#define SCL_PIN 9           // Define SCL pin

Preferences preferences;    // Create a Preferences object
int lastButtonState = HIGH; // Previous state of the button
int buttonState;            // Current state of the button
unsigned int count;         // Medication frequency
bool wifiConnected = false; // Track WiFi connection status

int lastAlarmHour = -1;     // To track the last hour the alarm was triggered

void setup() {
  Serial.begin(115200);     // Initialize serial communication
  pinMode(trigPin, OUTPUT);
  pinMode(echoPin, INPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);  // Set the button pin as input with internal pull-up resistor
  pinMode(BUZZER_PIN, OUTPUT);        // Set the buzzer pin as output
  Wire.begin(SDA_PIN, SCL_PIN);       // Initialize the I2C bus with SDA and SCL pins
  rtc.begin();                        // Initialize the RTC module

  // Open Preferences with namespace "medication"
  preferences.begin("medication", false);

  // Get the current count value from Preferences, default to 3 if not found
  count = preferences.getUInt("count", 3);
  if (count < 1 || count > 4) {
    count = 3;
    preferences.putUInt("count", count);
  }

  // Decrement the counter, but don't let it go below 0
  if (count > 0) {
    count--;
    preferences.putUInt("counter", count);
  }

  Serial.printf("Boot detected. Counter decremented. Current value: %u\n", count);

  // Debug print to check the retrieved count value
  Serial.print("Retrieved count from Preferences: ");
  Serial.println(count);

  Serial.print("Medication frequency set to ");
  Serial.print(count);
  Serial.println(" times per day.");
  playMelody(); // Play the melody when the ESP32 is powered on

  // Attempt to connect to WiFi
  WiFi.begin(ssid, password);
  Serial.println("Connecting to WiFi...");
  unsigned long startAttemptTime = millis();

  // Wait for connection or timeout after 10 seconds
  while (WiFi.status() != WL_CONNECTED && millis() - startAttemptTime < 10000) {
    delay(500);
    Serial.print(".");
  }

  if (WiFi.status() == WL_CONNECTED) {
    wifiConnected = true;
    Serial.println("");
    Serial.print("Connected to WiFi network with IP Address: ");
    Serial.println(WiFi.localIP());
  } else {
    wifiConnected = false;
    Serial.println("");
    Serial.println("Failed to connect to WiFi. Continuing without WiFi.");
  }
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
  buttonState = digitalRead(BUTTON_PIN); // Read the state of the button

  if (buttonState == LOW && lastButtonState == HIGH) {
    delay(50); // Debounce delay
    if (digitalRead(BUTTON_PIN) == LOW) {
      count++;
      if (count > 4) {    // Maximum count, reset to 1
        count = 1;
        Serial.println("Medication frequency reset to default.");
      } else {
        Serial.print("Medication frequency set to ");
        Serial.print(count);
        Serial.println(" times per day.");
      }
      preferences.putUInt("count", count);  // Save count to Preferences
      playBuzzer(count);  // Play buzzer based on count
    }
  }
  lastButtonState = buttonState; // Update lastButtonState

  // RTC Alarm
  DateTime now = rtc.now(); // Get current time from RTC
  int hour = now.hour();    // Get current hour
  // Check if it's time for medication and if the alarm hasn't rung in this hour
  if (hour != lastAlarmHour) {
    switch (count) {
      case 1:
        if (hour == 12) {
          sendMedicationReminder(now); // Send reminder and activate buzzer
          lastAlarmHour = hour;
        }
        break;
      case 2:
        if (hour == 12 || hour == 0) {
          sendMedicationReminder(now); // Send reminder and activate buzzer
          lastAlarmHour = hour;
        }
        break;
      case 3:
        if (hour == 8 || hour == 16 || hour == 0) {
          sendMedicationReminder(now); // Send reminder and activate buzzer
          lastAlarmHour = hour;
        }
        break;
      case 4:
        if (hour == 6 || hour == 12 || hour == 18 || hour == 24) {
          sendMedicationReminder(now);
          lastAlarmHour = hour;
        }
        break;
    }
  }

  // Light Sensor
  int lightValue = analogRead(AO_PIN);

  // Send sensor data over serial
  Serial.print(distanceCm);
  Serial.print(",");
  Serial.print(lightValue);
  Serial.println();

  // Check for detected medicine class from serial
  if (Serial.available() > 0) {
    // Baca data dari serial
    String className = Serial.readStringUntil('\n');
    
    // Hapus karakter whitespace dari awal dan akhir string
    className.trim();
    
    // Dapatkan waktu sekarang untuk ditambahkan ke pesan
    DateTime now = rtc.now(); // Update current time
    String currentTime = now.timestamp(DateTime::TIMESTAMP_FULL);
    
    // Proses data yang diterima dan kirim pesan WhatsApp jika WiFi terhubung
    if (wifiConnected) {
      if (className == "Neozep Forte") {
        Serial.println("Neozep Forte terdeteksi");
        sendMessage("Alat mendeteksi Neozep Forte pada " + currentTime);
      } else if (className == "Intunal F") {
        Serial.println("Intunal F terdeteksi");
        sendMessage("Alat mendeteksi Intunal F pada " + currentTime);
      } else if (className == "Paramex") {
        Serial.println("Paramex terdeteksi");
        sendMessage("Alat mendeteksi Paramex pada " + currentTime);
      } else if (className == "Biogesic Paracetamol") {
        Serial.println("Biogesic Paracetamol terdeteksi");
        sendMessage("Alat mendeteksi Biogesic Paracetamol pada " + currentTime);
      } else if (className == "Bodrex Extra") {
        Serial.println("Bodrex Extra terdeteksi");
        sendMessage("Alat mendeteksi Bodrex Extra pada " + currentTime);
      } else if (className == "Bodrex Flu dan Batuk PE") {
        Serial.println("Bodrex Flu dan Batuk PE terdeteksi");
        sendMessage("Alat mendeteksi Bodrex Flu dan Batuk PE pada " + currentTime);
      } else if (className == "Bodrex Migra") {
        Serial.println("Bodrex Migra terdeteksi");
        sendMessage("Alat mendeteksi Bodrex Migra pada " + currentTime);
      } else if (className == "Decolgen") {
        Serial.println("Decolgen terdeteksi");
        sendMessage("Alat mendeteksi Decolgen pada " + currentTime);
      } else if (className == "Decolsin") {
        Serial.println("Decolsin terdeteksi");
        sendMessage("Alat mendeteksi Decolsin pada " + currentTime);
      } else if (className == "Dumin Paracetamol") {
        Serial.println("Dumin Paracetamol terdeteksi");
        sendMessage("Alat mendeteksi Dumin Paracetamol pada " + currentTime);
      } else if (className == "Insana Flu") {
        Serial.println("Insana Flu terdeteksi");
        sendMessage("Alat mendeteksi Insana Flu pada " + currentTime);
      } else if (className == "Intunal Kaplet") {
        Serial.println("Intunal Kaplet terdeteksi");
        sendMessage("Alat mendeteksi Intunal Kaplet pada " + currentTime);
      } else if (className == "Inza") {
        Serial.println("Inza terdeteksi");
        sendMessage("Alat mendeteksi Inza pada " + currentTime);
      } else if (className == "Mixagrip Flu") {
        Serial.println("Mixagrip Flu terdeteksi");
        sendMessage("Alat mendeteksi Mixagrip Flu pada " + currentTime);
      } else if (className == "Mixagrip Flu dan Batuk") {
        Serial.println("Mixagrip Flu dan Batuk terdeteksi");
        sendMessage("Alat mendeteksi Mixagrip Flu dan Batuk pada " + currentTime);
      } else if (className == "Neo Rheumacyl") {
        Serial.println("Neo Rheumacyl terdeteksi");
        sendMessage("Alat mendeteksi Neo Rheumacyl pada " + currentTime);
      } else if (className == "Oskadon Sakit Kepala") {
        Serial.println("Oskadon Sakit Kepala terdeteksi");
        sendMessage("Alat mendeteksi Oskadon Sakit Kepala pada " + currentTime);
      } else if (className == "Oskadon SP") {
        Serial.println("Oskadon SP terdeteksi");
        sendMessage("Alat mendeteksi Oskadon SP pada " + currentTime);
      } else if (className == "Pamol Paracetamol") {
        Serial.println("Pamol Paracetamol terdeteksi");
        sendMessage("Alat mendeteksi Pamol Paracetamol pada " + currentTime);
      } else if (className == "Panadol Cold Flu") {
        Serial.println("Panadol Cold Flu terdeteksi");
        sendMessage("Alat mendeteksi Panadol Cold Flu pada " + currentTime);
      } else if (className == "Panadol Extra Paracetamol") {
        Serial.println("Panadol Extra Paracetamol terdeteksi");
        sendMessage("Alat mendeteksi Panadol Extra Paracetamol pada " + currentTime);
      } else if (className == "Panadol Paracetamol") {
        Serial.println("Panadol Paracetamol terdeteksi");
        sendMessage("Alat mendeteksi Panadol Paracetamol pada " + currentTime);
      } else if (className == "Paramex Flu dan Batuk PE") {
        Serial.println("Paramex Flu dan Batuk PE terdeteksi");
        sendMessage("Alat mendeteksi Paramex Flu dan Batuk PE pada " + currentTime);
      } else if (className == "Paramex Nyeri Otot") {
        Serial.println("Paramex Nyeri Otot terdeteksi");
        sendMessage("Alat mendeteksi Paramex Nyeri Otot pada " + currentTime);
      } else if (className == "Poldan MIG") {
        Serial.println("Poldan MIG terdeteksi");
        sendMessage("Alat mendeteksi Poldan MIG pada " + currentTime);
      } else if (className == "Procold Flu") {
        Serial.println("Procold Flu terdeteksi");
        sendMessage("Alat mendeteksi Procold Flu pada " + currentTime);
      } else if (className == "Procold Flu dan Batuk") {
        Serial.println("Procold Flu dan Batuk terdeteksi");
        sendMessage("Alat mendeteksi Procold Flu dan Batuk pada " + currentTime);
      } else if (className == "Sanaflu") {
        Serial.println("Sanaflu terdeteksi");
        sendMessage("Alat mendeteksi Sanaflu pada " + currentTime);
      } else if (className == "Sanmol") {
        Serial.println("Sanmol terdeteksi");
        sendMessage("Alat mendeteksi Sanmol pada " + currentTime);
      } else if (className == "Saridon") {
        Serial.println("Saridon terdeteksi");
        sendMessage("Alat mendeteksi Saridon pada " + currentTime);
      } else if (className == "Saridon Extra") {
        Serial.println("Saridon Extra terdeteksi");
        sendMessage("Alat mendeteksi Saridon Extra pada " + currentTime);
      } else if (className == "Stop Cold") {
        Serial.println("Stop Cold terdeteksi");
        sendMessage("Alat mendeteksi Stop Cold pada " + currentTime);
      } else if (className == "Ultraflu Extra") {
        Serial.println("Ultraflu Extra terdeteksi");
        sendMessage("Alat mendeteksi Ultraflu Extra pada " + currentTime);
      } else if (className == "Ultraflu PE") {
        Serial.println("Ultraflu PE terdeteksi");
        sendMessage("Alat mendeteksi Ultraflu PE pada " + currentTime);
      } else {
        Serial.println("Obat tidak dikenal: " + className);
      }
    }
  }

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

// Function to send medication reminder
void sendMedicationReminder(DateTime now) {
  String currentTime = now.timestamp(DateTime::TIMESTAMP_TIME);
  sendMessage("Saatnya minum obat pada jam " + currentTime);
  activateBuzzer();
}

void sendMessage(String message) {
  String url = "https://api.callmebot.com/whatsapp.php?phone=" + phoneNumber + "&apikey=" + apiKey + "&text=" + urlEncode(message);    
  HTTPClient http;
  http.begin(url);

  // Specify content-type header
  http.addHeader("Content-Type", "application/x-www-form-urlencoded");
  
  // Send HTTP POST request
  int httpResponseCode = http.POST(url);
  if (httpResponseCode == 200) {
    Serial.print("Message sent successfully: ");
    Serial.println(message);
  } else {
    Serial.println("Error sending the message");
    Serial.print("HTTP response code: ");
    Serial.println(httpResponseCode);
  }

  // Free resources
  http.end();
}
