import cv2
import numpy as np
import requests
from flask import Flask, request, jsonify, send_from_directory
# IMPORT BARU: Menggunakan datetime dari modul datetime
from datetime import datetime
from flask_cors import CORS 
import os
import uuid 
import time 
import paho.mqtt.client as mqtt
import json
import socket 
# Asumsi file database_setup.py ada di direktori yang sama
from database_setup import get_db_connection 

app = Flask(__name__)
# ==================================================================
# PENTING: MENGAKTIFKAN CORS
# ==================================================================
CORS(app) 

# --- Konfigurasi ---
INVESTIGATION_FOLDER = "/mnt/d/xampp-8.1/htdocs/sensor-motion/foto-investigation/"
MQTT_BROKER = "127.0.0.1" 
MQTT_PORT = 1883
MQTT_TIMEOUT = 60
# -------------------

# Membuat folder untuk penyimpanan gambar jika belum ada
os.makedirs(INVESTIGATION_FOLDER, exist_ok=True) 

# --- FUNGSI BANTU DATABASE ---

def insert_history(filepath, detected, person_count):
    """Menyisipkan catatan deteksi baru ke tabel 'history'."""
    try:
        conn = get_db_connection()
        conn.execute(
            "INSERT INTO history (datetime, capture_image, detection_status, person_count) VALUES (?, ?, ?, ?)",
            (
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                os.path.basename(filepath), # Hanya menyimpan nama file
                "Detected" if detected else "Not Detected",
                person_count
            )
        )
        conn.commit()
        conn.close()
        print(f"✅ Data history disimpan: Status={detected}, Count={person_count}, File={os.path.basename(filepath)}")
    except Exception as e:
        print(f"❌ Gagal menyisipkan data history: {e}")


def update_lamp_status_db(new_status):
    """Memperbarui status lampu terakhir di tabel 'status_lamp'."""
    try:
        conn = get_db_connection()
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Menyisipkan entri baru (atau Anda bisa menggunakan REPLACE/UPDATE jika desain tabel Anda mengizinkan)
        conn.execute(
            "INSERT INTO status_lamp (datetime, status) VALUES (?, ?)",
            (current_time, new_status)
        )
        conn.commit()
        conn.close()
        print(f"✅ Status lampu di DB diperbarui menjadi: {new_status}")
        return True
    except Exception as e:
        print(f"❌ Gagal memperbarui status lampu di DB: {e}")
        return False
    
# --- FUNGSI BANTU MQTT ---

mqtt_client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    """Callback saat koneksi ke broker MQTT berhasil."""
    if rc == 0:
        print(f"✅ Terhubung ke MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
        client._is_connected = True 
    else:
        print(f"❌ Gagal terhubung ke MQTT Broker, kode kembali: {rc}")
        client._is_connected = False

def on_disconnect(client, userdata, rc):
    """Callback saat koneksi ke broker MQTT terputus."""
    client._is_connected = False
    if rc != 0:
        print("MQTT client disconnect with unexpected code. Trying to reconnect...")
        
mqtt_client.on_connect = on_connect
mqtt_client.on_disconnect = on_disconnect
mqtt_client._is_connected = False 

def publish_to_mqtt(topic, payload):
    """Fungsi untuk mempublikasikan payload ke topik MQTT."""
    if not mqtt_client._is_connected:
        return False, "MQTT client is not connected to the broker."
          
    try:
        result = mqtt_client.publish(topic, payload, qos=1)
        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"✅ Berhasil mempublikasikan ke topik '{topic}': '{payload}'")
            return True, None
        else:
            error_message = f"Gagal mempublikasikan ke MQTT, kode: {result.rc}"
            print(f"❌ {error_message}")
            return False, error_message
    except Exception as e:
        error_message = f"Error saat publish MQTT: {e}"
        print(f"❌ {error_message}")
        return False, error_message


try:
    # Coba hubungkan ke broker
    mqtt_client.connect(MQTT_BROKER, MQTT_PORT, MQTT_TIMEOUT)
    mqtt_client.loop_start() 
except Exception as e:
    print(f"❌ Gagal menghubungkan ke MQTT saat inisialisasi: {e}")

# --- INISIALISASI HOG (CV2) ---
hog = cv2.HOGDescriptor()
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

HOG_PARAMS = {
    'winStride': (4, 4),
    'padding': (8, 8),
    'scale': 1.05,
    'hitThreshold': -0.2
}

def analyze_human_detection(image_data):
    """Menganalisis data gambar untuk mendeteksi manusia."""
    try:
        # HOG membutuhkan gambar grayscale, ubah jika gambar berwarna (IMREAD_COLOR)
        gray = cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
        locations, weights = hog.detectMultiScale(gray, **HOG_PARAMS)
        is_human_detected = len(locations) > 0
        
        results = []
        for i, box in enumerate(locations):
            results.append({
                "box": list(map(int, box)),
                "confidence": float(weights[i])
            })
        return is_human_detected, results
    except Exception as e:
        print(f"Error during HOG analysis: {e}")
        return False, []

def save_investigation_image(image_bytes, detected):
    """Menyimpan byte gambar ke disk dengan nama unik."""
    unique_id = uuid.uuid4().hex[:6] # Ambil 6 karakter pertama
    prefix = "DETECTED_" if detected else ""
    # Menggunakan datetime dari modul datetime
    filename = f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S')}_{unique_id}.jpg"
    filepath = os.path.join(INVESTIGATION_FOLDER, filename)
    
    try:
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        return filepath
    except Exception as e:
        print(f"Gagal menyimpan file: {e}")
        return None

# ==================================================================
# ENDPOINT PUBLIC (FOTO INVESTIGASI) 🖼️
# ==================================================================
@app.route('/foto-investigation/<filename>')
def get_investigation_image(filename):
    """Menyajikan file gambar dari folder INVESTIGATION_FOLDER."""
    return send_from_directory(INVESTIGATION_FOLDER, filename)


# ==================================================================
# ENDPOINT HEALTH CHECK 🩺
# ==================================================================
@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint untuk memeriksa status aplikasi, model HOG, dan koneksi MQTT."""
    
    # 1. Periksa Status Model HOG/CV2
    model_status = "Ready" if hog is not None else "Failed"
    
    # 2. Periksa Status Koneksi MQTT
    mqtt_connected = mqtt_client._is_connected
    
    # 3. Cek Status Database (Percobaan koneksi singkat)
    db_status = "OK"
    try:
        conn = get_db_connection()
        conn.close()
    except Exception as e:
        db_status = f"Failed ({str(e)})"
        
    overall_status = "UP"
    if model_status == "Failed" or not mqtt_connected or db_status != "OK":
        overall_status = "DOWN"
        
    return jsonify({
        "status": overall_status,
        "service": "Human Detection API (Flask)",
        "components": {
            "model_hog": model_status,
            "mqtt_broker": "Connected" if mqtt_connected else "Disconnected",
            "sqlite_db": db_status
        },
        "timestamp": time.time()
    }), 200 if overall_status == "UP" else 503

# ------------------------------------------------------------------

# ==================================================================
# ENDPOINT 1: MENGAMBIL DATA DARI DATABASE (HISTORY) 📊
# ==================================================================
@app.route('/history', methods=['GET'])
def get_history():
    """Mengambil semua data dari tabel 'history'."""
    try:
        conn = get_db_connection()
        # Mengambil kolom capture_image
        history = conn.execute(
            "SELECT id, datetime, capture_image, detection_status, person_count FROM history ORDER BY datetime DESC"
        ).fetchall()
        conn.close()
        
        history_list = [dict(row) for row in history]
        
        return jsonify({
            "status": "success",
            "count": len(history_list),
            "data": history_list
        }), 200
        
    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal mengambil data history: {str(e)}"}), 500

# ==================================================================
# ENDPOINT 2: PUBLISH CUSTOM KE MQTT 🚀 (TIDAK DIHAPUS)
# ==================================================================
@app.route('/mqtt/publish', methods=['POST'])
def publish_custom_mqtt():
    """Menerima parameter target topik dan value topik untuk dipublikasikan."""
    data = request.get_json()
    target_topic = data.get('target_topic')
    topic_value = data.get('topic_value')

    if not target_topic or topic_value is None:
        return jsonify({
            "status": "error", 
            "message": "Missing 'target_topic' or 'topic_value' in request body."
        }), 400

    # Payload diubah menjadi string sebelum dikirim ke fungsi publish_to_mqtt
    success, error = publish_to_mqtt(target_topic, str(topic_value))
    
    if success:
        return jsonify({
            "status": "success", 
            "message": "Pesan MQTT berhasil dipublikasikan.",
            "topic": target_topic,
            "payload": str(topic_value)
        }), 200
    else:
        return jsonify({
            "status": "error", 
            "message": error,
            "topic": target_topic,
            "payload": str(topic_value)
        }), 500


# ==================================================================
# ENDPOINT STATUS LAMPU
# ==================================================================
@app.route('/status/lamp', methods=['GET'])
def get_lamp_status():
    """Mengambil status terakhir lampu dari tabel status_lamp."""
    try:
        conn = get_db_connection()
        status_row = conn.execute(
            "SELECT status, datetime FROM status_lamp ORDER BY datetime DESC LIMIT 1"
        ).fetchone()
        conn.close()

        if status_row:
            return jsonify({
                "status": "success",
                "lamp_status": status_row['status'],
                "last_updated": status_row['datetime']
            }), 200
        else:
            return jsonify({
                "status": "success",
                "lamp_status": "UNKNOWN",
                "message": "Status lamp belum tersedia."
            }), 200
            
    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal mengambil status lampu: {str(e)}"}), 500


# ==================================================================
# ENDPOINT 3: MEMATIKAN LAMPU VIA MQTT 💡
# ==================================================================
@app.route('/control/turn_off_lamp', methods=['POST'])
def turn_off_lamp():
    """Mengirim pesan JSON {"status": "off"} ke topik 'lamp' dan memperbarui status DB."""
    
    LAMP_TOPIC = "lamp" 
    PAYLOAD_DICT = {"status": "off"} 
    PAYLOAD_JSON = json.dumps(PAYLOAD_DICT) 

    success, error = publish_to_mqtt(LAMP_TOPIC, PAYLOAD_JSON)
    
    if success:
        new_db_status = PAYLOAD_DICT["status"].lower() 
        update_success = update_lamp_status_db(new_db_status)

        response_message = "Perintah 'Turn Off Lamp' berhasil dikirim via MQTT."
        if not update_success:
             response_message += " Namun, gagal memperbarui status di database."

        return jsonify({
            "status": "success", 
            "message": response_message,
            "topic": LAMP_TOPIC,
            "command_payload": PAYLOAD_JSON
        }), 200
    else:
        return jsonify({
            "status": "error", 
            "message": error,
            "topic": LAMP_TOPIC,
            "command_payload": PAYLOAD_JSON
        }), 500


# ==================================================================
# ENDPOINT /detect/upload 🖼️
# ==================================================================
@app.route('/detect/upload', methods=['POST'])
def detect_from_upload():
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400

    if file:
        image_stream = file.read()
        nparr = np.frombuffer(image_stream, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img_np is None:
            return jsonify({"status": "error", "message": "Could not decode image"}), 400

        detected, results = analyze_human_detection(img_np)
        person_count = len(results)
        
        filepath = save_investigation_image(image_stream, detected)
        
        # Kirim perintah ON jika terdeteksi
        if detected:
            LAMP_TOPIC = "lamp" 
            PAYLOAD_DICT_ON = {"status": "on"} 
            PAYLOAD_JSON_ON = json.dumps(PAYLOAD_DICT_ON) 
            
            publish_success, error_msg = publish_to_mqtt(LAMP_TOPIC, PAYLOAD_JSON_ON)
            if publish_success:
                 update_lamp_status_db(PAYLOAD_DICT_ON["status"])
            
            print(f"!!! HUMAN DETECTED: Memicu Lampu ON. Jumlah Orang: {person_count}")
        
        if filepath:
            insert_history(filepath, detected, person_count)


        response_data = {
            "status": "success",
            "human_detected": detected,
            "person_count": person_count,
            "detections": results,
            "image_filename": os.path.basename(filepath) if filepath else None
        }
        
        if detected:
            response_data["message"] = f"Human detected. Total {person_count} person(s) found."
        else:
            response_data["message"] = "No human detected."
            
        return jsonify(response_data)
        
# ==================================================================
# ENDPOINT /detect/url (FINAL INTEGRATION) 🖼️
# ==================================================================
@app.route('/detect/url', methods=['POST'])
def detect_from_url():
    """
    Menerima URL gambar, mengunduh, menganalisis HOG,
    menyimpan hasil ke history, dan mengontrol lampu ON jika terdeteksi.
    """
    LAMP_TOPIC = "lamp" 
    PAYLOAD_DICT_ON = {"status": "on"} 
    PAYLOAD_JSON_ON = json.dumps(PAYLOAD_DICT_ON) 
    
    data = request.get_json()
    image_url = data.get('image_url')

    if not image_url:
        return jsonify({
            "status": "error",
            "message": "Parameter 'image_url' hilang dari request body."
        }), 400

    print(f"\n-> Menganalisis URL: {image_url}")

    # 1. Coba ambil dan unduh gambar dari URL
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        image_bytes = response.content
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Gagal mengambil gambar dari URL ({image_url}): {e}")
        return jsonify({
            "status": "error",
            "message": f"Gagal koneksi/mengunduh gambar dari server ({image_url}). Error: {type(e).__name__}"
        }), 503

    # 2. Proses dan Analisis HOG
    try:
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_np is None:
            raise ValueError("Could not decode image from URL bytes")

        detected, results = analyze_human_detection(img_np)
        person_count = len(results)

    except Exception as e:
        print(f"❌ Error saat analisis HOG atau decoding: {e}")
        # Tetap lanjutkan untuk menyimpan gambar (jika ada) meskipun analisis gagal
        detected, person_count = False, 0 

    # 3. Simpan Gambar Investigasi ke Disk
    filepath = save_investigation_image(image_bytes, detected)
    
    # 4. Simpan Hasil Deteksi ke History DB
    if filepath:
        insert_history(filepath, detected, person_count)

    # 5. Kontrol Lampu via MQTT jika terdeteksi
    mqtt_message = "No lamp command sent."
    if detected:
        print(f"!!! HUMAN DETECTED: Memicu Lampu ON. Jumlah Orang: {person_count}")
        success, error_msg = publish_to_mqtt(LAMP_TOPIC, PAYLOAD_JSON_ON)
        
        if success:
            # Perbarui status lampu di DB ke 'on'
            update_lamp_status_db(PAYLOAD_DICT_ON["status"])
            mqtt_message = "Lamp ON command successfully sent."
        else:
            print(f"❌ Gagal mengirim perintah MQTT ON: {error_msg}")
            mqtt_message = f"Lamp ON command failed to send: {error_msg}"
            
        message = f"Human detected. Total {person_count} person(s) found. {mqtt_message}"
    else:
        message = "No human detected."


    # 6. Response
    return jsonify({
        "status": "success",
        "human_detected": detected,
        "message": message,
        "person_count": person_count,
        "detections": results if 'results' in locals() else [],
        "image_filename": os.path.basename(filepath) if filepath else None,
        "mqtt_status": mqtt_message
    }), 200


# ==================================================================
# MAIN PROGRAM
# ==================================================================
if __name__ == '__main__':
    try:
        print("Starting Flask application...")
        # Perluas host ke '0.0.0.0' agar dapat diakses dari jaringan luar
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        print("Koneksi MQTT terputus.")