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
    embedding_fn = LocalEmbeddingFunction("paraphrase-multilingual-mpnet-base-v2")
    client = chromadb.PersistentClient(path="data/chromadb")
    collection = client.get_collection(
        name="tajwid_annaba",
        embedding_function=embedding_fn
    )

    print(f"Total entri di ChromaDB: {collection.count()}\n")

    hasil = collection.get()
    for i, (doc, meta) in enumerate(zip(hasil["documents"], hasil["metadatas"])):
        print(f"--- Entri {i+1} ---")
        print(f"ID       : {hasil['ids'][i]}")
        print(f"Ayat     : {meta['ayat_number']}")
        print(f"Lafaz    : {meta['lafaz_arab']} ({meta['transliterasi']})")
        print(f"Hukum    : {meta['hukum']}")
        print(f"Kategori : {meta['kategori']}")
        print(f"Dokumen  : {doc}")
        print()

if __name__ == "__main__":
    main()