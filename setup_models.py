import time
from foundry_local_sdk import FoundryLocalManager, Configuration

def download_and_setup():
    config = Configuration(app_name="rag_assistant")
    manager = FoundryLocalManager(config)
    
    print("1. Foundry Local servisi başlatılıyor...")
    manager.start_web_service()
    time.sleep(2)

    all_models = manager.catalog.list_models()
    
    emb_model = next((m for m in all_models if "qwen3-embedding-0.6b" in m.id), None)
    if emb_model:
        print(f"\n--- Embedding Modeli Kontrol Ediliyor ({emb_model.id}) ---")
        if not emb_model.is_cached:
            print("Embedding modeli indiriliyor...")
            emb_model.download()
        print("Embedding modeli hazır! ")
    else:
        print("Embedding modeli katalogda bulunamadı!")

    chat_model = next((m for m in all_models if "Phi-3.5-mini-instruct" in m.id), None)
    
    if chat_model:
        print(f"\n--- LLM Chat Modeli Kontrol Ediliyor ({chat_model.id}) ---")
        if not chat_model.is_cached:
            print(f"'{chat_model.id}' yerel diske indirilmeye başlanıyor...")
            print("İndirme boyuta göre birkaç dakika sürebilir, lütfen bekleyin...")
            chat_model.download()
            print("Chat modeli başarıyla indirildi!")
        else:
            print("Chat modeli zaten yerel cihazınızda mevcut! ")
    else:
        print("Chat modeli katalogda bulunamadı!")

if __name__ == "__main__":
    download_and_setup()