import paho.mqtt.client as mqtt
import requests
import json
import time

# --- Konfigurasi MQTT ---
MQTT_BROKER = "localhost"  # Ganti dengan alamat broker MQTT Anda
MQTT_PORT = 1883
MQTT_TOPIC = "camera/motion/status" # Topik yang mengirim status pergerakan

# --- Konfigurasi API Kamera ---
# GANTI INI: Asumsi bahwa ada endpoint API di kamera yang mengembalikan gambar terbaru
CAMERA_IMAGE_API_URL = "http://192.168.1.100/capture"  # Ganti dengan URL API kamera Anda

# --- Konfigurasi API Flask ---
# app.py Anda memiliki endpoint /detect/url, tapi kita ubah ke /detect/upload 
# agar listener bisa mengirim data gambar langsung, BUKAN URL, untuk efisiensi
# (Namun, jika /detect/url harus digunakan, kita bisa gunakan endpoint itu juga)
FLASK_DETECT_URL = "http://127.0.0.1:5000/detect/upload" 
# Kita akan gunakan endpoint UPLOAD (/detect/upload) agar tidak perlu mengunduh 2 kali.

# --- Fungsi Callback MQTT ---
def on_connect(client, userdata, flags, rc):
    """Callback saat berhasil terhubung ke broker."""
    if rc == 0:
        print("✅ Terhubung ke MQTT Broker.")
        client.subscribe(MQTT_TOPIC)
        print(f"Mendengarkan topik: {MQTT_TOPIC}")
    else:
        print(f"❌ Gagal terhubung, kode hasil: {rc}")

def on_message(client, userdata, msg):
    """Callback saat pesan dari topik yang disubscribe diterima."""
    try:
        payload = msg.payload.decode()
        print(f"\n[MQTT] Pesan Diterima: {payload}")
        
        # Asumsi payload adalah JSON: {"status_motion": 1}
        data = json.loads(payload)
        motion_status = data.get('status_motion')
        
        if motion_status == 1:
            print("   => PERGERAKAN TERDETEKSI. Mengambil foto terbaru dari kamera...")
            
            # Panggil fungsi yang mengambil gambar dan mengirimkannya ke app.py
            capture_and_send_to_detector()
            
        elif motion_status == 0:
            print("   => Status: Tidak ada pergerakan. Abaikan.")
        
        else:
            print("   => Payload tidak valid.")

    except json.JSONDecodeError:
        print(f"   => Gagal decode JSON dari payload: {msg.payload}")
    except Exception as e:
        print(f"   => Error saat memproses pesan: {e}")


# --- Fungsi Pengambilan Gambar dan Panggilan API ---
def capture_and_send_to_detector():
    """Mengambil gambar dari kamera dan mengirimkannya ke app.py."""
    
    # 1. Ambil Gambar dari Kamera
    try:
        # Panggil API kamera untuk mendapatkan gambar (asumsi responsnya adalah raw image data/byte)
        print(f"   -> Mengambil gambar dari: {CAMERA_IMAGE_API_URL}")
        response_cam = requests.get(CAMERA_IMAGE_API_URL, timeout=10)
        response_cam.raise_for_status() # Cek kode status HTTP
        
        # Dapatkan data gambar dalam bentuk byte
        image_bytes = response_cam.content
        
    except requests.exceptions.RequestException as e:
        print(f"   -> ❌ Gagal mengambil gambar dari kamera: {e}")
        return

    # 2. Kirim Gambar ke Endpoint UPLOAD di app.py
    try:
        files = {'file': ('motion_snapshot.jpg', image_bytes, 'image/jpeg')}
        
        print(f"   -> Mengirim gambar ke detector Flask: {FLASK_DETECT_URL}")
        response_flask = requests.post(
            FLASK_DETECT_URL, 
            files=files,
            timeout=30 # Waktu tunggu lebih lama untuk proses deteksi
        )
        
        response_flask.raise_for_status()
        
        # Tampilkan respons dari app.py
        result = response_flask.json()
        print(f"[API] Respon dari app.py: Status={result.get('status')}, Human Detected={result.get('human_detected')}")
        
    except requests.exceptions.RequestException as e:
        print(f"[API] ❌ Gagal menghubungi app.py atau Error HTTP: {e}")
    except Exception as e:
        print(f"[API] ❌ Error tidak terduga: {e}")

# --- Program Utama ---
if __name__ == "__main__":
    client = mqtt.Client(client_id="PythonListener")
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
        
    except ConnectionRefusedError:
        print("Pastikan broker MQTT Anda berjalan dan dapat diakses.")
    except KeyboardInterrupt:
        print("\nProgram dihentikan oleh pengguna.")
    finally:
        client.disconnect()