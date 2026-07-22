# app.py
# Karahan Optik — Randevu Backend (Python / Flask + PostgreSQL)
#
# webdeneme.html (randevu formu) ile admingiriş.html (admin paneli) arasında
# PostgreSQL veritabanı üzerinden köprü kurar. HTML/CSS dosyalarına dokunulmaz,
# API sözleşmesi (endpoint'ler ve JSON alan adları) eskisiyle birebir aynıdır.

import os
import time
import random
import string
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from psycopg2.pool import SimpleConnectionPool
from flask import Flask, jsonify, request, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, static_folder=None)

# ---- Veritabanı bağlantısı ----
# DATABASE_URL ortam değişkeni Railway/Render/Heroku gibi platformlarda
# PostgreSQL eklendiğinde otomatik olarak sağlanır.
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL ortam değişkeni bulunamadı. "
        "Barındırma panelinden bir PostgreSQL veritabanı ekleyip "
        "DATABASE_URL değişkenini tanımlamanız gerekiyor."
    )

# Bazı sağlayıcılar (ör. Heroku) 'postgres://' önekini kullanır,
# psycopg2 ise 'postgresql://' bekler.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Küçük/orta trafik için yeterli, hafif bir bağlantı havuzu.
pool = SimpleConnectionPool(1, 10, dsn=DATABASE_URL, sslmode="require")


@contextmanager
def get_conn():
    conn = pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


def init_db():
    with get_conn() as conn:
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


def generate_id():
    ts = format(int(time.time() * 1000), "x")
    rnd = "".join(random.choices(string.ascii_lowercase + string.digits, k=5))
    return ts + rnd


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def row_to_dict(row):
    return dict(row)


init_db()


# ---- Statik dosyalar (HTML/CSS olduğu gibi sunulur) ----
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "webdeneme.html")


@app.route("/admin")
def admin():
    return send_from_directory(BASE_DIR, "admingiriş.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(BASE_DIR, filename)


# ---- API ROTALARI ----

# Tüm randevuları getir (admin paneli bunu okur)
@app.route("/api/appointments", methods=["GET"])
def get_appointments():
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM appointments ORDER BY olusturma DESC")
            rows = cur.fetchall()
    return jsonify([row_to_dict(r) for r in rows])


# Yeni randevu ekle (webdeneme.html formu bunu çağırır)
@app.route("/api/appointments", methods=["POST"])
def add_appointment():
    yeni_randevu = request.get_json(force=True) or {}

    if not yeni_randevu.get("id"):
        yeni_randevu["id"] = generate_id()
    if not yeni_randevu.get("durum"):
        yeni_randevu["durum"] = "bekliyor"
    if not yeni_randevu.get("olusturma"):
        yeni_randevu["olusturma"] = now_iso()

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                """
                INSERT INTO appointments (id, tarih, saat, sebep, ad, telefon, durum, olusturma)
                VALUES (%(id)s, %(tarih)s, %(saat)s, %(sebep)s, %(ad)s, %(telefon)s, %(durum)s, %(olusturma)s)
                RETURNING *
                """,
                {
                    "id": yeni_randevu.get("id"),
                    "tarih": yeni_randevu.get("tarih"),
                    "saat": yeni_randevu.get("saat"),
                    "sebep": yeni_randevu.get("sebep"),
                    "ad": yeni_randevu.get("ad"),
                    "telefon": yeni_randevu.get("telefon"),
                    "durum": yeni_randevu.get("durum"),
                    "olusturma": yeni_randevu.get("olusturma"),
                },
            )
            created = cur.fetchone()
    return jsonify(row_to_dict(created)), 201


# Randevu güncelle (admin paneli durum değiştirme için kullanır)
@app.route("/api/appointments/<id>", methods=["PUT"])
def update_appointment(id):
    updates = request.get_json(force=True) or {}
    if not updates:
        return jsonify({"error": "Güncellenecek alan gönderilmedi"}), 400

    # Sadece bilinen kolonların güncellenmesine izin ver (SQL injection'a karşı güvenli).
    allowed_columns = {"tarih", "saat", "sebep", "ad", "telefon", "durum", "olusturma"}
    set_clauses = []
    values = {}
    for key, value in updates.items():
        if key in allowed_columns:
            set_clauses.append(f"{key} = %({key})s")
            values[key] = value

    if not set_clauses:
        return jsonify({"error": "Geçerli bir alan gönderilmedi"}), 400

    values["id"] = id

    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"UPDATE appointments SET {', '.join(set_clauses)} WHERE id = %(id)s RETURNING *",
                values,
            )
            item = cur.fetchone()

    if item is None:
        return jsonify({"error": "Randevu bulunamadı"}), 404
    return jsonify(row_to_dict(item))


# Randevu sil (admin paneli silme butonu için kullanır)
@app.route("/api/appointments/<id>", methods=["DELETE"])
def delete_appointment(id):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM appointments WHERE id = %s", (id,))
    return jsonify({"ok": True})


if __name__ == "__main__":
    print("Sunucu çalışıyor: http://localhost:3000")
    print("Admin paneli:    http://localhost:3000/admin")
    app.run(host="0.0.0.0", port=3000, debug=False)
