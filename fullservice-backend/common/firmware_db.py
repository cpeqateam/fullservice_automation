"""
Firmware veritabanı erişimi — Marka / Model / Firmware combobox'larını besler.

GRK'daki `app/database.py` + `app/controllers/device_controller.py` mantığının
FULL Servis sunucusu (Linux) için sadeleştirilmiş portudur. Uzak PostgreSQL'e
(cpeqadb) SSL ile bağlanır ve `grk_firmware` tablosundan distinct marka/model/
sürüm listelerini okur.

Tasarım kararı: bağlantı kurulamazsa uygulama ÇÖKMEZ — `engine = None` kalır ve
sorgu fonksiyonları RuntimeError fırlatır. Sunucu endpoint'i bunu 503'e çevirir,
frontend de combobox'ları serbest-metin girişine düşürür (GRK ile aynı davranış).

Sertifikalar `common/config.py:CERT_DIR` (varsayılan: fullservice-backend/certs/)
altında aranır: ca.crt, client.crt, client.key. Bunlar repoya KONULMAZ (gizli).
"""
from __future__ import annotations

import os

from common.config import CERT_DIR, get_secret

# Bağlantı adresi (cpeqadb) — SIR: koda konmaz. Önce ortam değişkeni, yoksa
# gitignore'lu secrets.json'dan okunur (FS_FIRMWARE_DB_URL). Tanımlı değilse boş
# kalır → engine=None; combobox serbest-metne düşer (uygulama çökmez).
DB_URL = get_secret("FS_FIRMWARE_DB_URL")

engine = None        # Bağlantı kurulursa SQLAlchemy Engine; aksi halde None
SessionLocal = None  # Oturum fabrikası


def _libpq_safe_path(path: str) -> str:
    """
    libpq (psycopg2) sertifika dosya yollarını işletim sisteminin ANSI kod
    sayfasıyla açar; Windows'ta yol Türkçe/ASCII-dışı karakter içeriyorsa
    (örn. "Masaüstü") dosya VAR olsa bile "does not exist" hatası verir.

    Çözüm: ASCII-dışı yolu Windows kısa-yol (8.3) biçimine çevirir — bu daima
    ASCII'dir. Kısa-yol üretilemezse (8.3 kapalı bir disk vb.) sertifikayı geçici
    ASCII bir klasöre kopyalayıp oranın yolunu döner. ASCII yollar olduğu gibi
    kalır; Linux/macOS bu fonksiyondan etkilenmez.
    """
    if not path or path.isascii():
        return path

    if os.name == "nt":
        try:
            import ctypes
            from ctypes import create_unicode_buffer
            buf = create_unicode_buffer(1024)
            n = ctypes.windll.kernel32.GetShortPathNameW(path, buf, 1024)
            if n and buf.value and buf.value.isascii() and os.path.exists(buf.value):
                return buf.value
        except Exception:
            pass

    # Son çare: ASCII-güvenli geçici klasöre kopyala
    try:
        import shutil
        import tempfile
        safe_dir = os.path.join(tempfile.gettempdir(), "fs_certs")
        os.makedirs(safe_dir, exist_ok=True)
        dest = os.path.join(safe_dir, os.path.basename(path))
        shutil.copyfile(path, dest)
        return dest
    except Exception:
        return path


try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    cert_dir = os.path.abspath(CERT_DIR)
    ssl_args = {
        "sslmode":         "verify-ca",
        "sslrootcert":     _libpq_safe_path(os.path.join(cert_dir, "ca.crt")),
        "sslcert":         _libpq_safe_path(os.path.join(cert_dir, "client.crt")),
        "sslkey":          _libpq_safe_path(os.path.join(cert_dir, "client.key")),
        "connect_timeout": 5,
    }
    engine = create_engine(DB_URL, pool_pre_ping=True, connect_args=ssl_args)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:  # sqlalchemy yoksa veya bağlantı kurulamazsa
    print(f"[FIRMWARE_DB] Veritabani baglantisi yapilandirilamadi: {e}")
    engine = None
    SessionLocal = None


def db_available() -> bool:
    """Sertifikalar + bağlantı havuzu hazır mı?"""
    return SessionLocal is not None


def _query(sql: str, params: dict | None = None) -> list:
    """Tek sütunlu SELECT çalıştırıp ilk sütun değerlerini liste olarak döner."""
    if SessionLocal is None:
        raise RuntimeError("Firmware DB baglantisi yok (engine=None).")
    from sqlalchemy import text
    db = SessionLocal()
    try:
        rows = db.execute(text(sql), params or {}).fetchall()
        return [r[0] for r in rows if r[0] is not None]
    finally:
        db.close()


def get_brands() -> list[str]:
    return _query(
        "SELECT DISTINCT brand FROM firmware "
        "WHERE brand IS NOT NULL ORDER BY brand"
    )


def get_models(brand: str) -> list[str]:
    return _query(
        "SELECT DISTINCT model FROM firmware "
        "WHERE brand = :b AND model IS NOT NULL ORDER BY model",
        {"b": brand},
    )


def get_versions(brand: str, model: str) -> list[str]:
    return _query(
        "SELECT DISTINCT firmware_version FROM firmware "
        "WHERE brand = :b AND model = :m AND firmware_version IS NOT NULL "
        "ORDER BY firmware_version",
        {"b": brand, "m": model},
    )
