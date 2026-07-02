"""
LLM kedua: Google Gemini — untuk fitur perbandingan model (task HARI 4).

Sengaja dibuat MIRIP struktur generator.py (Groq) supaya main_api.py bisa
manggil dua-duanya dengan cara yang sama (sama-sama menerima query + konteks,
sama-sama mengembalikan dict {jawaban, sumber, konteks_digunakan}).

generator.py (Groq) TIDAK diubah sama sekali oleh file ini.
"""
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
_model = genai.GenerativeModel("gemini-3-flash-preview")


def generate_answer(query: str, konteks: list) -> dict:
    if not konteks:
        return {
            "jawaban": "Maaf, tidak ditemukan informasi tajwid yang relevan dengan pertanyaan tersebut dalam database An-Naba.",
            "sumber": []
        }

    konteks_text = ""
    for i, item in enumerate(konteks, 1):
        konteks_text += f"""
[Konteks {i}]
Ayat: {item['ayat_number']}
Lafaz: {item['lafaz_arab']} ({item['transliterasi']})
Hukum: {item['hukum']}
Kategori: {item['kategori']}
Penjelasan: {item['penjelasan']}
Sumber: {item['sumber']}
"""

    # Prompt sengaja dibuat SAMA PERSIS dengan generator.py (Groq) supaya
    # perbandingan hasil dua LLM ini adil — variabelnya cuma model-nya,
    # bukan instruksinya.
    prompt = f"""Kamu adalah sistem pakar tajwid Al-Quran khusus untuk Surah An-Naba.
Tugasmu adalah menjawab pertanyaan tentang hukum tajwid HANYA berdasarkan konteks yang diberikan di bawah ini.

ATURAN KETAT:
1. Jawab HANYA berdasarkan konteks yang tersedia, jangan menambah informasi dari luar konteks.
2. Jika informasi tidak ada di konteks, katakan "Informasi tersebut tidak tersedia dalam database tajwid An-Naba."
3. Selalu sebutkan sumber rujukan di akhir jawaban.
4. Gunakan bahasa Indonesia yang jelas dan mudah dipahami.
5. Jangan mengarang atau berasumsi hukum tajwid yang tidak ada di konteks.

KONTEKS YANG TERSEDIA:
{konteks_text}

PERTANYAAN: {query}

JAWABAN:"""

    response = _model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(temperature=0.1)
    )

    sumber_list = list(set([item["sumber"] for item in konteks]))

    return {
        "jawaban": response.text,
        "sumber": sumber_list,
        "konteks_digunakan": len(konteks)
    }