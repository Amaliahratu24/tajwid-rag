"""
Skrip evaluasi otomatis sistem Tajwid RAG (versi cepat & aman terputus).

Cara pakai:
1. Pastikan API sudah jalan: uvicorn src.api.main_api:app --reload
2. pip install rouge-score bert-score requests
3. Jalankan: python eval.py

PENTING:
- Setiap hasil LANGSUNG ditulis ke hasil_evaluasi.csv begitu didapat
  (bukan di akhir semua proses). Jadi kalau kamu Ctrl+C di tengah jalan
  karena kelamaan, data yang SUDAH didapat TETAP AMAN tersimpan.
- Jalankan skrip ini lagi kapan saja untuk melanjutkan sisa yang belum -
  otomatis skip yang sudah ada di CSV.
- Kalau ada pertanyaan yang gagal, TIDAK diulang otomatis di tempat
  (supaya tidak buang waktu nunggu timeout berkali-kali) - cukup jalankan
  skrip ini lagi di akhir, ID yang gagal otomatis dicoba lagi karena
  belum tercatat di CSV.
"""
import json
import csv
import os
import time
import requests
from rouge_score import rouge_scorer

API_URL = "http://localhost:8000/ask"
DATASET_PATH = "qna_dataset_50.json"
OUTPUT_CSV = "hasil_evaluasi.csv"

MODELS = ["groq", "gemini"]
DELAY = {"groq": 0.3, "gemini": 1.5}   # jeda antar request, tidak retry bertubi-tubi lagi
TIMEOUT = 30  # detik, lebih pendek dari sebelumnya (60s) biar gagal cepat ketauan

FIELDNAMES = ["id", "tipe", "model", "pertanyaan", "jawaban_benar",
              "jawaban_sistem", "rougeL", "is_grounded",
              "grounding_score_faithfulness"]


def load_existing_keys():
    keys = set()
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                keys.add((int(row["id"]), row["model"]))
    return keys


def append_row(row):
    file_exists = os.path.exists(OUTPUT_CSV)
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def main():
    with open(DATASET_PATH, encoding="utf-8") as f:
        dataset = json.load(f)

    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False)
    existing = load_existing_keys()
    print(f"Ditemukan {len(existing)} hasil sebelumnya (dilewati).")

    gagal = []
    for model in MODELS:
        print(f"\n=== Model: {model} ===")
        for item in dataset:
            key = (item["id"], model)
            if key in existing:
                continue

            try:
                resp = requests.post(API_URL, json={
                    "pertanyaan": item["pertanyaan"],
                    "session_id": None,
                    "model": model
                }, timeout=TIMEOUT)
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"  [GAGAL] id={item['id']}: {e}")
                gagal.append((item["id"], model))
                time.sleep(DELAY[model])
                continue

            jawaban_sistem = data.get("jawaban", "")
            rouge = scorer.score(item["jawaban_benar"], jawaban_sistem)["rougeL"].fmeasure

            row = {
                "id": item["id"], "tipe": item["tipe"], "model": model,
                "pertanyaan": item["pertanyaan"], "jawaban_benar": item["jawaban_benar"],
                "jawaban_sistem": jawaban_sistem, "rougeL": round(rouge, 4),
                "is_grounded": data.get("is_grounded"),
                "grounding_score_faithfulness": data.get("grounding_score"),
            }
            append_row(row)  # LANGSUNG simpan, tidak nunggu akhir program
            print(f"  id={item['id']:>2}  ROUGE-L={rouge:.3f}  grounded={data.get('is_grounded')}")
            time.sleep(DELAY[model])

    if gagal:
        print(f"\n{len(gagal)} pertanyaan gagal: {gagal}")
        print("Jalankan 'python eval.py' lagi untuk mencoba ulang HANYA yang gagal ini.")
    else:
        print("\nSemua pertanyaan berhasil diproses.")

    print("\nBERTScore belum dihitung di run ini - jalankan compute_bertscore.py")
    print("setelah semua baris di atas lengkap (lihat instruksi di bawah).")


if __name__ == "__main__":
    main()
