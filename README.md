# Tajwid RAG — Sistem Tanya Jawab Hukum Tajwid Surah An-Naba'

Sistem RAG (Retrieval-Augmented Generation) untuk menjawab pertanyaan seputar
hukum tajwid dalam Surah An-Naba', dengan **strict grounding check** —
jawaban LLM diverifikasi otomatis supaya tidak mengarang di luar data yang ada.

Sistem ini mendukung **dua pilihan LLM**: Groq (llama-3.3-70b-versatile) dan
Gemini (gemini-2.0-flash), yang bisa dipilih langsung lewat parameter di API.

## 📁 Struktur Proyek

```
tajwid-rag/
├── main.py                      # jalankan sistem lewat CLI (terminal)
├── requirements.txt             # daftar library Python
├── .env                         # konfigurasi 
│
├── data/
│   ├── annaba_raw.json           # 40 ayat An-Naba' (arab, latin, arti)
│   ├── tajwid_annaba.json        # data hukum tajwid tiap ayat
│   └── chromadb/                 # vector database (dibuat otomatis)
│
└── src/
    ├── ingestion/                # menyiapkan data
    │   ├── fetch_data.py
    │   ├── create_tajwid_data.py
    │   ├── build_embeddings.py    # isi ChromaDB
    │   └── setup_database.py      # bikin tabel MySQL (ayat, hukum_tajwid) + isi data
    │
    ├── retrieval/
    │   └── retriever.py           # cari dokumen tajwid relevan (MySQL + ChromaDB)
    │
    ├── generation/
    │   ├── generator.py           # kirim ke LLM Groq, hasilkan jawaban
    │   └── llm_gemini.py          # kirim ke LLM Gemini, hasilkan jawaban (opsi kedua)
    │
    ├── grounding/
    │   └── strict_grounding.py    # verifikasi jawaban benar2 didukung konteks
    │
    ├── database/
    │   └── setup_app_tables.py    # bikin 6 tabel: users, sessions, questions, retrieved_docs, answers, feedback
    │                               
    │
    └── api/
        └── main_api.py            # FastAPI, endpoint untuk frontend
```

## ✅ Prasyarat

Sebelum mulai, pastikan sudah terinstall:
- **Python 3.10+** ([python.org](https://python.org))
- **XAMPP** (Apache + MySQL) — [apachefriends.org](https://www.apachefriends.org)
- **Git** atau **GitHub Desktop**
- Akun **Groq Cloud** untuk API key gratis — [console.groq.com](https://console.groq.com)
- Akun **Google AI Studio** untuk API key Gemini gratis — [aistudio.google.com/api-keys](https://aistudio.google.com/api-keys)

## 🚀 Langkah Instalasi

### 1. Clone repo

```bash
git clone https://github.com/Amaliahratu24/tajwid-rag.git
cd tajwid-rag
```

Atau pakai **GitHub Desktop**: File → Clone Repository → paste URL repo ini.

### 2. Install semua library Python

```bash
pip install -r requirements.txt
```

Proses ini agak lama (beberapa menit) karena ada library besar seperti `torch`
dan `sentence-transformers`. Tunggu sampai selesai tanpa error.

### 3. Buat file `.env`

Buat file `.env` di folder utama repo, lalu isi
dengan konfigurasi **laptop kamu sendiri**:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=tajwid_rag
DB_PORT=3306
GROQ_API_KEY=isi_dengan_api_key_groq_kamu
GEMINI_API_KEY=isi_dengan_api_key_gemini_kamu
```

> ⚠️ **PENTING SOAL PORT MYSQL — WAJIB DIBACA**
>
> Port MySQL XAMPP **berbeda-beda di tiap laptop**. Defaultnya `3306`,
> tapi kalau di laptopmu sudah ada software lain yang bentrok di port itu,
> XAMPP bisa otomatis pindah ke port lain (contoh: penulis README ini
> pakai port **4306**).
>
> **Cara cek port MySQL kamu:**
> 1. Buka **XAMPP Control Panel**
> 2. Klik tombol **Config** di baris MySQL → pilih `my.ini`
> 3. Cari baris `port = ....` di bagian `[mysqld]`
> 4. Sesuaikan angka itu ke `DB_PORT` di file `.env` kamu
>
> Kalau tidak disesuaikan, kamu akan dapat error
> `Can't connect to MySQL server` atau `Access denied for user 'root'`.
> Jangan asumsikan port `3306` otomatis benar — **selalu cek dulu**.

Dapatkan `GROQ_API_KEY` gratis di [console.groq.com](https://console.groq.com)
→ menu **API Keys** → **Create API Key**.

Dapatkan `GEMINI_API_KEY` gratis di [aistudio.google.com](https://aistudio.google.com)
→ klik ikon kunci 🔑 di pojok kiri bawah → **Create API key** → pilih
**Create API key in new project**. Tidak perlu isi data billing/kartu untuk
pemakaian skala kecil (free tier).

### 4. Nyalakan XAMPP

Buka **XAMPP Control Panel**, klik **Start** pada **Apache** dan **MySQL**,
pastikan keduanya berwarna hijau.

### 5. Buat database & isi data konten

```bash
python src/ingestion/setup_database.py
```

Ini membuat database `tajwid_rag` beserta tabel `ayat` dan `hukum_tajwid`,
lalu otomatis mengisi datanya dari file JSON di folder `data/`.

Output yang diharapkan:
```
Database 'tajwid_rag' dan tabel berhasil dibuat.
Berhasil import 40 ayat ke tabel 'ayat'.
Berhasil import ... entri hukum tajwid ke tabel 'hukum_tajwid'.
Semua data berhasil diimport ke MySQL.
```

### 6. Buat 6 tabel aplikasi (log aktivitas pengguna)

```bash
python src/database/setup_app_tables.py
```

Ini membuat tabel `users`, `sessions`, `questions`, `retrieved_docs`,
`answers`, `feedback` — untuk mencatat aktivitas tanya-jawab pengguna.
Kolom `model_llm` di tabel `answers` mencatat model mana (Groq/Gemini)
yang dipakai untuk tiap jawaban.

### 7. Coba lewat CLI (opsional, untuk tes cepat)

```bash
python main.py
```

Ketik pertanyaan **lengkap** (bukan cuma angka nomor), contoh:
```
Sebutkan contoh Mad Thabi'i dalam surah An-Naba
```

### 8. Jalankan API (untuk dipakai frontend)

```bash
uvicorn src.api.main_api:app --reload
```

Biarkan terminal ini tetap terbuka selama server berjalan. Buka
`http://localhost:8000/docs` di browser untuk melihat dan mencoba semua
endpoint yang tersedia secara interaktif.

## 📡 Ringkasan Endpoint API

| Method | Endpoint | Kegunaan |
|---|---|---|
| GET | `/` | Cek API hidup atau tidak |
| POST | `/sessions` | Bikin sesi chat baru |
| POST | `/ask` | Kirim pertanyaan, dapat jawaban + grounding check |
| POST | `/feedback` | Kirim rating bintang untuk suatu jawaban |

### Memilih model LLM (Groq atau Gemini)

Endpoint `POST /ask` menerima parameter opsional `"model"` untuk memilih
LLM yang dipakai:
- `"model": "groq"` → pakai Groq (llama-3.3-70b-versatile) — **default**
  kalau parameter ini tidak diisi/dikosongkan
- `"model": "gemini"` → pakai Gemini (gemini-2.0-flash)

Contoh body request `POST /ask`:
```json
{
  "pertanyaan": "Apa hukum tajwid lafaz Ar-Rahman dalam surah An-Naba?",
  "session_id": null,
  "model": "gemini"
}
```

Contoh response:
```json
{
  "question_id": 1,
  "answer_id": 1,
  "session_id": 1,
  "model_digunakan": "gemini-2.0-flash",
  "jawaban": "...",
  "sumber": ["Kitab Hidayatus Sibyan"],
  "is_grounded": true,
  "grounding_score": 0.706
}
```

## 👥 Kontributor
 
| Nama Lengkap | NIM | Peran |
|---|---|---|
| Ratu Amaliah | 11230910000026 | Dataset & RAG Core |
| Fitria Sintia Wati | 11230910000036 | Frontend |
| Fadiya Tsabita | 11230910000062 | Evaluasi & Hukum Tajwid |
| Syifa Auliyah Kusumawardani | 11230910000114 | Backend, API & Database |
