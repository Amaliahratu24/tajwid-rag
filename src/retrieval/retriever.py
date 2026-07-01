import chromadb
from chromadb.api.types import EmbeddingFunction
from sentence_transformers import SentenceTransformer
import mysql.connector
import os
import re
from dotenv import load_dotenv

load_dotenv()

class LocalEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name):
        self.model = SentenceTransformer(model_name)

    def __call__(self, input):
        embeddings = self.model.encode(input, convert_to_numpy=True)
        return embeddings.tolist()

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT"))
    )

def ekstrak_nomor_ayat(query: str):
    """Deteksi apakah query mengandung nomor ayat."""
    pola = r'\b(ayat|surah|surat|verse)?\s*(ke[- ]?)?\s*(\d+)\b'
    match = re.search(pola, query.lower())
    if match:
        return int(match.group(3))
    return None

def retrieve_dari_mysql(ayat_number: int):
    """Ambil semua hukum tajwid berdasarkan nomor ayat dari MySQL."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM hukum_tajwid WHERE ayat_number = %s
    """, (ayat_number,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def retrieve_dari_chroma(query: str, top_k: int = 5):
    """Semantic search dari ChromaDB."""
    embedding_fn = LocalEmbeddingFunction("paraphrase-multilingual-mpnet-base-v2")
    client = chromadb.PersistentClient(path="data/chromadb")
    collection = client.get_collection(
        name="tajwid_annaba",
        embedding_function=embedding_fn
    )
    results = collection.query(
        query_texts=[query],
        n_results=top_k
    )

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    konteks = []
    for i, metadata in enumerate(results["metadatas"][0]):
        cursor.execute("""
            SELECT * FROM hukum_tajwid
            WHERE ayat_number = %s AND lafaz_arab = %s
        """, (metadata["ayat_number"], metadata["lafaz_arab"]))
        row = cursor.fetchone()
        if row:
            row["similarity_score"] = results["distances"][0][i]
            konteks.append(row)
    cursor.close()
    conn.close()
    return konteks

def retrieve_tajwid(query: str, top_k: int = 5):
    """
    Hybrid retrieval:
    - Jika query mengandung nomor ayat → prioritaskan filter MySQL by ayat_number
    - Lalu gabungkan dengan hasil semantic search ChromaDB
    - Deduplikasi berdasarkan id
    """
    hasil_akhir = []
    ids_sudah_ada = set()

    # Cek apakah ada nomor ayat di query
    nomor_ayat = ekstrak_nomor_ayat(query)

    if nomor_ayat:
        rows_mysql = retrieve_dari_mysql(nomor_ayat)
        for row in rows_mysql:
            if row["id"] not in ids_sudah_ada:
                hasil_akhir.append(row)
                ids_sudah_ada.add(row["id"])

    # Tambahkan hasil semantic search
    hasil_chroma = retrieve_dari_chroma(query, top_k=top_k)
    for item in hasil_chroma:
        if item["id"] not in ids_sudah_ada:
            hasil_akhir.append(item)
            ids_sudah_ada.add(item["id"])

    return hasil_akhir