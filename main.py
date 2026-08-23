import os
import database
from rag_engine import RAGEngine

def main():
    print("=" * 60)
    print(" Microsoft Foundry Local - Çoklu Format Destekli RAG Asistanı")
    print("=" * 60)

    database.init_db()

    print("\n[+] Yerel modeller ve runtime yükleniyor...")
    engine = RAGEngine()
    print("[+] Motor hazır!")

    data_dir = 'data'
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        
    print(f"\n[+] '{data_dir}/' klasöründeki PDF ve TXT dosyaları taranıyor...")
    
    count = engine.ingest_all_documents(data_dir)
    print(f"[+] Toplam {count} metin parçası (chunk) veritabanına başarıyla yüklendi.\n")

    print("=" * 60)
    print(" Sorularınızı sorabilirsiniz (Çıkmak için 'q' yazın):")
    print("=" * 60)

    while True:
        query = input("\nSoru: ").strip()
        if not query:
            continue
        if query.lower() in ['q', 'exit', 'cikis']:
            print("Asistan kapatılıyor...")
            break

        answer, docs = engine.answer_query(query)

        print("\n--- Veritabanından Bulunan Alakalı Parçalar (Retrieval) ---")
        for score, content, source in docs:
            print(f"  * [{source}] (Skor: {score:.4f}) -> {content[:70]}...")

        print("\n--- Modelin Yanıtı (Generation) ---")
        print(answer)

if __name__ == "__main__":
    main()