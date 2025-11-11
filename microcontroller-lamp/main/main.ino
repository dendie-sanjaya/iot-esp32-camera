#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// ===================================
// 1. KONFIGURASI JARINGAN & MQTT
// ===================================

// Kredensial WiFi Anda
const char* ssid = "xxxx";
const char* password = "xxxxxx"; // GANTI dengan PASSWORD ASLI WIFI Anda!

// Konfigurasi MQTT Broker
const char* mqtt_server = "192.168.100.35"; // Pastikan ini adalah IP lokal PC/Server Broker Anda!
const int mqtt_port = 1883;

// Topic yang di-subscribe (HARUS SAMA dengan topik publikasi Express: 'lamp')
const char* inTopic = "lamp";

// ===================================
// 2. KONFIGURASI PERANGKAT KERAS
// ===================================

// PIN KONTROL: D2 (GPIO 4) lebih stabil daripada D1
const int RELAY_PIN = D2; 

// LOGIKA RELAY (SUDAH DIPERBAIKI):
// KAMI MENGUBAHNYA KEMBALI KE ACTIVE-LOW.
// ACTIVE-LOW: LOW (0V) = ON, HIGH (3.3V) = OFF
#define RELAY_ON HIGH
#define RELAY_OFF LOW

/*
// Logika ACTIVE-HIGH (Untuk referensi jika Relay Anda berbeda):
// #define RELAY_ON HIGH  
// #define RELAY_OFF LOW
*/

// ===================================
// OBJEK KLIEN
// ===================================

WiFiClient espClient;
PubSubClient client(espClient);
long lastReconnectAttempt = 0;

// ===================================
// FUNGSI UTILITY
// ===================================

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Menghubungkan ke ");
  Serial.println(ssid);

  // Menggunakan fungsi begin() standar
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("Koneksi WiFi berhasil");
  Serial.print("Alamat IP: ");
  Serial.println(WiFi.localIP());
}

boolean reconnect() {
  // Coba koneksi dengan Client ID unik
  if (client.connect("ESP8266Client-Lamp")) {
    Serial.println("Terhubung ke MQTT Broker");
    
    // Berlangganan ke topik 'lamp'
    client.subscribe(inTopic);
    Serial.print("Berlangganan ke topik: ");
    Serial.println(inTopic);
    return true;
  } else {
    Serial.print("Gagal koneksi MQTT, rc=");
    Serial.print(client.state());
    Serial.println(" Coba lagi dalam 5 detik");
    return false;
  }
}

// ===================================
// FUNGSI CALLBACK (PENERIMA PESAN MQTT)
// ===================================

void callback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Pesan tiba di topik: ");
  Serial.println(topic);

  // Buffer untuk menampung payload JSON
  StaticJsonDocument<200> doc;
  
  // Deserialisasi payload
  DeserializationError error = deserializeJson(doc, payload, length);

  if (error) {
    Serial.print(F("Gagal mem-parsing JSON: "));
    Serial.println(error.f_str());
    return;
  }
  
  // Mengambil nilai "status" dari payload JSON
  const char* status = doc["status"]; 

  if (status) {
    String statusStr = status;
    statusStr.toUpperCase(); // Pastikan pemrosesan dalam huruf besar (ON/OFF)

    if (statusStr == "ON") {
      digitalWrite(RELAY_PIN, RELAY_ON);
      Serial.println("-> PERINTAH: Lampu HIDUP (ON)");
    } else if (statusStr == "OFF") {
      digitalWrite(RELAY_PIN, RELAY_OFF);
      Serial.println("-> PERINTAH: Lampu MATI (OFF)");
    } else {
      Serial.print("Status tidak dikenal: ");
      Serial.println(status);
    }
  }
}

// ===================================
// SETUP
// ===================================

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, RELAY_OFF); // Pin D2 diatur ke HIGH (OFF) saat start
  
  setup_wifi();
  
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(callback);
}

// ===================================
// LOOP UTAMA
// ===================================

void loop() {
  if (!client.connected()) {
    long now = millis();
    if (now - lastReconnectAttempt > 5000) {
      lastReconnectAttempt = now;
      if (reconnect()) {
        lastReconnectAttempt = 0;
      }
    }
  }
  client.loop();
}
