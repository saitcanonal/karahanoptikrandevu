## ⚠️ ÖNEMLİ: Render hatasının sebebi ve güvenlik uyarısı

**Hatanın sebebi:** `app.py` ve `migrate_json_to_postgres.py` dosyalarında şu satır vardı:

```python
DATABASE_URL = os.environ.get("postgresql://kullanici:sifre@host/db")
```

`os.environ.get(...)` fonksiyonuna, ortam değişkeninin **adı** yerine yanlışlıkla
doğrudan bağlantı adresinin kendisi verilmiş. Yani kod, adı gerçekten
`postgresql://kullanici:sifre@host/db` olan bir ortam değişkeni arıyordu — böyle bir
değişken olamayacağı için her zaman boş dönüyor ve "DATABASE_URL bulunamadı" hatası
veriyordu. Bu sürümde düzeltildi:

```python
DATABASE_URL = os.environ.get("DATABASE_URL")
```

Artık Render panelinde **Environment** sekmesinden `DATABASE_URL` adında bir
değişken tanımlamanız yeterli; kod onu doğru şekilde okuyacak.

**Güvenlik uyarısı:** Eski dosyalarda veritabanı şifreniz kodun içine açıkça
yazılmıştı. Bu bilgi paylaşıldığı için artık güvenli sayılmaz. Render panelinden
PostgreSQL veritabanınızın şifresini/bağlantı bilgisini yenilemenizi (reset/rotate)
öneririz; ardından yeni `DATABASE_URL` değerini Environment sekmesine girin.

**Veritabanını sıfırlamak isterseniz:** Eklenen `reset_db.py` dosyası `appointments`
tablosundaki tüm kayıtları siler (tabloyu değil, sadece içindeki verileri):

```bash
export DATABASE_URL="postgresql://kullanici_adi:sifre@host:5432/veritabani_adi"
python reset_db.py
```

Script onay istiyor, yanlışlıkla çalıştırıp veri kaybetmezsiniz.

---

# Karahan Optik — Randevu Sistemi (PostgreSQL sürümü)

Bu sürümde `appointments.json` yerine **PostgreSQL** kullanılıyor. HTML dosyalarında
(`webdeneme.html`, `admingiriş.html`) hiçbir değişiklik yapılmadı; sadece backend
(`app.py`) veriyi dosya yerine veritabanında tutuyor. API endpoint'leri ve gönderilen/alınan
JSON alanları (`ad`, `telefon`, `tarih`, `saat`, `sebep`, `durum`, `id`, `olusturma`) birebir aynı
kaldığı için ön yüzde hiçbir kod değişikliği gerekmiyor.

## 1) Gerekli ortam değişkeni: DATABASE_URL

Uygulamanın çalışması için bir PostgreSQL veritabanı ve bağlantı adresi gerekiyor.

- **Railway / Render / Heroku gibi platformlarda:** Panelden "PostgreSQL ekle" dediğinizde
  `DATABASE_URL` değişkeni otomatik olarak projenize tanımlanır, ekstra bir şey yapmanıza
  gerek yok.
- **Kendi sunucunuzda / VPS'te:** Bir PostgreSQL kurup şu formatta bir bağlantı adresi
  oluşturmanız gerekir:

  ```
  postgresql://kullanici_adi:sifre@host:5432/veritabani_adi
  ```

  Bunu ortam değişkeni olarak tanımlayın:

  ```bash
  export DATABASE_URL="postgresql://kullanici_adi:sifre@host:5432/veritabani_adi"
  ```

Uygulama ilk açılışta `appointments` tablosunu **kendisi otomatik olarak oluşturur**,
elle bir SQL çalıştırmanıza gerek yok.

## 2) Kurulum

```bash
pip install -r requirements.txt
```

## 3) Yerelde çalıştırma

```bash
export DATABASE_URL="postgresql://kullanici_adi:sifre@host:5432/veritabani_adi"
python app.py
```

Tarayıcıda:
- Randevu formu: http://localhost:3000
- Admin paneli: http://localhost:3000/admin

## 4) Canlıya alma (Procfile hazır)

`Procfile` içeriği değişmedi, gunicorn ile aynı şekilde çalışır:

```
web: gunicorn app:app --bind 0.0.0.0:$PORT
```

Railway/Render'a deploy ederken tek yapmanız gereken **PostgreSQL eklentisini eklemek**;
`DATABASE_URL` otomatik geleceği için başka bir ayar gerekmez.

## 5) Eski appointments.json verisini aktarmak (opsiyonel)

Eğer müşteride eskiden beri biriken randevu kayıtları varsa (`appointments.json` dosyasında),
bunları PostgreSQL'e taşımak için **bir kereliğine** şunu çalıştırın:

```bash
export DATABASE_URL="postgresql://kullanici_adi:sifre@host:5432/veritabani_adi"
python migrate_json_to_postgres.py
```

Bu işlem `appointments.json`'daki tüm kayıtları veritabanına ekler, dosyanın kendisine
dokunmaz. Kayıt yoksa veya dosya bulunamazsa güvenle atlar.

## Neler değişti, neler değişmedi?

| | Eski | Yeni |
|---|---|---|
| Veri deposu | `appointments.json` dosyası | PostgreSQL veritabanı |
| API endpoint'leri | aynı | aynı |
| HTML/CSS dosyaları | — | **hiç dokunulmadı** |
| Eşzamanlı yazma güvenliği | zayıf (dosya kilidi yok) | veritabanı seviyesinde güvenli |
| Ölçeklenebilirlik | tek sunucu, tek dosya | çoklu sunucu/worker ile uyumlu |

`appointments.json` dosyasını artık projede tutmanıza gerek yok, ancak isterseniz
yedek olarak saklayabilirsiniz — uygulama artık ona dokunmuyor.
