import os
import sqlite3
from datetime import datetime, timedelta

class LeadDatabase:
    def __init__(self, db_path="data/leads_history.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT,
                    city TEXT,
                    direct_phone TEXT,
                    source_website TEXT,
                    job_url TEXT UNIQUE,
                    created_at TIMESTAMP
                )
            """)
            conn.commit()

    def filter_and_save(self, raw_leads, retention_days=30):
        """
        Son 30 gün içinde kaydedilmemiş ve URL'si mükerrer olmayan 
        yeni firmaları veritabanına ekler ve sadece bu haftanın YENİ lead'lerini döner.
        """
        cutoff = datetime.now() - timedelta(days=retention_days)
        new_leads = []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for lead in raw_leads:
                company = (lead.get("company_name") or "").strip()
                city = (lead.get("city") or "").strip()
                job_url = (lead.get("job_url") or "").strip()
                source_site = (lead.get("source_website") or "").strip()

                if not company or len(company) < 2 or not city:
                    continue

                cursor.execute("""
                    SELECT id FROM leads 
                    WHERE (LOWER(company_name) = LOWER(?) AND LOWER(city) = LOWER(?) AND created_at >= ?)
                       OR job_url = ?
                """, (company, city, cutoff, job_url))
                
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO leads (company_name, city, direct_phone, source_website, job_url, created_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        company,
                        city,
                        lead.get("direct_phone", ""),
                        source_site,
                        job_url,
                        datetime.now()
                    ))
                    new_leads.append(lead)
            conn.commit()

        print(f"[*] Veritabanına {len(new_leads)} adet yeni tekil firma eklendi.")
        return new_leads

    def get_all_active_leads(self, retention_days=30):
        """
        Son 30 güne ait duplike olmayan tüm kurumsal lead'leri 
        kümülatif Excel raporu için veritabanından çeker.
        """
        cutoff = datetime.now() - timedelta(days=retention_days)
        active_leads = []

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT company_name, city, direct_phone, source_website, job_url 
                FROM leads 
                WHERE created_at >= ?
                GROUP BY LOWER(company_name), LOWER(city)
                ORDER BY created_at DESC
            """, (cutoff,))
            
            rows = cursor.fetchall()
            for row in rows:
                active_leads.append(dict(row))

        return active_leads
