# database_setup.py

import sqlite3
import time
import os

DATABASE_NAME = "detection_history.db"

def get_db_connection():
    """Membuat dan mengembalikan koneksi database."""
    # Akan membuat file DB jika belum ada
    conn = sqlite3.connect(DATABASE_NAME)
    conn.row_factory = sqlite3.Row 
    return conn

def initialize_database():
    """
    Membuat tabel 'history' dan 'status_lamp' jika belum ada, 
    dan menyisipkan sample data untuk keduanya.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"Menginisialisasi database: {DATABASE_NAME}")

    # 1. Membuat tabel history
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT NOT NULL,
            capture_image TEXT NOT NULL,
            detection_status TEXT NOT NULL,
            person_count INTEGER
        );
    """)
    print("Tabel 'history' diperiksa/dibuat.")

    # 2. Membuat tabel status_lamp (Baru ditambahkan)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS status_lamp (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datetime TEXT NOT NULL,
            status TEXT NOT NULL 
        );
    """)
    print("Tabel 'status_lamp' diperiksa/dibuat.")

    # --- INISIALISASI DATA HISTORY ---
    cursor.execute("SELECT COUNT(*) FROM history")
    if cursor.fetchone()[0] == 0:
        print("Menyisipkan 3 sample data ke tabel 'history'...")
        # Sample data history
        sample_data_history = [
            ("2025-11-12 10:00:00", "DETECTED_20251112100000_sample1.jpg", "Detected", 1),
            ("2025-11-12 10:10:45", "DETECTED_20251112101045_sample3.jpg", "Detected", 2),
        ]
        cursor.executemany(
            "INSERT INTO history (datetime, capture_image, detection_status, person_count) VALUES (?, ?, ?, ?)",
            sample_data_history
        )
        print("✅ 3 sample data history berhasil disisipkan.")
    else:
        print("Tabel 'history' sudah berisi data. Sample data dilewati.")

    # --- INISIALISASI DATA STATUS LAMP ---
    cursor.execute("SELECT COUNT(*) FROM status_lamp")
    if cursor.fetchone()[0] == 0:
        print("Menyisipkan sample data ke tabel 'status_lamp'...")
        # Sample data status_lamp (Memberikan status awal ON)
        current_time = time.strftime('%Y-%m-%d %H:%M:%S')
        sample_data_lamp = [
            (current_time, "on"),
        ]
        cursor.executemany(
            "INSERT INTO status_lamp (datetime, status) VALUES (?, ?)",
            sample_data_lamp
        )
        print(f"✅ Sample data status_lamp berhasil disisipkan (Status awal: on, Waktu: {current_time}).")
    else:
        print("Tabel 'status_lamp' sudah berisi data. Sample data dilewati.")


    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_database()