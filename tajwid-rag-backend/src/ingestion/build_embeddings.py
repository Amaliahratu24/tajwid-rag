import json
import os
import chromadb
from chromadb.api.types import EmbeddingFunction
from sentence_transformers import SentenceTransformer

class LocalEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model_name):
        self.model = SentenceTransformer(model_name)

    def __call__(self, input):
        embeddings = self.model.encode(input, convert_to_numpy=True)
        return embeddings.tolist()

def main():
    print("Memuat model embedding lokal...")
    embedding_fn = LocalEmbeddingFunction("paraphrase-multilingual-mpnet-base-v2")

    print("Memuat data tajwid...")
    with open("data/tajwid_annaba.json", "r", encoding="utf-8") as f:
        tajwid_data = json.load(f)

    documents = []
    metadatas = []
    ids = []

    for item in tajwid_data:
        teks_gabungan = (
            f"Lafaz: {item['lafaz_arab']} ({item['transliterasi']}). "
            f"Hukum: {item['hukum']}. "
            f"Kategori: {item['kategori']}. "
            f"Penjelasan: {item['penjelasan']}"
        )
        documents.append(teks_gabungan)
        metadatas.append({
            "ayat_number": item["ayat"],
            "lafaz_arab": item["lafaz_arab"],
            "transliterasi": item["transliterasi"],
            "hukum": item["hukum"],
            "kategori": item["kategori"],
            "sumber": item["sumber"]
        })
        ids.append(f"tajwid_{item['id']}")

    print("Menghubungkan ke ChromaDB...")
    client = chromadb.PersistentClient(path="data/chromadb")

    try:
        client.delete_collection("tajwid_annaba")
    except:
        pass

    collection = client.create_collection(
        name="tajwid_annaba",
        embedding_function=embedding_fn
    )

    print("Membuat embedding dan menyimpan ke ChromaDB...")
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print(f"Selesai. {len(documents)} entri berhasil di-embed dan disimpan ke ChromaDB.")

if __name__ == "__main__":
    main()