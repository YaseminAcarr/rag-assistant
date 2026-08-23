# ⚕️ Yoğun Bakım Ampirik Tedavi Asistanı (RAG Destekli Klinik Karar Destek Sistemi)

Bu proje, yoğun bakım ünitelerinde yatan kritik hastalar için **Microsoft Foundry Local** ve **RAG (Retrieval-Augmented Generation)** mimarisini kullanarak kanıta dayalı ampirik antibiyotik ve dozaj önerileri sunan yerel bir Yapay Zeka destekli klinik karar destek sistemidir.

## 🚀 Projenin Temel Özellikleri
* **Yerel ve Güvenli Çalışma:** Verileriniz ve yapay zeka modelleri (`Phi-3.5-mini-instruct` ve `Qwen3-embedding`) tamamen yerel ortamda (Microsoft Foundry Local SDK ile) çalışır, dışarıya veri sızdırmaz.
* **Jenerik Güvenlik Kalkanı:** Hastanın böbrek fonksiyonlarına (`CrCl` - Kreatinin Klirensi) bağlı olarak otomatik dinamik uyarı mekanizması barındırır.
* **Semantik RAG Motoru:** Klinik rehberleri (`.txt`, `.json`) anlamsal parçalara ayırarak veritabanında saklar ve en doğru tıbbi kaynağı eşleştirir.
* **Geçmiş Vaka Yönetimi:** Geçmiş konsültasyon oturumlarını saklama, yükleme ve silme imkanı sunar.
* **Dinamik Rehber Yükleme:** Arayüz üzerinden yeni klinik rehber PDF/TXT dosyaları yükleyerek bilgi bankasını genişletebilirsiniz.

## 🛠️ Kullanılan Teknolojiler
* **Python** (FastAPI altyapısı ve mantıksal katman)
* **Streamlit** (İnteraktif web arayüzü)
* **Microsoft Foundry Local SDK** (`Phi-3.5-mini-instruct` LLM & Embedding modelleri)
* **SQLite & Vector Database** (Klinik rehberler ve oturum yönetimi)

---
## 📂 Proje Dizin Yapısı
```text
rag-assistant/
│
├── data/                       # Klinik rehber dokümanları (.txt, .pdf, .json)
├── venv/                       # Python sanal ortam klasörü
├── app.py                      # Streamlit arayüz ve akış yönetimi
├── rag_engine.py               # RAG mantığı, LLM ve Embedding istemci yönetimi
├── database.py                 # SQLite veritabanı, vaka ve oturum işlemleri
├── document_loader.py          # PDF/TXT/JSON okuma ve semantik parçalama modülü
├── auto_extractor.py           # Otonom klinik veri çıkarım betiği
├── setup_models.py             # Yerel model indirme ve doğrulama betiği
├── requirements.txt            # Python bağımlılık listesi
└── README.md                   # Proje dokümantasyonu
```
## ⚙️ Kurulum ve Çalıştırma

Projeyi yerel makinenizde çalıştırmak için şu adımları izleyin:

1. **Repoyu Klonlayın:**
```bash
git clone https://github.com/YaseminAcarr/rag-assistant.git
cd rag-assistant
```
2. **Sanal Ortam (venv) Oluşturun ve Aktifleştirin:**
```bash
python -m venv venv
# Windows için:
.\venv\Scripts\Activate
# Mac/Linux için:
source venv/bin/activate
```
3. **Gerekli Kütüphaneleri Yükleyin:**
```bash
pip install -r requirements.txt
```
4. **Uygulamayı Başlatın:**
```bash
streamlit run app.py
```

### Yasal Uyarı: Bu proje, bir klinik karar destek prototipidir. Asistan tarafından sunulan ampirik tedavi ve dozaj önerileri tavsiye niteliğinde olup, nihai tıbbi kararlar her zaman uzman hekimin sorumluluğundadır.