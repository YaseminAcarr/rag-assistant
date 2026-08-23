import time
from foundry_local_sdk import FoundryLocalManager, Configuration
import database
import document_loader

class RAGEngine:
    def __init__(self):
        config = Configuration(app_name="rag_assistant")
        try:
            self.manager = FoundryLocalManager(config)
            self.manager.start_web_service()
        except Exception:
            pass
            
        time.sleep(2)
        
        all_models = self.manager.catalog.list_models()
        
        emb_model = next((m for m in all_models if "qwen3-embedding-0.6b" in m.id), None)
        if emb_model and not emb_model.is_loaded:
            emb_model.load()
        self.emb_client = emb_model.get_embedding_client() if emb_model else None

        chat_model = next((m for m in all_models if "Phi-3.5-mini-instruct" in m.id), None)
        if chat_model and not chat_model.is_loaded:
            chat_model.load()
        self.chat_client = chat_model.get_chat_client() if chat_model else None

        if self.chat_client:
            try:
                time.sleep(3)
                self.chat_client.complete_chat(messages=[{"role": "user", "content": "Merhaba"}])
            except Exception as e:
                print(f"[-] Model ısınma uyarısı (önemsiz): {e}")
                pass

    def get_embedding(self, text):
        res = self.emb_client.generate_embeddings(inputs=[text])
        if hasattr(res, 'data') and len(res.data) > 0:
            return res.data[0].embedding
        return res[0]

    def ingest_all_documents(self, data_dir="data"):
        database.clear_documents()
        chunks = document_loader.load_all_documents(data_dir)

        for item in chunks:
            vector = self.get_embedding(item["text"])
            database.save_document(
                content=item["text"],
                source=item["source"],
                embedding_vector=vector
            )
        return len(chunks)

    def generate_direct(self, prompt):
        messages = [{"role": "user", "content": prompt}]
        response = self.chat_client.complete_chat(messages=messages)
        return response.choices[0].message.content
    
    def generate_follow_up_questions(self, answer):
        """
        Üretilen yanıta dayanarak hekimin sorması muhtemel 
        en kritik 3 takip sorusunu güvenli bir şekilde üretir.
        """
        prompt = f"""
        Aşağıdaki medikal yanıta dayanarak, bir hekimin sorması muhtemel en kritik 3 takip sorusunu üret.
        Yanıt: {answer}
        Format: Sadece 3 soru, aralarına virgül koyarak ver. Başka hiçbir açıklama ekleme.
        """
        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.chat_client.complete_chat(messages=messages)
            res = response.choices[0].message.content
            return [q.strip() for q in res.split(',')]
        except Exception:
            return []

    def validate_dosage_safety(self, crcl):
        """
        TÜMÜYLE JENERİK GÜVENLİK KALKANI:
        İlaç ismi fark etmeksizin, hastanın böbrek fonksiyonu düşükse
        hekim için otomatik ve dinamik bir güvenlik uyarısı döndürür.
        """
        warnings = []
        if crcl < 50.0:
            warnings.append(f"⚠️ **Sistem Uyarısı:** Hastanın böbrek klirensi düşüktür (CrCl: {crcl} mL/dk). Lütfen asistanın önerdiği dozun, rehberdeki böbrek yetmezliği dozajlarına uygunluğunu hekim olarak teyit ediniz.")
        return warnings

    def answer_query(self, query, patient_data="", search_query="", crcl_value=65.0):
        enhanced_search_query = f"{search_query} {patient_data} dozaj ampirik tedavi" if search_query else query
        query_vector = self.get_embedding(enhanced_search_query)
        
        relevant_docs = database.search_documents(query_vector, top_k=1, min_similarity=0.15)

        if not relevant_docs:
            return "⚠️ **Bilgi Yok:** Eşleşen klinik rehber bulunamadı.", [], []
            
        context_str = "\n".join([f"- [{doc[2]}] {doc[1]}" for doc in relevant_docs])

        try:
            system_prompt = (
                "Sen uzman bir klinik asistanısın. Yalnızca aşağıdaki KLİNİK REHBERLER metnine dayanarak cevap ver.\n"
                "Kurallar:\n"
                "1. Hekimin sorduğu ilacı tespit et ve rehberde yalnızca o ilaca ait olan bilgileri kullan.\n"
                "2. Başka ilaçların verilerini veya dozlarını araya kesinlikle karıştırma.\n"
                "3. Düşünce sürecini, iç monologları kesinlikle çıktıya yazma. Doğrudan ve net bir medikal yanıt üret."
            )
            
            user_prompt = f"KLİNİK REHBERLER:\n{context_str}\n\nHASTA BİLGİLERİ:\n{patient_data}\n\nSORU:\n{query}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = None

            for attempt in range(3):
                try:
                    response = self.chat_client.complete_chat(messages=messages)
                    break
                except Exception as inner_e:
                    if attempt == 2:
                        raise inner_e
                    time.sleep(2)
            
            if not response or (hasattr(response, 'error') and response.error):
                raise Exception(getattr(response, 'error', 'Model yanıt vermedi.'))
                
            final_response = response.choices[0].message.content
            
            if not final_response:
                return "⚠️ Yanıt oluşturulamadı.", relevant_docs, []

            safety_warnings = self.validate_dosage_safety(crcl_value)
            if safety_warnings:
                warning_block = "\n\n".join(safety_warnings)
                final_response = f"{warning_block}\n\n{final_response}"

            questions = self.generate_follow_up_questions(final_response)

            return final_response, relevant_docs, questions

        except Exception as e:
            error_msg = str(e)
            if "cancelled" in error_msg.lower() or "timeout" in error_msg.lower() or "allocate" in error_msg.lower():
                return "⚠️ **Yerel Model Yoğunluğu:** Model ilk yüklemede veya bellek ayrımında gecikti. Lütfen sorunuzu hemen tekrar gönderin (ikinci denemede önbellek hazır olacağı için yanıt alınacaktır).", relevant_docs, []
            return f"⚠️ Hata oluştu: {error_msg}", relevant_docs, []