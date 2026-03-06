# ESP32 Algorithm Integration Guide for Farmzy

## Overview

This guide explains how to connect ESP32 microcontrollers with soil sensors to the Farmzy platform via ThingSpeak, enabling real-time soil monitoring and smart farming decisions.

## Architecture

```
ESP32 + Sensors --> ThingSpeak Cloud --> Farmzy Backend --> Farmzy Frontend
                                    --> Farmzy Frontend (direct API)
```

## ThingSpeak Channel Field Mapping

Your ThingSpeak channel must use this exact field mapping:

| Field     | Sensor Data    | Unit   | Typical Range |
|-----------|---------------|--------|---------------|
| field1    | Moisture      | %      | 0 - 100       |
| field2    | pH            | -      | 0 - 14        |
| field3    | Nitrogen (N)  | mg/kg  | 0 - 100+      |
| field4    | Phosphorus (P)| mg/kg  | 0 - 50+       |
| field5    | Potassium (K) | mg/kg  | 0 - 300+      |

## ESP32 Arduino Code Template

### Required Libraries

Install via Arduino Library Manager:
- `WiFi.h` (built-in for ESP32)
- `HTTPClient.h` (built-in for ESP32)

### Wiring

| Sensor          | ESP32 Pin | Notes                          |
|-----------------|-----------|--------------------------------|
| Moisture Sensor | GPIO 34   | Capacitive soil moisture (ADC) |
| pH Sensor       | GPIO 35   | Analog pH probe (ADC)          |
| NPK Sensor      | GPIO 16/17| RS485 Modbus (UART2 TX/RX)     |

### Complete ESP32 Code

```cpp
#include <WiFi.h>
#include <HTTPClient.h>

// ============ CONFIGURATION ============
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// ThingSpeak Configuration
const char* THINGSPEAK_HOST = "http://api.thingspeak.com";
const char* THINGSPEAK_API_KEY = "YOUR_WRITE_API_KEY";  // Write API Key

// Sensor Pins
const int MOISTURE_PIN = 34;    // Capacitive moisture sensor (ADC1)
const int PH_PIN = 35;          // pH sensor analog output (ADC1)
const int NPK_TX_PIN = 17;      // RS485 TX for NPK sensor
const int NPK_RX_PIN = 16;      // RS485 RX for NPK sensor
const int NPK_DE_RE_PIN = 4;    // RS485 DE/RE control pin

// Timing
const unsigned long SEND_INTERVAL = 60000;  // Send every 60 seconds (ThingSpeak free: 15s min)
unsigned long lastSendTime = 0;

// Calibration values (adjust based on your sensors)
const int MOISTURE_DRY = 4095;   // ADC value when sensor is dry
const int MOISTURE_WET = 1500;   // ADC value when sensor is in water
const float PH_OFFSET = 0.0;    // pH calibration offset
const float PH_SLOPE = 3.5;     // pH calibration slope (mV per pH unit)

// NPK Modbus commands (for common NPK RS485 sensors)
byte nitrogen_cmd[] = {0x01, 0x03, 0x00, 0x1E, 0x00, 0x01, 0xE4, 0x0C};
byte phosphorus_cmd[] = {0x01, 0x03, 0x00, 0x1F, 0x00, 0x01, 0xB5, 0xCC};
byte potassium_cmd[] = {0x01, 0x03, 0x00, 0x20, 0x00, 0x01, 0x85, 0xC0};

// ============ SENSOR FUNCTIONS ============

float readMoisture() {
  int raw = analogRead(MOISTURE_PIN);
  // Map ADC value to percentage (0-100%)
  float moisture = map(raw, MOISTURE_DRY, MOISTURE_WET, 0, 100);
  moisture = constrain(moisture, 0, 100);
  return moisture;
}

float readPH() {
  // Average multiple readings for stability
  long total = 0;
  for (int i = 0; i < 10; i++) {
    total += analogRead(PH_PIN);
    delay(10);
  }
  float avgVoltage = (total / 10.0) * (3.3 / 4095.0);
  // Convert voltage to pH (calibrate with known pH solutions)
  float pH = 7.0 + ((2.5 - avgVoltage) / PH_SLOPE) + PH_OFFSET;
  pH = constrain(pH, 0, 14);
  return pH;
}

float readNPKValue(byte* command, int cmdLength) {
  // Send Modbus command via RS485
  digitalWrite(NPK_DE_RE_PIN, HIGH);  // Enable transmit
  delay(1);
  Serial2.write(command, cmdLength);
  Serial2.flush();
  digitalWrite(NPK_DE_RE_PIN, LOW);   // Enable receive
  
  // Wait for response
  delay(100);
  
  byte response[7];
  if (Serial2.available() >= 7) {
    Serial2.readBytes(response, 7);
    // Extract value from Modbus response (bytes 3-4)
    float value = (response[3] << 8) | response[4];
    return value;
  }
  return -1;  // Error
}

float readNitrogen() {
  return readNPKValue(nitrogen_cmd, sizeof(nitrogen_cmd));
}

float readPhosphorus() {
  return readNPKValue(phosphorus_cmd, sizeof(phosphorus_cmd));
}

float readPotassium() {
  return readNPKValue(potassium_cmd, sizeof(potassium_cmd));
}

// ============ THINGSPEAK ============

bool sendToThingSpeak(float moisture, float pH, float nitrogen, float phosphorus, float potassium) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi not connected!");
    return false;
  }
  
  HTTPClient http;
  String url = String(THINGSPEAK_HOST) + "/update?api_key=" + THINGSPEAK_API_KEY
    + "&field1=" + String(moisture, 1)
    + "&field2=" + String(pH, 2)
    + "&field3=" + String(nitrogen, 1)
    + "&field4=" + String(phosphorus, 1)
    + "&field5=" + String(potassium, 1);
  
  http.begin(url);
  int httpCode = http.GET();
  
  if (httpCode == 200) {
    String response = http.getString();
    Serial.println("ThingSpeak entry: " + response);
    http.end();
    return true;
  } else {
    Serial.println("ThingSpeak error: " + String(httpCode));
    http.end();
    return false;
  }
}

// ============ SETUP & LOOP ============

void setup() {
  Serial.begin(115200);
  Serial2.begin(9600, SERIAL_8N1, NPK_RX_PIN, NPK_TX_PIN);  // RS485 for NPK
  
  pinMode(NPK_DE_RE_PIN, OUTPUT);
  digitalWrite(NPK_DE_RE_PIN, LOW);
  
  // Connect to WiFi
  Serial.println("Connecting to WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected! IP: " + WiFi.localIP().toString());
  
  // Initial reading
  delay(2000);
}

void loop() {
  unsigned long now = millis();
  
  if (now - lastSendTime >= SEND_INTERVAL) {
    lastSendTime = now;
    
    // Read all sensors
    float moisture = readMoisture();
    float pH = readPH();
    float nitrogen = readNitrogen();
    float phosphorus = readPhosphorus();
    float potassium = readPotassium();
    
    // Print readings
    Serial.println("--- Sensor Readings ---");
    Serial.printf("Moisture: %.1f%%\n", moisture);
    Serial.printf("pH: %.2f\n", pH);
    Serial.printf("Nitrogen: %.1f mg/kg\n", nitrogen);
    Serial.printf("Phosphorus: %.1f mg/kg\n", phosphorus);
    Serial.printf("Potassium: %.1f mg/kg\n", potassium);
    
    // Send to ThingSpeak
    if (sendToThingSpeak(moisture, pH, nitrogen, phosphorus, potassium)) {
      Serial.println("Data sent to ThingSpeak successfully!");
    } else {
      Serial.println("Failed to send data to ThingSpeak");
    }
  }
  
  // Reconnect WiFi if disconnected
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected. Reconnecting...");
    WiFi.reconnect();
    delay(5000);
  }
  
  delay(100);
}
```

## How Data Flows Through Farmzy

### 1. ESP32 to ThingSpeak
- ESP32 reads sensors every 60 seconds
- Sends data to ThingSpeak via HTTP GET to `/update`
- ThingSpeak stores the data and makes it available via API

### 2. ThingSpeak to Farmzy Backend
The backend (`app/soilytics/thingspeak.py`) fetches data:
```python
# ThingSpeakClient.fetch_latest_reading() maps:
# field1 -> moisture, field2 -> pH
# field3 -> nitrogen, field4 -> phosphorus, field5 -> potassium
```

Backend endpoint: `POST /api/soil/fetch-thingspeak`
- Fetches latest data from ThingSpeak
- Runs through SoilIntelligenceEngine for analysis
- Stores results in database

### 3. ThingSpeak to Farmzy Frontend (Direct)
The frontend can also fetch directly from ThingSpeak API:
```
GET https://api.thingspeak.com/channels/{CHANNEL_ID}/feeds.json?api_key={API_KEY}&results=100
```
This is used for real-time charts on the Soil Analytics page.

### 4. Soil Analysis Pipeline
```
Raw Reading -> SoilIntelligenceEngine.analyze_soil_reading()
  -> Classify nutrients (N, P, K) against thresholds
  -> Classify pH and moisture
  -> Calculate soil_score (0-100)
  -> Calculate degradation_index (SDI)
  -> Generate recommendations
```

### 5. Irrigation Decision
```
Soil Data + Weather -> HydroIQEngine.compute_irrigation_decision()
  -> Calculate ET0 (Hargreaves method)
  -> Calculate crop water requirement
  -> Check soil moisture vs trigger threshold
  -> Decide irrigate/not
  -> Distribute across zones
```

## Extending the Algorithm

### Adding New Sensors

To add a new sensor (e.g., light, temperature):

1. **ThingSpeak**: Add field6, field7, etc. to your channel
2. **ESP32**: Add sensor reading function and include in `sendToThingSpeak()`
3. **Backend** (`app/soilytics/thingspeak.py`): Update `_parse_feed()` to map new fields
4. **Backend** (`app/soilytics/models.py`): Add new fields to `SoilReading`
5. **Frontend**: Update `lib/thingspeak.ts` `parseFeed()` function

### Improving Soil Score Algorithm

The soil score in `app/soilytics/engine.py` uses penalty-based scoring:
```python
score = 100 - (nitrogen_penalty + phosphorus_penalty + potassium_penalty + ph_penalty + moisture_penalty)
```

To improve:
- Add machine learning model trained on your farm's historical data
- Include weather data correlation
- Add temporal patterns (seasonal adjustments)
- Weight penalties based on crop-specific requirements

### Adding Irrigation Control (ESP32 Actuator)

To make the ESP32 also control irrigation valves:

```cpp
// Add to ESP32 code
const int VALVE_PIN = 25;  // Relay control for solenoid valve

void checkIrrigationDecision() {
  HTTPClient http;
  // Fetch decision from Farmzy backend
  http.begin("http://YOUR_BACKEND_URL/api/irrigation/compute");
  http.addHeader("Content-Type", "application/json");
  int httpCode = http.POST("{\"farm_id\":\"FARM_PNL_01\"}");
  
  if (httpCode == 200) {
    String response = http.getString();
    // Parse JSON response - check "irrigate" field
    if (response.indexOf("\"irrigate\": true") >= 0) {
      digitalWrite(VALVE_PIN, HIGH);  // Open valve
      Serial.println("Irrigation ON");
    } else {
      digitalWrite(VALVE_PIN, LOW);   // Close valve
      Serial.println("Irrigation OFF");
    }
  }
  http.end();
}
```

## Setup Checklist

1. **Create ThingSpeak Account** at https://thingspeak.com
2. **Create Channel** with 5 fields (moisture, pH, N, P, K)
3. **Note your Channel ID** and **Write API Key** (for ESP32) and **Read API Key** (for Farmzy)
4. **Flash ESP32** with the code above (update WiFi credentials and API key)
5. **Configure Farmzy Backend** (`.env`):
   ```
   THINGSPEAK_API_KEY=your-write-api-key
   THINGSPEAK_CHANNEL_ID=your-channel-id
   THINGSPEAK_READ_API_KEY=your-read-api-key
   ```
6. **Configure Farmzy Frontend** (`.env`):
   ```
   VITE_THINGSPEAK_CHANNEL_ID=your-channel-id
   VITE_THINGSPEAK_API_KEY=your-read-api-key
   ```
7. **Test**: Power on ESP32, wait 60 seconds, check ThingSpeak channel for data, then check Farmzy dashboard

## Troubleshooting

- **No data on ThingSpeak**: Check WiFi connection, verify Write API key, ensure 15s minimum between updates (free tier)
- **Incorrect readings**: Calibrate sensors - use known pH solutions for pH sensor, weigh soil samples for moisture baseline
- **RS485 NPK not responding**: Check wiring (TX/RX not swapped), verify baud rate matches sensor, check DE/RE pin timing
- **Frontend shows no data**: Verify Channel ID and Read API Key in settings, check browser console for CORS errors
