import sqlite3
from datetime import datetime, timedelta

DB_PATH = "data/leads_history.db"

def init_db():
    import os
    os.makedirs("data", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT NOT NULL,
            city TEXT,
            source TEXT,
            job_title TEXT,
            job_url TEXT UNIQUE,
            direct_phone TEXT,
            enriched_phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def is_lead_recent(company_name: str, city: str, days_threshold=30) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cutoff_date = datetime.now() - timedelta(days=days_threshold)
    cursor.execute("""
        SELECT COUNT(*) FROM leads 
        WHERE LOWER(company_name) = LOWER(?) 
        AND LOWER(city) = LOWER(?) 
        AND created_at >= ?
    """, (company_name.strip(), city.strip(), cutoff_date))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def save_lead(lead: dict):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT OR IGNORE INTO leads 
            (company_name, city, source, job_title, job_url, direct_phone, enriched_phone, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            lead.get("company_name"),
            lead.get("city"),
            lead.get("source"),
            lead.get("job_title"),
            lead.get("job_url"),
            lead.get("direct_phone"),
            lead.get("enriched_phone"),
            datetime.now()
        ))
        conn.commit()
    except Exception as e:
        print(f"DB Kayıt Hatası: {e}")
    finally:
        conn.close()