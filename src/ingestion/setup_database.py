import mysql.connector
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Konfigurasi koneksi ke MySQL, dibaca dari file .env (beda-beda tiap laptop)
DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": int(os.getenv("DB_PORT"))
}

def create_database_and_tables():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Buat database
    cursor.execute("CREATE DATABASE IF NOT EXISTS tajwid_rag CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    cursor.execute("USE tajwid_rag")

    # Tabel ayat
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ayat (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ayat_number INT NOT NULL,
            arabic TEXT NOT NULL,
            transliteration TEXT,
            translation_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    # Tabel hukum tajwid
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hukum_tajwid (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ayat_number INT NOT NULL,
            lafaz_arab VARCHAR(255),
            transliterasi VARCHAR(255),
            hukum VARCHAR(100) NOT NULL,
            kategori VARCHAR(100),
            penjelasan TEXT,
            sumber VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    conn.commit()
    print("Database 'tajwid_rag' dan tabel berhasil dibuat.")
    cursor.close()
    conn.close()

def import_ayat_data():
    conn = mysql.connector.connect(**DB_CONFIG, database="tajwid_rag")
    cursor = conn.cursor()

    with open("data/annaba_raw.json", "r", encoding="utf-8") as f:
        ayat_data = json.load(f)

    cursor.execute("DELETE FROM ayat")  # bersihkan dulu kalau ada data lama
    for ayat in ayat_data:
        cursor.execute("""
            INSERT INTO ayat (ayat_number, arabic, transliteration, translation_id)
            VALUES (%s, %s, %s, %s)
        """, (
            ayat["ayat_number"],
            ayat["arabic"],
            ayat.get("transliteration", ""),
            ayat.get("translation_id", "")
        ))

    conn.commit()
    print(f"Berhasil import {len(ayat_data)} ayat ke tabel 'ayat'.")
    cursor.close()
    conn.close()

def import_tajwid_data():
    conn = mysql.connector.connect(**DB_CONFIG, database="tajwid_rag")
    cursor = conn.cursor()

    with open("data/tajwid_annaba.json", "r", encoding="utf-8") as f:
        tajwid_data = json.load(f)

    cursor.execute("DELETE FROM hukum_tajwid")  # bersihkan dulu kalau ada data lama
    for item in tajwid_data:
        cursor.execute("""
            INSERT INTO hukum_tajwid (ayat_number, lafaz_arab, transliterasi, hukum, kategori, penjelasan, sumber)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            item["ayat"],
            item["lafaz_arab"],
            item["transliterasi"],
            item["hukum"],
            item["kategori"],
            item["penjelasan"],
            item["sumber"]
        ))

    conn.commit()
    print(f"Berhasil import {len(tajwid_data)} entri hukum tajwid ke tabel 'hukum_tajwid'.")
    cursor.close()
    conn.close()

def main():
    print("Membuat database dan tabel...")
    create_database_and_tables()
    print("Mengimport data ayat...")
    import_ayat_data()
    print("Mengimport data hukum tajwid...")
    import_tajwid_data()
    print("Semua data berhasil diimport ke MySQL.")

if __name__ == "__main__":
    main()