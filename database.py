import sqlite3
import json
import math

DB_NAME = "database.db"

def init_db():
    """SQLite veritabanını RAG, Hasta kayıtları, Kütüphane ve Sohbet Geçmişi için hazırlar."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            source TEXT NOT NULL,
            embedding TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS patients (
            patient_id TEXT PRIMARY KEY,
            age INTEGER,
            crcl_value REAL,
            intubation_days INTEGER,
            symptoms TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            category TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            patient_id TEXT,
            messages TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()


def add_to_library(filename, category="Genel"):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT OR IGNORE INTO library (filename, category) VALUES (?, ?)', (filename, category))
        conn.commit()
    except sqlite3.Error as e:
        print(f"Kütüphaneye ekleme hatası: {e}")
    conn.close()

def save_chat_session(session_id, patient_id, messages_list):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
  
    cursor.execute('INSERT INTO chat_history (session_id, patient_id, messages) VALUES (?, ?, ?)', 
                   (session_id, patient_id, json.dumps(messages_list)))
    conn.commit()
    conn.close()


def save_patient(patient_id, age, crcl_value, intubation_days, symptoms):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO patients (patient_id, age, crcl_value, intubation_days, symptoms)
        VALUES (?, ?, ?, ?, ?)
    ''', (patient_id, age, crcl_value, intubation_days, symptoms))
    conn.commit()
    conn.close()

def save_document(content, source, embedding_vector):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        'INSERT INTO documents (content, source, embedding) VALUES (?, ?, ?)',
        (content, source, json.dumps(embedding_vector))
    )
    conn.commit()
    conn.close()

def clear_documents():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM documents')
    conn.commit()
    conn.close()

def cosine_similarity(v1, v2):
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)

def search_documents(query_vector, top_k=3, min_similarity=0.0):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT content, source, embedding FROM documents')
    rows = cursor.fetchall()
    conn.close()

    results = []
    for content, source, emb_str in rows:
        doc_vector = json.loads(emb_str)
        sim_score = cosine_similarity(query_vector, doc_vector)
        if sim_score >= min_similarity:
            results.append((sim_score, content, source))

    results.sort(key=lambda x: x[0], reverse=True)
    return results[:top_k]

def get_chat_session(session_id):
    """Belirli bir oturumun mesaj geçmişini getirir."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT messages FROM chat_history WHERE session_id = ? ORDER BY timestamp DESC LIMIT 1', (session_id,))
    row = cursor.fetchone()
    conn.close()
    return json.loads(row[0]) if row else []

def list_all_sessions():
    """Tüm geçmiş oturumları tarih ve Hasta ID bilgisiyle listeler."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT session_id, patient_id, timestamp FROM chat_history GROUP BY session_id ORDER BY timestamp DESC')
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_chat_session(session_id):
    """Belirli bir sohbet oturumunu veritabanından siler."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM chat_history WHERE session_id = ?', (session_id,))
    conn.commit()
    conn.close()
    
def get_library_documents():
    """Kütüphanedeki tüm dokümanları listeler."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, category, upload_date FROM library ORDER BY upload_date DESC")
    rows = cursor.fetchall()
    conn.close()
    return rows