import os
import json
import pdfplumber

def load_text_file(file_path):
    """TXT dosyasından metin okur."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def load_pdf_file(file_path):
    """
    PDF dosyasındaki metinleri ve tabloları akıllıca okur.
    Tabloları satır ve sütun yapısını koruyarak çıkarır.
    """
    full_text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                full_text.append(page_text)
            
            tables = page.extract_tables()
            for table in tables:
                table_str = "\n".join([" | ".join([str(cell) if cell else "" for cell in row]) for row in table])
                full_text.append("\n[TABLO BAŞLANGICI]\n" + table_str + "\n[TABLO BİTİŞİ]\n")
                
    return "\n\n".join(full_text)

def semantic_chunking(text, source_name, max_length=300):
    """
    Metni karakter sayısına göre rastgele değil, 
    paragraf ve tablo sınırlarını (\n\n) koruyarak akıllıca böler.
    """
    chunks = []
    paragraphs = text.split('\n\n')
    
    current_chunk = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
            
        if len(current_chunk) + len(para) < max_length:
            current_chunk += para + "\n\n"
        else:
            if current_chunk:
                chunks.append({
                    "text": current_chunk.strip(),
                    "source": source_name
                })
            current_chunk = para + "\n\n"
            
    if current_chunk:
        chunks.append({
            "text": current_chunk.strip(),
            "source": source_name
        })

    return chunks

def load_all_documents(data_dir="data"):
    """Klasördeki tüm dosyaları (TXT, PDF, JSON) tarar ve semantik parçalara böler."""
    if not os.path.exists(data_dir):
        os.makedirs(data_dir, exist_ok=True)
        return []

    all_chunks = []
    for file_name in os.listdir(data_dir):
        file_path = os.path.join(data_dir, file_name)
        
        if file_name.endswith('.txt'):
            raw_text = load_text_file(file_path)
            chunks = semantic_chunking(raw_text, source_name=file_name)
            all_chunks.extend(chunks)
            print(f"  [OK] '{file_name}' (TXT) -> {len(chunks)} semantik parça.")
            
        elif file_name.endswith('.pdf'):
            raw_text = load_pdf_file(file_path)
            chunks = semantic_chunking(raw_text, source_name=file_name)
            all_chunks.extend(chunks)
            print(f"  [OK] '{file_name}' (PDF) -> {len(chunks)} semantik parça.")
            
        elif file_name.endswith('.json'):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                json_chunks = []
                for item in data:
                    semptom_str = ", ".join(item["semptomlar"])
                    text_block = f"[KLİNİK TEŞHİS VERİSİ]\nHastalık: {item['hastalik']}\nBelirtiler/Semptomlar: {semptom_str}\nUyarı: {item.get('klinik_uyari', '')}"
                    json_chunks.append({
                        "text": text_block,
                        "source": file_name
                    })
                all_chunks.extend(json_chunks)
                print(f"  [OK] '{file_name}' (JSON) -> {len(json_chunks)} yapılandırılmış parça.")

    return all_chunks