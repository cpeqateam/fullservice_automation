"""
Kimlik doğrulama (FULL Servis, sunucu tarafı) — kullanıcı girişini doğrular.

GRK auth_controller.login mantığının sadeleştirilmiş portudur:
  • Kullanıcılar GRK ile AYNI tablodan (cpeqadb → grk_users) kontrol edilir.
  • Şifre formatları: bcrypt → MD5 → SHA256 → düz metin (eski kayıtlarla uyum).
  • DB erişilemese bile her zaman izin verilen VARSAYILAN hesap: cpeteam / cpeteam.

grk_users tablosu DB birleştirmesinde YENİDEN ADLANDIRILMADI (olduğu gibi kalıyor).
Bağlantı firmware_db.py'nin hazırladığı SessionLocal'ı (aynı SSL bağlantısı) kullanır.
"""
from __future__ import annotations

import hashlib

from common import firmware_db

# DB erişilemese bile DAİMA geçerli varsayılan hesap (kullanıcı isteri).
DEFAULT_USER = "cpeteam"
DEFAULT_PASS = "cpeteam"


def _check_password(plain: str, stored: str) -> bool:
    """Düz metin şifreyi DB'deki değerle karşılaştırır: bcrypt → MD5 → SHA256 → düz metin."""
    if stored is None:
        return False
    try:
        from passlib.context import CryptContext
        ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
        if ctx.verify(plain, stored):
            return True
    except Exception:
        pass
    if stored == hashlib.md5(plain.encode()).hexdigest():
        return True
    if stored == hashlib.sha256(plain.encode()).hexdigest():
        return True
    return plain == stored


def login(username: str, password: str) -> dict | None:
    """Başarılıysa kullanıcı bilgisi (dict), başarısızsa None döner.

    Sıra: (1) varsayılan cpeteam hesabı — DB gerektirmez, her zaman çalışır;
          (2) grk_users tablosu (DB)."""
    username = (username or "").strip()

    # 1) Varsayılan hesap — DB bağlantısı olmasa bile her daim geçerli
    if username == DEFAULT_USER and password == DEFAULT_PASS:
        return {
            "user_id": -1, "name": "CPE", "surname": "Team",
            "username": DEFAULT_USER, "email": None, "is_root": True, "default": True,
        }

    # 2) DB'den (grk_users) doğrula
    if firmware_db.SessionLocal is None:
        print("[AUTH] DB baglantisi yok — sadece varsayilan hesap (cpeteam) kullanilabilir.")
        return None

    from sqlalchemy import text
    db = firmware_db.SessionLocal()
    try:
        row = db.execute(text(
            "SELECT user_id, name, surname, username, email, password "
            "FROM users WHERE username = :u"
        ), {"u": username}).fetchone()
    except Exception as e:
        print(f"[AUTH] grk_users sorgu hatasi: {e}")
        return None
    finally:
        db.close()

    if not row or not _check_password(password, row.password or ""):
        return None

    return {
        "user_id": row.user_id, "name": row.name, "surname": row.surname,
        "username": row.username, "email": row.email,
        "is_root": row.username == "root", "default": False,
    }
