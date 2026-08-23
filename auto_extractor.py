import os
import json
from rag_engine import RAGEngine
from document_loader import load_text_file, load_pdf_file, semantic_chunking

def extract_clinical_data(engine, text_chunk):
    """
    Yerel LLM'e metin parçasını gönderip sadece JSON formatında veri çeker.
    """
    prompt = f"""
    Sen uzman bir klinik veri asistanısın. Aşağıdaki medikal metni analiz et. 
    Metindeki hastalıkları, teşhis kriterlerini, semptomları ve varsa klinik uyarıları çıkar.
    YANITINI SADECE AŞAĞIDAKİ JSON FORMATINDA VER. HİÇBİR EKBİLGİ VEYA SOHBET METNİ EKLEME.
    
    Beklenen Format:
    [
      {{
        "hastalik": "Hastalık Adı",
        "semptomlar": ["semptom1", "semptom2"],
        "klinik_uyari": "Varsa önemli uyarı"
      }}
    ]
    
    Metin:
    {text_chunk}
    """
    try:
        response = engine.generate_direct(prompt)
        

        clean_response = response.strip().strip("```json").strip("```").strip()
        data = json.loads(clean_response)
        return data
    except Exception as e:
        print(f"[-] Bu parçadan JSON çıkarılamadı veya hastalık bulunamadı. Hata: {e}")
        return []

def run_autonomous_pipeline(data_dir="data"):
    print("=" * 60)
    print(" Otonom Klinik Veri Çıkarım Hattı Başlatılıyor...")
    print("=" * 60)
    
    engine = RAGEngine()
    all_extracted_data = []
    
    if not os.path.exists(data_dir):
        print(f"[-] '{data_dir}' klasörü bulunamadı.")
        return


    for file_name in os.listdir(data_dir):
        file_path = os.path.join(data_dir, file_name)
        

        if file_name.endswith('.json'):
            continue
            
        print(f"\n[+] Okunuyor: {file_name}")
        raw_text = ""
        
        if file_name.endswith('.txt'):
            raw_text = load_text_file(file_path)
        elif file_name.endswith('.pdf'):
            raw_text = load_pdf_file(file_path)
            
        if not raw_text:
            continue
            
        chunks = semantic_chunking(raw_text, source_name=file_name, max_length=400)
        
        for i, chunk in enumerate(chunks):
            print(f"  -> Parça {i+1}/{len(chunks)} analiz ediliyor...")
            extracted_json = extract_clinical_data(engine, chunk["text"])
            
            if extracted_json and isinstance(extracted_json, list):
                all_extracted_data.extend(extracted_json)

    if all_extracted_data:
        output_path = os.path.join(data_dir, "otomatik_semptomlar.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_extracted_data, f, ensure_ascii=False, indent=4)
        print("\n" + "=" * 60)
        print(f"[OK] Mükemmel! Tüm belgeler tarandı.")
        print(f"[OK] Toplam {len(all_extracted_data)} hastalık/semptom eşleşmesi çıkarıldı.")
        print(f"[OK] Veriler '{output_path}' dosyasına kaydedildi.")
        print("=" * 60)
    else:
        print("\n[-] Metinlerden yapılandırılmış veri çıkarılamadı.")

if __name__ == "__main__":
    run_autonomous_pipeline()