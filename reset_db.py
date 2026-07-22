# reset_db.py
#
# appointments tablosundaki TÜM randevu kayıtlarını siler (tabloyu sıfırlar).
# Tabloyu silmez, sadece içini boşaltır — uygulama tekrar çalıştığında
# tablo zaten var olduğu için sorun çıkmaz.
#
# DİKKAT: Bu işlem geri alınamaz. Tüm randevular kalıcı olarak silinir.
#
# Kullanım:
#   export DATABASE_URL="postgresql://kullanici_adi:sifre@host:5432/veritabani_adi"
#   python reset_db.py

import os
import sys

import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("HATA: DATABASE_URL ortam değişkeni tanımlı değil.")
    sys.exit(1)

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

onay = input(
    "Bu işlem 'appointments' tablosundaki TÜM kayıtları kalıcı olarak silecek.\n"
    "Devam etmek istediğinize emin misiniz? (evet yazıp Enter'a basın): "
)
if onay.strip().lower() != "evet":
    print("İptal edildi, hiçbir şey silinmedi.")
    sys.exit(0)

conn = psycopg2.connect(DATABASE_URL, sslmode="require")
try:
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE appointments")
    conn.commit()
    print("Tamamlandı: appointments tablosu sıfırlandı, tüm kayıtlar silindi.")
except Exception as e:
    conn.rollback()
    print(f"HATA, işlem geri alındı: {e}")
    sys.exit(1)
finally:
    conn.close()
