import os
import time
import streamlit as st
import database
from rag_engine import RAGEngine

st.set_page_config(page_title="Klinik Karar Destek Sistemi", layout="wide")

@st.cache_resource
def init_system():
    database.init_db()
    engine = RAGEngine()
    if os.path.exists("data") and os.listdir("data"):
        count = engine.ingest_all_documents("data")
        print(f"[+] Otomatik yükleme: Toplam {count} parça veritabanına işlendi.")
    return engine  
engine = init_system()

with st.sidebar:
    
    st.header(" Geçmiş Vakalar")
    if st.button("➕ Yeni Konsültasyon", use_container_width=True):
        st.session_state.session_id = str(time.time())
        st.session_state.messages = []
        st.rerun()
    
    sessions = database.list_all_sessions()
    selected_session = st.selectbox(
        "Eski vakayı yükle:", 
        sessions, 
        format_func=lambda x: f"{x[2]} (Hasta: {x[1]})" if x[1] else f"{x[2]} - Oturum"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Vakayı Yükle", use_container_width=True):
            if selected_session:
                st.session_state.session_id = selected_session[0]
                st.session_state.messages = database.get_chat_session(selected_session[0])
                st.rerun()
    with col2:
        if st.button(" Vakayı Sil", use_container_width=True):
            if selected_session:
                database.delete_chat_session(selected_session[0])
                st.success("Vaka silindi!")
                st.session_state.session_id = str(time.time())
                st.session_state.messages = []
                st.rerun()

    st.markdown("---")
    st.header(" Hasta Parametreleri")
    patient_id = st.text_input("Hasta ID (Örn: H-1042)", value="H-1042")
    age_str = st.text_input("Yaş", value="65")
    crcl_str = st.text_input("CrCl Değeri (mL/dk)", value="20.0")
    intub_days_str = st.text_input("Entübasyon Süresi (Gün)", value="5")
    symptoms = st.text_area("Semptomlar ve Bulgular", value="ateş, pürülan balgam, lökositoz")
    
    try:
        age, crcl, intub_days = int(age_str), float(crcl_str), int(intub_days_str)
    except ValueError:
        age, crcl, intub_days = 65, 20.0, 5

    if st.button("Verileri Sisteme Kaydet", use_container_width=True):
        database.save_patient(patient_id, age, crcl, intub_days, symptoms)
        st.success("Hasta verileri kaydedildi!")

    st.markdown("---")
    st.header("📂 PDF/TXT Rehber Yükle")
    uploaded_file = st.file_uploader("Klinik rehber seç", type=["pdf", "txt", "json"])
    
    if uploaded_file and st.button("Rehberi İşle", use_container_width=True):
        os.makedirs("data", exist_ok=True)
        with open(os.path.join("data", uploaded_file.name), "wb") as f:
            f.write(uploaded_file.getbuffer())
        count = engine.ingest_all_documents("data")
        database.add_to_library(uploaded_file.name, category="Klinik Rehber")
        st.success(f"Başarılı! {count} parça eklendi.")
        time.sleep(1)
        st.rerun()  

    st.markdown("---")
    st.header(" Kütüphane Arşivi")
    lib_docs = database.get_library_documents()

    if lib_docs:
        for doc in lib_docs:
            st.caption(f"📄 **{doc[0]}**\n_Kategori: {doc[1]} | Tarih: {doc[2][:10]}_")
    else:
        st.info("Henüz kütüphaneye eklenen rehber yok.")

st.title("⚕️ Yoğun Bakım Ampirik Tedavi Asistanı")

if "session_id" not in st.session_state:
    st.session_state.session_id = str(time.time())
if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if query := st.chat_input("Konsültasyon notunuzu yazın..."):
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    patient_data = f"Hasta ID: {patient_id}, Yaş: {age}, CrCl: {crcl}, Semptomlar: {symptoms}"
    with st.spinner("⏳ Yerel model RAG veritabanını tarıyor ve yanıt üretiyor..."):
        answer, docs, questions = engine.answer_query(patient_data, query, f"{symptoms} {query}", crcl_value=crcl)
        
    with st.chat_message("assistant"):
        st.markdown(answer)

        if docs:
            unique_sources = set([doc[2] for doc in docs]) 
            st.caption(f"📚 **Kullanılan Rehber(ler):** {', '.join(unique_sources)}")

    st.session_state.messages.append({"role": "assistant", "content": answer})
    
    database.save_chat_session(st.session_state.session_id, patient_id, st.session_state.messages)
