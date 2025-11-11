// Mengatur koneksi WiFi dan MQTT untuk ESP8266
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// =======================================================
// --- KONFIGURASI PENGGUNA (HARUS DIUBAH) ---
// =======================================================

// Konfigurasi WiFi
const char* ssid = "NAMA_WIFI_ANDA";     // Ganti dengan nama WiFi Anda
const char* password = "PASSWORD_ANDA";  // Ganti dengan password WiFi Anda

// Konfigurasi MQTT
const char* mqtt_server = "192.168.1.10"; // Ganti dengan IP Address tempat Anda menjalankan app.py (localhost dari sudut pandang PC Anda, tapi ESP8266 butuh IP spesifik)
const int mqtt_port = 1883;
const char* mqtt_client_id = "ESP8266-Motion-Sensor"; 
const char* mqtt_topic_publish = "sensor/motion"; 

// Konfigurasi Sensor PIR
const int PIR_PIN = D1;  // Menggunakan pin D2 pada NodeMCU/ESP8266

// Payload JSON yang akan dikirim

const char* MOTION_PAYLOAD = "{\"status_motion\": 1,\"sensor_id\": 1}";
const char* NO_MOTION_PAYLOAD = "{\"status_motion\": 0,\"sensor_id\": 1}";

// =======================================================
// --- INISIALISASI OBJEK ---
// =======================================================

WiFiClient espClient;
PubSubClient client(espClient);

// Variabel status
int motionState = LOW; // Status awal sensor gerak
long lastMsg = 0;      // Timestamp terakhir pesan dikirim
int debounceDelay = 5000; // Debounce 5 detik agar tidak spam MQTT

// =======================================================
// --- FUNGSI WIFI DAN MQTT ---
// =======================================================

void setup_wifi() {
  delay(10);
  Serial.println();
  Serial.print("Menghubungkan ke ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("");
  Serial.println("WiFi Terhubung");
  Serial.print("Alamat IP: ");
  Serial.println(WiFi.localIP());
}

void reconnect() {
  // Loop sampai terhubung kembali
  while (!client.connected()) {
    Serial.print("Mencoba koneksi MQTT...");
    // Mencoba terhubung
    if (client.connect(mqtt_client_id)) {
      Serial.println("terhubung!");
    } else {
      Serial.print("gagal, rc=");
      Serial.print(client.state());
      Serial.println(" Coba lagi dalam 5 detik");
      // Tunggu 5 detik sebelum mencoba lagi
      delay(5000);
    }
  }
}

// =======================================================
// --- SETUP DAN LOOP UTAMA ---
// =======================================================

void setup() {
  Serial.begin(115200);

  // Setup pin sensor gerak (Input)
  pinMode(PIR_PIN, INPUT); 

  // Setup koneksi WiFi
  setup_wifi();

  // Setup koneksi MQTT
  client.setServer(mqtt_server, mqtt_port);
  // Di sini kita tidak perlu callback, karena ESP8266 hanya bertugas PUBLISH
}

void loop() {
  // Pastikan koneksi MQTT terjaga
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  long now = millis();
  
  // Baca status sensor PIR
  int currentState = digitalRead(PIR_PIN);

  // --- LOGIKA DETEKSI DAN DEBOUNCE ---
  if (currentState != motionState) {
    // Perubahan status terdeteksi
    
    if (currentState == HIGH) {
      // Gerakan Terdeteksi (Status: 1)
      if (now - lastMsg > debounceDelay) {
        Serial.println(">>> GERAKAN TERDETEKSI! Mengirim payload MQTT...");
        client.publish(mqtt_topic_publish, MOTION_PAYLOAD); // Mengirim {"status_motion": 1}
        lastMsg = now; // Reset timer debounce
      }
    } else {
      // Gerakan Berakhir (Status: 0 - Opsional, tidak terlalu penting untuk deteksi)
      // Di-comment karena kita hanya ingin notifikasi saat ada gerakan baru.
      /*
      if (now - lastMsg > debounceDelay) {
        Serial.println("Gerakan Berakhir. Mengirim payload MQTT...");
        client.publish(mqtt_topic_publish, NO_MOTION_PAYLOAD); // Mengirim {"status_motion": 0}
        lastMsg = now;
      }
      */
    }
    
    // Perbarui status gerak 
    motionState = currentState; 
  }

  delay(100); // Penundaan kecil untuk stabilitas
}