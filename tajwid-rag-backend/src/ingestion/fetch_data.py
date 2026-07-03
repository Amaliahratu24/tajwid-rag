import requests
import json
import os

# An-Naba adalah surah nomor 78
SURAH_NUMBER = 78

def fetch_surah_data():
    url = f"https://raw.githubusercontent.com/risan/quran-json/main/dist/chapters/id/{SURAH_NUMBER}.json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def fetch_transliteration():
    url = f"https://raw.githubusercontent.com/risan/quran-json/main/dist/chapters/{SURAH_NUMBER}.json"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def main():
    print("Mengambil data ayat An-Naba (Arab + terjemahan Indonesia)...")
    data_id = fetch_surah_data()
    print("Mengambil data transliterasi...")
    data_translit = fetch_transliteration()

    # Gabungkan data
    combined = []
    for v_id, v_tl in zip(data_id["verses"], data_translit["verses"]):
        combined.append({
            "ayat_number": v_id["id"],
            "arabic": v_id["text"],
            "translation_id": v_id["translation"],
            "transliteration": v_tl.get("transliteration", "")
        })

    os.makedirs("data", exist_ok=True)
    output_path = os.path.join("data", "annaba_raw.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(combined, f, ensure_ascii=False, indent=2)

    print(f"Selesai. Data tersimpan di {output_path}, total {len(combined)} ayat.")

if __name__ == "__main__":
    main()