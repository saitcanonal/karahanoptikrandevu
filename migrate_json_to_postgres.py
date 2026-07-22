# migrate_json_to_postgres.py
#
# Eski appointments.json dosyasındaki randevuları PostgreSQL'e aktarır.
# Sadece bir kez, geçiş yaparken çalıştırılır.
#
# Kullanım:
#   1) DATABASE_URL ortam değişkenini ayarlayın (yerelde test ediyorsanız):
#        export DATABASE_URL="postgresql://kullanici:sifre@host:5432/dbadi"
#   2) appointments.json dosyasını bu script ile aynı klasöre koyun.
#   3) python migrate_json_to_postgres.py

import json
import os
import sys

import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("HATA: DATABASE_URL ortam değişkeni tanımlı değil.")
    sys.exit(1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

JSON_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "appointments.json")

if not os.path.exists(JSON_PATH):
    print(f"appointments.json bulunamadı: {JSON_PATH}")
    sys.exit(1)

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

if not data:
    print("appointments.json boş, aktarılacak randevu yok.")
    sys.exit(0)

conn = psycopg2.connect(DATABASE_URL, sslmode="require")
conn.autocommit = False

try:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS appointments (
                id TEXT PRIMARY KEY,
                tarih TEXT,
                saat TEXT,
                sebep TEXT,
                ad TEXT,
                telefon TEXT,
                durum TEXT DEFAULT 'bekliyor',
                olusturma TEXT
            )
            """
        )

        aktarilan = 0
        for r in data:
            cur.execute(
                """
                INSERT INTO appointments (id, tarih, saat, sebep, ad, telefon, durum, olusturma)
                VALUES (%(id)s, %(tarih)s, %(saat)s, %(sebep)s, %(ad)s, %(telefon)s, %(durum)s, %(olusturma)s)
                ON CONFLICT (id) DO NOTHING
                """,
                {
                    "id": r.get("id"),
                    "tarih": r.get("tarih"),
                    "saat": r.get("saat"),
                    "sebep": r.get("sebep"),
                    "ad": r.get("ad"),
                    "telefon": r.get("telefon"),
                    "durum": r.get("durum", "bekliyor"),
                    "olusturma": r.get("olusturma"),
                },
            )
            aktarilan += 1

    conn.commit()
    print(f"Tamamlandı: {aktarilan} randevu PostgreSQL'e aktarıldı.")
except Exception as e:
    conn.rollback()
    print(f"HATA, işlem geri alındı: {e}")
    sys.exit(1)
finally:
    conn.close()
