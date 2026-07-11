# Tajwid RAG — Sistem Tanya Jawab Hukum Tajwid Surah An-Naba'

Sistem RAG (Retrieval-Augmented Generation) untuk menjawab pertanyaan seputar
hukum tajwid dalam Surah An-Naba', dengan **strict grounding check** —
jawaban LLM diverifikasi otomatis supaya tidak mengarang di luar data yang ada.

Sistem ini mendukung **dua pilihan LLM**: Groq (llama-3.3-70b-versatile) dan
Gemini (gemini-2.0-flash), yang bisa dipilih langsung lewat parameter di API
atau dropdown di frontend.

## 📁 Struktur Proyek

```
tajwid-rag/
├── main.py                      # jalankan sistem lewat CLI (terminal)
├── requirements.txt              # daftar library Python
├── .env                          # konfigurasi
│
├── data/
│   ├── annaba_raw.json           # 40 ayat An-Naba' (arab, latin, arti)
│   ├── tajwid_annaba.json        # data hukum tajwid tiap ayat
│   └── chromadb/                 # vector database (dibuat otomatis)
│
├── frontend/                     # tampilan website
│   ├── index.html
│   ├── script.js                 # panggil API ke http://localhost:8000
│   └── style.css
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
    │   └── llm_gemini.py          # kirim ke LLM Gemini, hasilkan jawaban 
    │
    ├── grounding/
    │   └── strict_grounding.py    # verifikasi jawaban benar2 didukung konteks
    │
    ├── shared/
    │   └── embedding_model.py     # satu instance model embedding dipakai bareng
    │                               #   oleh retriever.py & strict_grounding.py
    │
    ├── database/
    │   └── setup_app_tables.py    # bikin 6 tabel: users, sessions, questions,
    │                               #   retrieved_docs, answers, feedback
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

Proses ini agak lama karena ada library besar seperti `torch`
dan `sentence-transformers`. Tunggu sampai selesai tanpa error.

### 3. Buat file `.env`

Buat file `.env` di folder utama repo, lalu isi dengan konfigurasi
**laptop kamu sendiri**:

```
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=
DB_NAME=tajwid_rag
DB_PORT=3306
GROQ_API_KEY=isi_dengan_api_key_groq_kamu
GEMINI_API_KEY=isi_dengan_api_key_gemini_kamu
```

Dapatkan `GROQ_API_KEY` gratis di [console.groq.com](https://console.groq.com)
→ menu **API Keys** → **Create API Key**.

Dapatkan `GEMINI_API_KEY` gratis di [aistudio.google.com/api-keys](https://aistudio.google.com/api-keys)
→ klik ikon kunci 🔑 di pojok kiri bawah → **Create API key** → pilih
**Create API key in new project**.

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

### 8. Jalankan API (backend)

```bash
uvicorn src.api.main_api:app --reload
```

Biarkan terminal ini tetap terbuka selama server berjalan. Buka
`http://localhost:8000/docs` di browser untuk melihat dan mencoba semua
endpoint yang tersedia secara interaktif.

### 9. Buka Frontend (website)

Pastikan API di Langkah 8 masih berjalan (terminal jangan ditutup), lalu:

1. Buka folder `frontend/` di File Explorer
2. Klik dua kali file `index.html` — akan terbuka otomatis di browser

Atau, kalau `index.html` tidak mau langsung connect ke API (karena
kadang browser membatasi file lokal), jalankan lewat server sederhana:
```bash
cd frontend
python -m http.server 5500
```
lalu buka `http://localhost:5500` di browser.

Website akan otomatis terhubung ke API di `http://localhost:8000` (sudah
diatur di `frontend/script.js`, baris `API_URL`). Ada dropdown di pojok
kanan atas untuk pilih model **Groq** atau **Gemini**.

## 👥 Kontributor

| Nama Lengkap | NIM | Peran |
|---|---|---|
| Syifa Auliyah Kusumawardani | 11230910000114 | Backend, API & Database |
| Ratu Amaliah | 11230910000026 | Dataset & RAG Core |
| Fitria Sintia Wati | 11230910000036 | Frontend |
| Fadiya Tsabita | 11230910000062 | Evaluasi & Hukum Tajwid |
