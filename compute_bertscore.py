"""
Hitung BERTScore untuk hasil yang sudah didapat eval.py.
Dipisah dari eval.py supaya proses lambat (download+load model BERT)
tidak mengulang tiap kali eval.py dijalankan ulang untuk retry.

Jalankan SETELAH hasil_evaluasi.csv sudah lengkap 100 baris (atau
sebanyak yang berhasil kamu kumpulkan):
    python compute_bertscore.py
"""
import csv
from bert_score import score as bertscore

INPUT_CSV = "hasil_evaluasi.csv"
OUTPUT_CSV = "hasil_evaluasi_final.csv"

with open(INPUT_CSV, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print(f"Menghitung BERTScore untuk {len(rows)} baris (bisa beberapa menit)...")
jawaban = [r["jawaban_sistem"] for r in rows]
referensi = [r["jawaban_benar"] for r in rows]

P, R, F1 = bertscore(jawaban, referensi, lang="id", verbose=True)

for i, row in enumerate(rows):
    row["bertscore_f1"] = round(float(F1[i]), 4)

fieldnames = list(rows[0].keys())
with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"Selesai, tersimpan di {OUTPUT_CSV}")

for model in ["groq", "gemini"]:
    sub = [r for r in rows if r["model"] == model]
    if not sub:
        continue
    avg_rouge = sum(float(r["rougeL"]) for r in sub) / len(sub)
    avg_bert = sum(float(r["bertscore_f1"]) for r in sub) / len(sub)
    avg_ground = sum(float(r["grounding_score_faithfulness"] or 0) for r in sub) / len(sub)
    print(f"\nRingkasan model {model} (dari {len(sub)} data):")
    print(f"  Rata-rata ROUGE-L      : {avg_rouge:.4f}")
    print(f"  Rata-rata BERTScore F1 : {avg_bert:.4f}")
    print(f"  Rata-rata Faithfulness : {avg_ground:.4f}")
