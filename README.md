# Tajwid RAG — Sistem Tanya Jawab Hukum Tajwid Surah An-Naba'

Sistem RAG (Retrieval-Augmented Generation) untuk menjawab pertanyaan seputar
hukum tajwid dalam Surah An-Naba', dengan **strict grounding check** —
jawaban LLM diverifikasi otomatis supaya tidak mengarang di luar data yang ada.

Sistem ini mendukung **dua pilihan LLM**: Groq (llama-3.3-70b-versatile) dan
Gemini (gemini-3-flash-preview), yang bisa dipilih langsung lewat parameter di API
atau dropdown di frontend.

## 📁 Struktur Proyek

```
tajwid-rag/
├── main.py                      # jalankan sistem lewat CLI (terminal)
├── eval.py                      # skrip evaluasi otomatis (ROUGE-L, BERTScore, Faithfulness)
├── qna_dataset_50.json          # dataset 50 soal Q&A untuk evaluasi
├── hasil_evaluasi.csv           # hasil evaluasi (dibuat otomatis oleh eval.py)
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
    │   └── embedding_model.py     # satu instance model embedding dipakai bareng oleh retriever.py & strict_grounding.py
    │
    ├── inspect_chroma.py          # (opsional) utilitas untuk cek isi ChromaDB dari terminal, tidak dipakai saat runtime
    │
    ├── database/
    │   └── setup_app_tables.py    # bikin 6 tabel: users, sessions, questions, retrieved_docs, answers, feedback
    │
    └── api/
        └── main_api.py            # FastAPI, endpoint untuk frontend
```

## ✅ Prasyarat

Sebelum mulai, pastikan sudah terinstall:
- **Python 3.12** (versi yang sudah diuji berjalan lancar dengan proyek ini)
- **XAMPP** (Apache + MySQL) — [apachefriends.org](https://www.apachefriends.org)
- Akun **Groq Cloud** untuk API key gratis — [console.groq.com](https://console.groq.com)
- Akun **Google AI Studio** untuk API key Gemini gratis — [aistudio.google.com/api-keys](https://aistudio.google.com/api-keys)

> Catatan: proyek ini bisa didapat dengan **clone lewat Git** atau **download
> ZIP langsung dari GitHub**. Kalau tidak familiar dengan Git, download ZIP
> jauh lebih simpel dan sudah terbukti bisa dijalankan penuh mengikuti langkah
> di bawah.

> ⚠️ **Penting soal folder `tajwid-rag-backend/`:** kalau hasil ekstrak ZIP
> kamu punya folder tambahan bernama `tajwid-rag-backend/` di dalam root
> repo (berisi salinan lama `main.py`, `src/`, `data/`, `requirements.txt`),
> itu adalah **folder versi lama/tidak terpakai** yang tertinggal saat
> pengembangan (masih pakai model `gemini-2.0-flash`, requirements-nya juga
> belum ada `rouge-score`/`bert-score`, dan tidak punya folder `frontend/`
> sama sekali). Semua langkah di README ini merujuk ke file-file di **root
> repo**, bukan ke folder `tajwid-rag-backend/`. Supaya tidak bingung mana
> yang harus dijalankan, folder ini **aman dan disarankan untuk dihapus**
> sebelum lanjut ke langkah instalasi.

## 🚀 Langkah Instalasi

### 1. Dapatkan source code

**Opsi A — Download ZIP (paling mudah, tidak perlu install Git):**

1. Buka halaman repo di GitHub.
2. Klik tombol hijau **Code** → **Download ZIP**.
3. Ekstrak file ZIP tersebut (misalnya ke folder `Downloads`).
4. Masuk ke folder hasil ekstrak lewat terminal/PowerShell.

**Opsi B — Clone lewat Git:**
```bash
git clone https://github.com/Amaliahratu24/tajwid-rag.git
cd tajwid-rag
```

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

### 7. Build embeddings ke ChromaDB (wajib sebelum menjalankan API)

```bash
python src/ingestion/build_embeddings.py
```

Skrip ini memuat model embedding lokal (akan otomatis download model dari
Hugging Face saat pertama kali dijalankan), lalu membuat embedding dari data
tajwid dan menyimpannya ke ChromaDB.

Output yang diharapkan:
```
Memuat model embedding lokal...
Memuat data tajwid...
Menghubungkan ke ChromaDB...
Membuat embedding dan menyimpan ke ChromaDB...
Selesai. 44 entri berhasil di-embed dan disimpan ke ChromaDB.
```

### 8. Coba lewat CLI (opsional, untuk tes cepat)

```bash
python main.py
```

Ketik pertanyaan **lengkap** (bukan cuma angka nomor), contoh:
```
Sebutkan contoh Mad Thabi'i dalam surah An-Naba
```

### 9. Jalankan API (backend)

```bash
uvicorn src.api.main_api:app --reload
```

Biarkan terminal ini tetap terbuka selama server berjalan. Buka
`http://localhost:8000/docs` di browser untuk melihat dan mencoba semua
endpoint yang tersedia secara interaktif.


Contoh log normal saat server jalan dan menerima request dari frontend:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Application startup complete.
[TIMING] retrieval: 14.20 detik
[TIMING] generate (llama-3.3-70b-versatile): 0.80 detik
[TIMING] grounding check: 0.35 detik
[TIMING] TOTAL (tanpa DB): 15.37 detik
INFO:     127.0.0.1:51738 - "POST /ask HTTP/1.1" 200 OK
```
Request pertama ke tiap model biasanya lebih lambat (proses load model
embedding pertama kali), request selanjutnya jauh lebih cepat.

### 10. Buka Frontend (website)

Pastikan API di Langkah 9 masih berjalan (terminal jangan ditutup). **Buka
terminal baru** (jangan tutup terminal API), lalu:

```bash
cd frontend
python -m http.server 5500
```

Lalu buka `http://localhost:5500` di browser.

Output normal saat server frontend jalan:
```
Serving HTTP on :: port 5500 (http://[::]:5500/) ...
"GET / HTTP/1.1" 200 -
"GET /style.css HTTP/1.1" 200 -
"GET /script.js HTTP/1.1" 200 -
"GET /favicon.ico" 404 -
```

Alternatif lain: buka folder `frontend/` di File Explorer, lalu klik dua kali
`index.html` langsung — tapi kadang browser membatasi koneksi API dari file
lokal (`file://`), jadi cara `http.server` di atas lebih disarankan.

Website akan otomatis terhubung ke API di `http://localhost:8000` (sudah
diatur di `frontend/script.js`, baris `API_URL`). Ada dropdown di pojok
kanan atas untuk pilih model **Groq** atau **Gemini**.

## 📊 Evaluasi

Sistem diuji memakai dataset **50 pertanyaan** (`qna_dataset_50.json`) — 44
pertanyaan **in-domain** (jawabannya ada di database tajwid An-Naba') dan 6
pertanyaan **out-of-domain** (sengaja di luar cakupan, untuk menguji apakah
sistem menolak mengarang jawaban).

### Cara menjalankan evaluasi

```bash
pip install rouge-score bert-score requests
python eval.py
```

Skrip ini **resumable** — kalau berhenti di tengah jalan (misalnya kena limit
API), tinggal jalankan lagi `python eval.py` dan otomatis melanjutkan dari
yang belum selesai, tanpa mengulang yang sudah berhasil. Kalau semua 100
baris (50 soal × 2 model) sudah pernah berhasil sebelumnya, skrip akan
menampilkan:
```
Ditemukan 100 hasil sebelumnya, akan dilewati (skip).
SEMUA DATA LENGKAP (50 x 2 model).
```
dan langsung menampilkan ringkasan tanpa memanggil API lagi. Hasilnya
tersimpan di `hasil_evaluasi.csv`.

### Metrik yang digunakan

| Metrik | Mengukur |
|---|---|
| **ROUGE-L** | Kemiripan susunan kata jawaban sistem vs jawaban rujukan |
| **BERTScore F1** | Kemiripan makna (semantik) jawaban sistem vs jawaban rujukan |
| **Faithfulness (grounding score)** | Seberapa besar jawaban benar-benar didukung oleh konteks yang diambil sistem, bukan karangan LLM |

### Hasil (50 pertanyaan × 2 model = 100 data)

| Model | ROUGE-L | BERTScore F1 | Faithfulness | Grounded (dari 50) |
|---|---|---|---|---|
| **Groq** (llama-3.3-70b-versatile) | 0.7350 | 0.8744 | 0.7879 | 46/50 |
| **Gemini** (gemini-3-flash-preview) | 0.7816 | 0.8384 | 0.7378 | 50/50 |

**Catatan singkat:**
- **Gemini** unggul di ROUGE-L (susunan kata lebih dekat ke jawaban rujukan)
  dan konsisten lolos grounding check di semua 50 pertanyaan, tapi jauh lebih
  lambat per-request (bisa >20 detik) dibanding Groq.
- **Groq** unggul di BERTScore F1 (makna jawaban) dan Faithfulness, jauh
  lebih cepat (di bawah 1 detik per jawaban), tapi 4 dari 50 jawabannya
  gagal lolos strict grounding check.
- **Keterbatasan Gemini free tier:** model `gemini-3-flash-preview` di Google
  AI Studio dibatasi **20 request per hari** (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`),
  jauh lebih ketat dibanding Groq. Ini perlu diperhitungkan kalau sistem
  dipakai untuk trafik lebih besar dari skala tugas kuliah.


## 👥 Kontributor

| Nama Lengkap | NIM | Peran |
|---|---|---|
| Ratu Amaliah | 11230910000026 | Dataset & RAG Core |
| Fitria Sintia Wati | 11230910000036 | Frontend |
| Fadiya Tsabita | 11230910000062 | Evaluasi & Hukum Tajwid |
| Syifa Auliyah Kusumawardani | 11230910000114 | Backend, API & Database |
