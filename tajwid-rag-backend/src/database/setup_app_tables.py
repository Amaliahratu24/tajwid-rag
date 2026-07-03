"""
Membuat 6 tabel aplikasi (ERD) untuk sistem Tajwid RAG:
users, sessions, questions, retrieved_docs, answers, feedback

Tabel ini terpisah dari tabel KONTEN (ayat, hukum_tajwid) yang sudah
dibuat oleh setup_database.py. Tabel di sini untuk MENCATAT aktivitas
pengguna, bukan menyimpan isi tajwid.

Jalankan setelah setup_database.py:
    python src/database/setup_app_tables.py
"""
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "port": int(os.getenv("DB_PORT", 4306)),
}
DB_NAME = os.getenv("DB_NAME", "tajwid_rag")


def create_app_tables():
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(f"USE {DB_NAME}")

    # 1. users — siapa yang pakai sistem (anonim/nama saja, tidak perlu login penuh)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nama VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    # 2. sessions — satu sesi percakapan (bisa banyak pertanyaan per sesi)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    # 3. questions — pertanyaan yang diketik user
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            pertanyaan TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    # 4. retrieved_docs — dokumen/konteks apa saja yang diambil retriever untuk 1 pertanyaan
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS retrieved_docs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question_id INT NOT NULL,
            hukum_tajwid_id INT,
            similarity_score FLOAT,
            urutan INT,
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
            FOREIGN KEY (hukum_tajwid_id) REFERENCES hukum_tajwid(id) ON DELETE SET NULL
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    # 5. answers — jawaban LLM + hasil strict grounding check
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INT AUTO_INCREMENT PRIMARY KEY,
            question_id INT NOT NULL,
            jawaban TEXT NOT NULL,
            model_llm VARCHAR(100),
            is_grounded BOOLEAN,
            grounding_score FLOAT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    # 6. feedback — rating bintang dari user (task Fitri di HARI 4, tapi tabelnya di sini)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INT AUTO_INCREMENT PRIMARY KEY,
            answer_id INT NOT NULL,
            rating INT CHECK (rating BETWEEN 1 AND 5),
            komentar TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (answer_id) REFERENCES answers(id) ON DELETE CASCADE
        ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
    """)

    conn.commit()
    print("6 tabel aplikasi (users, sessions, questions, retrieved_docs, answers, feedback) berhasil dibuat.")
    cursor.close()
    conn.close()


if __name__ == "__main__":
    create_app_tables()