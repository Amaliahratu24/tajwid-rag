import chromadb
from chromadb.api.types import EmbeddingFunction
from sentence_transformers import SentenceTransformer
import mysql.connector
import os
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

def retrieve_tajwid(query: str, top_k: int = 5):
    # Retrieval dari ChromaDB
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

    # Ambil detail lengkap dari MySQL berdasarkan hasil Chroma
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
            konteks.append({
                "ayat_number": row["ayat_number"],
                "lafaz_arab": row["lafaz_arab"],
                "transliterasi": row["transliterasi"],
                "hukum": row["hukum"],
                "kategori": row["kategori"],
                "penjelasan": row["penjelasan"],
                "sumber": row["sumber"],
                "similarity_score": results["distances"][0][i]
            })

    cursor.close()
    conn.close()
    return konteks