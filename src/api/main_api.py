"""
FastAPI layer untuk sistem Tajwid RAG.

Menyatukan: retriever.py (pencarian dokumen) + generator.py (LLM Groq)
+ strict_grounding.py (verifikasi jawaban) + logging ke MySQL.

Jalankan:
    uvicorn src.api.main_api:app --reload --port 8000

Endpoint utama buat (frontend):
    POST /ask   body: {"pertanyaan": "...", "session_id": 1}
    -> {jawaban, sumber, is_grounded, grounding_score, question_id, answer_id}

Kalau session_id belum ada, panggil dulu POST /sessions untuk bikin sesi baru.
"""
import os
import time
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import mysql.connector
from dotenv import load_dotenv

from src.retrieval.retriever import retrieve_tajwid
from src.generation.generator import generate_answer as generate_answer_groq
from src.generation.llm_gemini import generate_answer as generate_answer_gemini
from src.grounding.strict_grounding import check_grounding

load_dotenv()

app = FastAPI(title="Tajwid RAG API", version="0.1.0")

# biar bisa fetch dari localhost:xxxx tanpa CORS error saat development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", ""),
    "database": os.getenv("DB_NAME", "tajwid_rag"),
    "port": int(os.getenv("DB_PORT", 3306)),
}


def get_conn():
    return mysql.connector.connect(**DB_CONFIG)


class AskRequest(BaseModel):
    pertanyaan: str
    session_id: int | None = None
    model: str | None = "groq"  # pilihan: "groq" atau "gemini"


class SessionRequest(BaseModel):
    nama: str | None = None


class FeedbackRequest(BaseModel):
    answer_id: int
    rating: int
    komentar: str | None = None


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Tajwid RAG API jalan"}


@app.post("/sessions")
def buat_session(req: SessionRequest):
    """Bikin sesi baru. Panggil sekali saat user pertama buka chat."""
    conn = get_conn()
    cursor = conn.cursor()
    user_id = None
    if req.nama:
        cursor.execute("INSERT INTO users (nama) VALUES (%s)", (req.nama,))
        user_id = cursor.lastrowid
    cursor.execute("INSERT INTO sessions (user_id) VALUES (%s)", (user_id,))
    session_id = cursor.lastrowid
    conn.commit()
    cursor.close()
    conn.close()
    return {"session_id": session_id}


@app.post("/ask")
def ask(req: AskRequest):
    if not req.pertanyaan.strip():
        raise HTTPException(status_code=400, detail="Pertanyaan tidak boleh kosong")

    conn = get_conn()
    cursor = conn.cursor()

    # kalau frontend belum bikin session, auto-buatkan supaya tidak error
    session_id = req.session_id
    if session_id is None:
        cursor.execute("INSERT INTO sessions (user_id) VALUES (NULL)")
        session_id = cursor.lastrowid
        conn.commit()

    # 1. simpan pertanyaan
    cursor.execute(
        "INSERT INTO questions (session_id, pertanyaan) VALUES (%s, %s)",
        (session_id, req.pertanyaan),
    )
    question_id = cursor.lastrowid
    conn.commit()

    # 2. retrieval
    t0 = time.perf_counter()
    konteks = retrieve_tajwid(req.pertanyaan, top_k=5)
    t1 = time.perf_counter()
    print(f"[TIMING] retrieval: {t1 - t0:.2f} detik")

    # 3. simpan dokumen yang di-retrieve
    for urutan, item in enumerate(konteks, start=1):
        cursor.execute(
            """INSERT INTO retrieved_docs (question_id, hukum_tajwid_id, similarity_score, urutan)
               VALUES (%s, %s, %s, %s)""",
            (question_id, item.get("id"), item.get("similarity_score"), urutan),
        )
    conn.commit()

    # 4. generate jawaban — pilih LLM sesuai request (default: groq)
    t2 = time.perf_counter()
    if (req.model or "groq").lower() == "gemini":
        hasil = generate_answer_gemini(req.pertanyaan, konteks)
        nama_model = "gemini-3-flash-preview"
    else:
        hasil = generate_answer_groq(req.pertanyaan, konteks)
        nama_model = "llama-3.3-70b-versatile"
    t3 = time.perf_counter()
    print(f"[TIMING] generate ({nama_model}): {t3 - t2:.2f} detik")

    # 5. strict grounding check
    t4 = time.perf_counter()
    grounding = check_grounding(hasil["jawaban"], konteks)
    t5 = time.perf_counter()
    print(f"[TIMING] grounding check: {t5 - t4:.2f} detik")
    print(f"[TIMING] TOTAL (tanpa DB): {t5 - t0:.2f} detik")

    # 6. simpan jawaban + hasil grounding
    cursor.execute(
        """INSERT INTO answers (question_id, jawaban, model_llm, is_grounded, grounding_score)
           VALUES (%s, %s, %s, %s, %s)""",
        (question_id, hasil["jawaban"], nama_model,
         grounding["is_grounded"], grounding["grounding_score"]),
    )
    answer_id = cursor.lastrowid
    conn.commit()

    cursor.close()
    conn.close()

    return {
        "question_id": question_id,
        "answer_id": answer_id,
        "session_id": session_id,
        "model_digunakan": nama_model,
        "jawaban": hasil["jawaban"],
        "sumber": hasil["sumber"],
        "is_grounded": grounding["is_grounded"],
        "grounding_score": grounding["grounding_score"],
    }


@app.post("/feedback")
def kirim_feedback(req: FeedbackRequest):
    """Rating bintang 1-5 dari user untuk satu jawaban (task HARI 4)."""
    if not (1 <= req.rating <= 5):
        raise HTTPException(status_code=400, detail="Rating harus 1-5")
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO feedback (answer_id, rating, komentar) VALUES (%s, %s, %s)",
        (req.answer_id, req.rating, req.komentar),
    )
    conn.commit()
    cursor.close()
    conn.close()
    return {"status": "feedback tersimpan"}