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
import os

from common.config import CERT_DIR

# Bağlantı adresi — GRK ile aynı cpeqadb. Ortam değişkeni ile override edilebilir.
DB_URL = os.environ.get(
    "FS_FIRMWARE_DB_URL",
    "postgresql://cpeqateam:cpeqateam@78.186.148.93:4749/cpeqadb",
)

engine = None        # Bağlantı kurulursa SQLAlchemy Engine; aksi halde None
SessionLocal = None  # Oturum fabrikası

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker

    cert_dir = os.path.abspath(CERT_DIR)
    ssl_args = {
        "sslmode":         "verify-ca",
        "sslrootcert":     os.path.join(cert_dir, "ca.crt"),
        "sslcert":         os.path.join(cert_dir, "client.crt"),
        "sslkey":          os.path.join(cert_dir, "client.key"),
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
        "SELECT DISTINCT brand FROM grk_firmware "
        "WHERE brand IS NOT NULL ORDER BY brand"
    )


def get_models(brand: str) -> list[str]:
    return _query(
        "SELECT DISTINCT model FROM grk_firmware "
        "WHERE brand = :b AND model IS NOT NULL ORDER BY model",
        {"b": brand},
    )


def get_versions(brand: str, model: str) -> list[str]:
    return _query(
        "SELECT DISTINCT firmware_version FROM grk_firmware "
        "WHERE brand = :b AND model = :m AND firmware_version IS NOT NULL "
        "ORDER BY firmware_version",
        {"b": brand, "m": model},
    )
