"""
Strict Grounding Check — fitur UTAMA penelitian ini.

Prompt di generator.py sudah MEMINTA LLM untuk tidak mengarang, tapi itu
tidak menjamin apa-apa — LLM tetap bisa halusinasi. Modul ini melakukan
verifikasi TERPISAH setelah jawaban dihasilkan: mengecek apakah kalimat-
kalimat di jawaban benar-benar didukung oleh konteks yang di-retrieve.

Cara kerja (pendekatan embedding similarity, sederhana tapi terukur):
1. Pecah jawaban jadi kalimat-kalimat.
2. Embed setiap kalimat jawaban dan setiap potongan konteks (pakai model
   yang sama dengan retriever: paraphrase-multilingual-mpnet-base-v2).
3. Untuk tiap kalimat jawaban, cari skor similarity tertinggi terhadap
   semua konteks.
4. Jika skor di bawah threshold -> kalimat itu dianggap TIDAK grounded
   (kemungkinan LLM menambah informasi dari luar konteks / halusinasi).
5. Skor akhir = rata-rata skor semua kalimat. is_grounded = True jika
   proporsi kalimat grounded >= GROUNDING_THRESHOLD_RATIO.

Kalimat yang murni template ("Informasi tersebut tidak tersedia...",
"Sumber:", dll) dikecualikan dari pengecekan supaya tidak salah flag.
"""
import re
from src.shared.embedding_model import get_embedding_model
import numpy as np

SIMILARITY_THRESHOLD = 0.45   # skor cosine minimum per kalimat supaya dianggap grounded
GROUNDING_THRESHOLD_RATIO = 0.7  # minimal 70% kalimat harus grounded

TEMPLATE_PATTERNS = [
    "informasi tersebut tidak tersedia",
    "tidak ditemukan informasi",
    "sumber:",
]


def _get_model():
    return get_embedding_model()  # pakai model BERSAMA, sama dengan yang dipakai retriever.py


def _split_sentences(text: str):
    # split sederhana berbasis tanda titik/tanya/seru, cukup untuk Bahasa Indonesia
    kalimat = re.split(r'(?<=[.!?])\s+', text.strip())
    return [k.strip() for k in kalimat if k.strip()]


def _is_template_sentence(kalimat: str) -> bool:
    lower = kalimat.lower()
    return any(p in lower for p in TEMPLATE_PATTERNS)


def _cosine_sim(a, b):
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    return float(np.dot(a, b))


def check_grounding(jawaban: str, konteks: list) -> dict:
    """
    Args:
        jawaban: teks jawaban dari LLM (hasil generate_answer)
        konteks: list dict hasil retrieve_tajwid (harus punya key 'penjelasan')

    Returns:
        dict: {
            is_grounded: bool,
            grounding_score: float (0-1, rata-rata similarity tertinggi per kalimat),
            detail_kalimat: [{kalimat, skor, grounded}, ...]
        }
    """
    if not konteks:
        return {"is_grounded": False, "grounding_score": 0.0, "detail_kalimat": []}

    model = _get_model()
    kalimat_list = _split_sentences(jawaban)
    kalimat_dicek = [k for k in kalimat_list if not _is_template_sentence(k)]

    if not kalimat_dicek:
        # semua kalimat adalah template ("informasi tidak tersedia") -> aman, grounded by default
        return {"is_grounded": True, "grounding_score": 1.0, "detail_kalimat": []}

    konteks_texts = [c["penjelasan"] for c in konteks]
    konteks_embeddings = model.encode(konteks_texts, convert_to_numpy=True)
    kalimat_embeddings = model.encode(kalimat_dicek, convert_to_numpy=True)

    detail = []
    skor_list = []
    for kalimat, emb in zip(kalimat_dicek, kalimat_embeddings):
        skor_tertinggi = max(_cosine_sim(emb, k_emb) for k_emb in konteks_embeddings)
        grounded = skor_tertinggi >= SIMILARITY_THRESHOLD
        detail.append({"kalimat": kalimat, "skor": round(skor_tertinggi, 3), "grounded": grounded})
        skor_list.append(skor_tertinggi)

    grounding_score = float(np.mean(skor_list))
    proporsi_grounded = sum(1 for d in detail if d["grounded"]) / len(detail)
    is_grounded = proporsi_grounded >= GROUNDING_THRESHOLD_RATIO

    return {
        "is_grounded": is_grounded,
        "grounding_score": round(grounding_score, 3),
        "detail_kalimat": detail,
    }


if __name__ == "__main__":
    # contoh cepat untuk uji manual
    konteks_dummy = [
        {"penjelasan": "Mad Thabi'i terjadi ketika huruf alif, wau, atau ya bertemu harakat yang sesuai, dibaca panjang 2 harakat."}
    ]
    jawaban_dummy = "Mad Thabi'i dibaca panjang 2 harakat. Selain itu hukum ini juga berlaku untuk waqaf di akhir surah dengan durasi 6 harakat."
    hasil = check_grounding(jawaban_dummy, konteks_dummy)
    print(hasil)