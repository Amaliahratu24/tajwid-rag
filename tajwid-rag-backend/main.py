from src.retrieval.retriever import retrieve_tajwid
from src.generation.generator import generate_answer

CONTOH_PERTANYAAN = [
    "1. Apa hukum tajwid lafaz Ar-Rahman dalam surah An-Naba?",
    "2. Jelaskan hukum bacaan idgham bighunnah pada ayat 1 An-Naba",
    "3. Apa yang dimaksud Mad Arid Lissukun dalam surah An-Naba?",
    "4. Sebutkan contoh izhar qamariyyah dalam surah An-Naba",
    "5. Jelaskan hukum tajwid lafaz Jahannam dalam An-Naba",
    "6. Apa hukum bacaan pada lafaz An-Naba di ayat 2?",
    "7. Jelaskan hukum ghunnah yang terdapat dalam surah An-Naba",
    "8. Apa contoh idgham syamsiyyah dalam surah An-Naba?",
    "9. Jelaskan hukum tajwid lafaz Al-Fashl dalam An-Naba",
    "10. Sebutkan contoh Mad Thabi'i dalam surah An-Naba",
]

def tanya_tajwid(pertanyaan: str):
    print(f"\nPertanyaan: {pertanyaan}")
    print("Mencari konteks relevan...")
    konteks = retrieve_tajwid(pertanyaan, top_k=3)
    print(f"Ditemukan {len(konteks)} konteks relevan.")
    print("Menghasilkan jawaban...\n")
    hasil = generate_answer(pertanyaan, konteks)
    print("=" * 50)
    print("JAWABAN:")
    print(hasil["jawaban"])
    print("\nSumber:", ", ".join(hasil["sumber"]))
    print("=" * 50)
    return hasil

def main():
    print("\n" + "=" * 50)
    print("SISTEM RAG TAJWID SURAH AN-NABA")
    print("=" * 50)
    print("\nContoh pertanyaan yang bisa kamu ajukan:")
    for q in CONTOH_PERTANYAAN:
        print(f"  {q}")
    print("\nKetik pertanyaan kamu, atau ketik 'keluar' untuk berhenti.")

    while True:
        print()
        pertanyaan = input("Pertanyaan kamu: ").strip()
        if pertanyaan.lower() in ["keluar", "exit", "quit"]:
            print("Terima kasih, sistem dihentikan.")
            break
        if not pertanyaan:
            print("Pertanyaan tidak boleh kosong, coba lagi.")
            continue
        tanya_tajwid(pertanyaan)

if __name__ == "__main__":
    main()