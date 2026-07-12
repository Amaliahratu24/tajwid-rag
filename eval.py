"""
Skrip evaluasi otomatis sistem Tajwid RAG.

Cara pakai:
1. Pastikan API sudah jalan: uvicorn src.api.main_api:app --reload
2. Install dulu library yang belum ada:
   pip install rouge-score bert-score requests
3. Jalankan dari folder utama repo (sejajar dengan main.py):
   python eval.py

PENTING: skrip ini SEKARANG BISA DILANJUTKAN. Kalau hasil_evaluasi.csv
sudah ada isinya (dari run sebelumnya), baris yang SUDAH berhasil akan
dilewati (skip), cuma baris yang GAGAL/belum ada yang akan dicoba lagi.
Jadi aman dijalankan berkali-kali sampai semua 50x2 lengkap.
"""
import json
import csv
import os
import time
import requests
from rouge_score import rouge_scorer
from bert_score import score as bertscore

API_URL = "http://localhost:8000/ask"
DATASET_PATH = "qna_dataset_50.json"
OUTPUT_CSV = "hasil_evaluasi.csv"

MODELS = ["groq", "gemini"]

DELAY = {"groq": 0.3, "gemini": 4.0}
MAX_RETRY = 3


def load_existing_results():
    """Baca hasil_evaluasi.csv lama (kalau ada), kembalikan dict {(id, model): row}"""
    existing = {}
    if os.path.exists(OUTPUT_CSV):
        with open(OUTPUT_CSV, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing[(int(row["id"]), row["model"])] = row
    return existing


def call_api_with_retry(pertanyaan, model):
    for attempt in range(1, MAX_RETRY + 1):
        try:
            resp = requests.post(API_URL, json={
                "pertanyaan": pertanyaan,
                "session_id": None,
                "model": model
            }, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"    percobaan {attempt}/{MAX_RETRY} gagal: {e}")
            if attempt < MAX_RETRY:
                time.sleep(DELAY[model] * 3)  # jeda lebih panjang sebelum retry
    return None


def main():
    with open(DATASET_PATH, encoding="utf-8") as f:
        dataset = json.load(f)

    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=False)
    existing = load_existing_results()
    print(f"Ditemukan {len(existing)} hasil sebelumnya, akan dilewati (skip).")

    hasil = list(existing.values())  # bawa hasil lama, tambahi yang baru
    baru_per_model = {m: {"jawaban": [], "referensi": [], "row_idx": []} for m in MODELS}

    for model in MODELS:
        print(f"\n=== Model: {model} ===")
        for item in dataset:
            key = (item["id"], model)
            if key in existing:
                continue  # sudah berhasil sebelumnya, skip

            data = call_api_with_retry(item["pertanyaan"], model)
            if data is None:
                print(f"  [MASIH GAGAL] id={item['id']} - akan dicoba lagi di run berikutnya")
                continue

            jawaban_sistem = data.get("jawaban", "")
            rouge = scorer.score(item["jawaban_benar"], jawaban_sistem)["rougeL"].fmeasure

            row = {
                "id": item["id"],
                "tipe": item["tipe"],
                "model": model,
                "pertanyaan": item["pertanyaan"],
                "jawaban_benar": item["jawaban_benar"],
                "jawaban_sistem": jawaban_sistem,
                "rougeL": round(rouge, 4),
                "is_grounded": data.get("is_grounded"),
                "grounding_score_faithfulness": data.get("grounding_score"),
                "bertscore_f1": None,
            }
            hasil.append(row)
            baru_per_model[model]["jawaban"].append(jawaban_sistem)
            baru_per_model[model]["referensi"].append(item["jawaban_benar"])
            baru_per_model[model]["row_idx"].append(len(hasil) - 1)

            print(f"  id={item['id']:>2}  ROUGE-L={rouge:.3f}  grounded={data.get('is_grounded')}")
            time.sleep(DELAY[model])

        # Hitung BERTScore hanya untuk baris BARU model ini
        idxs = baru_per_model[model]["row_idx"]
        if idxs:
            print(f"  Menghitung BERTScore untuk {len(idxs)} jawaban baru model {model}...")
            P, R, F1 = bertscore(
                baru_per_model[model]["jawaban"],
                baru_per_model[model]["referensi"],
                lang="id", verbose=False
            )
            for i, idx in enumerate(idxs):
                hasil[idx]["bertscore_f1"] = round(float(F1[i]), 4)

    # Simpan ulang seluruh hasil (lama + baru) ke CSV
    if hasil:
        fieldnames = ["id", "tipe", "model", "pertanyaan", "jawaban_benar",
                      "jawaban_sistem", "rougeL", "is_grounded",
                      "grounding_score_faithfulness", "bertscore_f1"]
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(hasil)
        print(f"\nTersimpan {len(hasil)} baris total di {OUTPUT_CSV}")

        total_diharapkan = len(dataset) * len(MODELS)
        if len(hasil) < total_diharapkan:
            print(f"BELUM LENGKAP: baru {len(hasil)}/{total_diharapkan}. "
                  f"Jalankan lagi 'python eval.py' untuk melanjutkan sisanya.")
        else:
            print("SEMUA DATA LENGKAP (50 x 2 model).")

        for model in MODELS:
            rows = [r for r in hasil if r["model"] == model and r.get("bertscore_f1") not in (None, "")]
            if not rows:
                continue
            avg_rouge = sum(float(r["rougeL"]) for r in rows) / len(rows)
            avg_bert = sum(float(r["bertscore_f1"]) for r in rows) / len(rows)
            avg_ground = sum(float(r["grounding_score_faithfulness"] or 0) for r in rows) / len(rows)
            print(f"\nRingkasan model {model} (dari {len(rows)} data):")
            print(f"  Rata-rata ROUGE-L      : {avg_rouge:.4f}")
            print(f"  Rata-rata BERTScore F1 : {avg_bert:.4f}")
            print(f"  Rata-rata Faithfulness : {avg_ground:.4f}")
    else:
        print("Tidak ada hasil yang berhasil dikumpulkan. Cek apakah API sudah jalan.")


if __name__ == "__main__":
    main()
