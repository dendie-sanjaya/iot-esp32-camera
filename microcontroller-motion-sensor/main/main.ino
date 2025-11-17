// Mengatur koneksi WiFi dan MQTT untuk ESP8266
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

// =======================================================
// --- KONFIGURASI PENGGUNA (HARUS DIUBAH) ---
// =======================================================

// Konfigurasi WiFi
const char* ssid = "Mama adelia"; 	 // Ganti dengan nama WiFi Anda
const char* password = "uu311009"; 	// Ganti dengan password WiFi Anda

// Konfigurasi MQTT
// PERHATIAN: Tanda kutip penutup ("") di sini telah diperbaiki.
const char* mqtt_server = "192.168.100.35"; // Ganti dengan IP Address tempat Anda menjalankan broker MQTT (misalnya, komputer Anda)
const int mqtt_port = 1883;
const char* mqtt_client_id = "ESP8266-Motion-Sensor"; 
const char* mqtt_topic_publish = "sensor/motion"; 

// Konfigurasi Sensor PIR
const int PIR_PIN = D1; 	// Menggunakan pin D1 pada NodeMCU/ESP8266

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
long lastMsg = 0; 	 	// Timestamp terakhir pesan dikirim
int debounceDelay = 3000; // Debounce 3 detik (5000 ms). Digunakan untuk mencegah pengiriman berulang dalam waktu singkat.

// =======================================================
// --- FUNGSI WIFI DAN MQTT ---
// =======================================================

void setup_wifi() {
	delay(100);
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
		// Mencoba terhubung dengan client ID yang ditentukan
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
	// Karena ini hanya publisher, kita tidak perlu set callback
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
	// Hanya bertindak jika status sensor saat ini berbeda dari status yang tersimpan (motionState)
	if (currentState != motionState) {
		
		if (currentState == HIGH) {
			// Gerakan Terdeteksi (Transisi dari LOW ke HIGH)
			if (now - lastMsg > debounceDelay) {
				Serial.println(">>> GERAKAN DIMULAI! Mengirim payload MQTT (Status: 1)...");
				// Mengirim {"status_motion": 1}
				client.publish(mqtt_topic_publish, MOTION_PAYLOAD); 
				lastMsg = now; // Reset timer debounce setelah pengiriman
			}
		} else {
			// Gerakan Berakhir (Transisi dari HIGH ke LOW)
			// Status 0 ini penting untuk menunjukkan ruangan kosong kembali.
			if (now - lastMsg > debounceDelay) {
				Serial.println(">>> GERAKAN BERAKHIR. Mengirim payload MQTT (Status: 0)...");
				client.publish(mqtt_topic_publish, NO_MOTION_PAYLOAD); // Mengirim {"status_motion": 0}
				lastMsg = now;
			}
		}
		
		// Perbarui status gerak.
		motionState = currentState; 
	}

	delay(100); // Penundaan kecil untuk stabilitas
}