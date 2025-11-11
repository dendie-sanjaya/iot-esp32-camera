import cv2
import numpy as np
import requests
from flask import Flask, request, jsonify
# Import modul tambahan untuk manajemen file dan nama unik
import os
import uuid 
import time 

app = Flask(__name__)

# --- Konfigurasi Penyimpanan File ---
INVESTIGATION_FOLDER = "foto-investigation"
# Membuat folder jika belum ada (exist_ok=True mencegah error jika folder sudah ada)
os.makedirs(INVESTIGATION_FOLDER, exist_ok=True) 
# -----------------------------------

# --- Inisialisasi Model HOG (Hanya sekali saat server dimulai) ---
# Initialization of the HOG model for human detection.
hog = cv2.HOGDescriptor()
# Setting the default SVM detector for pedestrian detection.
hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())

# PARAMETER HOG YANG DI-TUNE (HitThreshold disetel negatif untuk sensitivitas tinggi)
HOG_PARAMS = {
    'winStride': (4, 4),
    'padding': (8, 8),
    'scale': 1.05,
    'hitThreshold': -0.2 # Nilai negatif meningkatkan sensitivitas detektor
}
# ------------------------------------------------------------------

def analyze_human_detection(image_data):
    """
    Menganalisis data gambar (sebagai array numpy) untuk mendeteksi manusia.
    
    Mengembalikan:
        bool: True jika manusia terdeteksi, False jika tidak.
        list: Daftar objek yang berisi koordinat bounding box dan skor keyakinan.
    """
    try:
        # Lakukan deteksi manusia
        locations, weights = hog.detectMultiScale(image_data, **HOG_PARAMS)
        
        is_human_detected = len(locations) > 0
        
        # Format hasil menjadi list of objects (box dan confidence)
        results = []
        for i, box in enumerate(locations):
            results.append({
                # Box format: [x, y, w, h]
                "box": list(map(int, box)),
                "confidence": float(weights[i])
            })
        
        return is_human_detected, results
    
    except Exception as e:
        print(f"Error during HOG analysis: {e}")
        return False, []

# ==================================================================
# FUNGSI BANTU: SIMPAN GAMBAR KE DISK
# ==================================================================
def save_investigation_image(image_bytes, detected):
    """
    Menyimpan byte gambar ke disk dengan nama unik.
    Jika deteksi berhasil, tambahkan prefix 'DETECTED_'.
    
    Mengembalikan: filepath unik (string).
    """
    # Menghasilkan nama file unik (gabungan timestamp dan UUID)
    unique_id = uuid.uuid4().hex
    prefix = "DETECTED_" if detected else ""
    # Format nama file: [PREFIX]YYYYMMDDHHMMSS_[UUID].jpg
    filename = f"{prefix}{time.strftime('%Y%m%d%H%M%S')}_{unique_id}.jpg"
    filepath = os.path.join(INVESTIGATION_FOLDER, filename)
    
    try:
        # Simpan byte gambar ke file
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        print(f"File disimpan: {filepath}")
        return filepath
    except Exception as e:
        print(f"Gagal menyimpan file: {e}")
        return None

# ==================================================================
# ENDPOINT 0: HEALTH CHECK 🩺
# ==================================================================
@app.route('/health', methods=['GET'])
def health_check():
    """Endpoint sederhana untuk memeriksa apakah server Flask berjalan dan model HOG terinisialisasi."""
    try:
        if hog is None:
            raise Exception("HOG object failed to initialize.")
        
        return jsonify({
            "status": "UP",
            "service": "Human Detection API (OpenCV)",
            "model_status": "Ready",
            "storage_folder": os.path.abspath(INVESTIGATION_FOLDER),
            "timestamp": time.time()
        }), 200
    except Exception as e:
        return jsonify({
            "status": "DOWN",
            "service": "Human Detection API (OpenCV)",
            "model_status": f"Initialization Error: {str(e)}",
            "timestamp": time.time()
        }), 503 


# ==================================================================
# ENDPOINT 1: Menerima file foto yang diunggah
# ==================================================================
@app.route('/detect/upload', methods=['POST'])
def detect_from_upload():
    """Menerima file gambar yang diunggah (multipart/form-data)."""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "No selected file"}), 400

    if file:
        image_stream = file.read()
        
        # Konversi array byte ke array numpy untuk deteksi
        nparr = np.frombuffer(image_stream, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img_np is None:
            return jsonify({"status": "error", "message": "Could not decode image"}), 400

        # Lakukan analisis deteksi
        detected, results = analyze_human_detection(img_np)
        person_count = len(results)
        
        # --- Simpan File ke Disk ---
        filepath = save_investigation_image(image_stream, detected)
        # --------------------------

        if detected:
            print(f"!!! HUMAN DETECTED: Notifikasi dikirim! Jumlah Orang: {person_count}")
            
            return jsonify({
                "status": "success",
                "human_detected": detected,
                "message": f"Human detected. Total {person_count} person(s) found.",
                "person_count": person_count,
                "detections": results,
                "filepath_attachment": filepath # Tambahkan path file
            })
        else:
            return jsonify({
                "status": "success",
                "human_detected": detected,
                "message": "No human detected.",
                "person_count": 0,
                "filepath_attachment": filepath # Tambahkan path file
            })


# ==================================================================
# ENDPOINT 2: Menerima URL API untuk mengambil foto (untuk listener.py)
# ==================================================================
@app.route('/detect/url', methods=['POST'])
def detect_from_url():
    """Menerima URL gambar dari payload JSON."""
    data = request.get_json()
    image_url = data.get('image_url')

    if not image_url:
        return jsonify({"status": "error", "message": "Missing 'image_url' in request body"}), 400

    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status() 
        
        image_bytes = response.content # Byte gambar yang diambil
        
        nparr = np.frombuffer(image_bytes, np.uint8)
        img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img_np is None:
            return jsonify({"status": "error", "message": "Could not decode image from URL"}), 400

        # Lakukan analisis deteksi
        detected, results = analyze_human_detection(img_np)
        person_count = len(results)
        
        # --- Simpan File ke Disk ---
        filepath = save_investigation_image(image_bytes, detected)
        # --------------------------
        
        if detected:
            print(f"!!! HUMAN DETECTED (via URL): Notifikasi dikirim! Jumlah Orang: {person_count}")
            
            return jsonify({
                "status": "success",
                "human_detected": detected,
                "message": f"Human detected. Total {person_count} person(s) found.",
                "person_count": person_count,
                "detections": results,
                "filepath_attachment": filepath # Tambahkan path file
            })
        else:
            return jsonify({
                "status": "success",
                "human_detected": detected,
                "message": "No human detected.",
                "person_count": 0,
                "filepath_attachment": filepath # Tambahkan path file
            })

    except requests.exceptions.RequestException as e:
        return jsonify({"status": "error", "message": f"Failed to fetch image from URL: {e}"}), 500
    except Exception as e:
        print(f"Internal processing error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == '__main__':
    # Jalankan server Flask
    app.run(host='0.0.0.0', port=5000)