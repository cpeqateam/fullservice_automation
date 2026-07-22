# Robot Test Otomasyonu — Entegrasyon Rehberi

> Bu belge, **Robot Test Otomasyonu**'nu geliştiren içindir.
> FULL Servis'teki hazır yapıları (kullanıcı girişi, sertifikalı DB bağlantısı,
> FTP yükleme, DB'ye sonuç yazma) kendi sistemine nasıl entegre edeceğini anlatır.
>
> **Özet:** Aşağıdaki 5 dosyaya bak. Temel olan **`firmware_db.py`** (bağlantı + sertifika);
> `auth_service`, `ftp_service`, `db_service` hepsi onun üstüne kuruludur.

---

## İnceleyeceğin dosyalar (özet tablo)

| # | Konu | Dosya | Ne işe yarar |
|---|------|-------|--------------|
| 0 | **Temel: DB bağlantısı + sertifika** | `common/firmware_db.py` + `common/config.py` | Sertifikalı PostgreSQL bağlantısı. Login ve DB-yazma bunu kullanır. |
| 1 | Kullanıcı girişi | `server/auth_service.py` | `grk_users` tablosundan login. |
| 2 | FTP'ye dosya aktarma | `server/ftp_service.py` | Logları FTPS ile yükler. |
| 3 | Test verisini DB'ye yazma | `server/db_service.py` | Sonuçları tabloya yazma kalıbı. |

**Gerekli Python paketleri:** `sqlalchemy`, `psycopg2` (DB için), standart `ftplib` (FTP için).

---

## 0 · Temel — DB Bağlantısı + Sertifika
📄 [`common/firmware_db.py`](fullservice-backend/common/firmware_db.py) · [`common/config.py`](fullservice-backend/common/config.py)

Her şeyin altında bu var: login de, DB'ye yazma da bu tek bağlantıyı (`SessionLocal`) kullanır. **Kopyalanacak asıl kalıp budur.**

| Ne | Yer | Açıklama |
|----|-----|----------|
| Bağlantı adresi | [firmware_db.py:23-26](fullservice-backend/common/firmware_db.py#L23-L26) | `DB_URL` (cpeqadb). ⚠️ Kimlik koda gömülü — sen **ortam değişkeninden** ver (`FS_FIRMWARE_DB_URL`), koda yazma. |
| SSL / sertifika ayarı | [firmware_db.py:74-83](fullservice-backend/common/firmware_db.py#L74-L83) | `sslmode=verify-ca` + `ca.crt` / `client.crt` / `client.key`. `engine` + `SessionLocal` burada kurulur. |
| Sertifika klasörü | [config.py:39](fullservice-backend/common/config.py#L39) | `CERT_DIR = <proje_kökü>/certs/`. Sertifikalar burada aranır. | Bu dosyaları ben flash bellek ile sana vereceğim. 
| Windows Türkçe yol düzeltmesi | [firmware_db.py:32-67](fullservice-backend/common/firmware_db.py#L32-L67) | `_libpq_safe_path` — yol "Masaüstü" gibi ASCII-dışı karakter içerirse gerekir (Windows'ta libpq sertifikayı bulamıyor). |

---

## 1 · Kullanıcı Girişi (login)
📄 [`server/auth_service.py`](fullservice-backend/server/auth_service.py)

| Ne | Yer | Açıklama |
|----|-----|----------|
| Giriş doğrulama | [auth_service.py:41-80](fullservice-backend/server/auth_service.py#L41-L80) | `login()` — `grk_users` tablosunu `firmware_db.SessionLocal` ile sorgular. |
| Şifre kontrolü | [auth_service.py:23-38](fullservice-backend/server/auth_service.py#L23-L38) | `_check_password` — bcrypt → md5 → sha256 → düz metin. |
| Endpoint | `server/main.py` → `POST /api/login` | HTTP ucu. |

> **Not:** `grk_users` tablosu ortaktır; ekstra tablo açmaya gerek yok, doğrudan okunur.
> Tek ihtiyacın **(0)'daki bağlantıdır**.

---

## 2 · FTP'ye Dosya Aktarma
📄 [`server/ftp_service.py`](fullservice-backend/server/ftp_service.py)

| Ne | Yer | Açıklama |
|----|-----|----------|
| Bağlantı ayarları | [ftp_service.py:32-36](fullservice-backend/server/ftp_service.py#L32-L36) | `FTP_ADDRESSES/PORT/USER/PASS` (env ile override). ⚠️ `testuser/testpass` default'u gömülü — gerçek kimliği **env'den** ver. |
| TLS bağlamı | [ftp_service.py:85-97](fullservice-backend/server/ftp_service.py#L85-L97) | `_make_ssl_context` — `certs/ca.crt` kullanır. |
| Bağlan (önce TLS, olmazsa düz) | [ftp_service.py:100+](fullservice-backend/server/ftp_service.py#L100) | `_connect_ftps_secure` / `_connect_ftp_plain`. |
| Yükleme + klasör açma + arka plan | ftp_service.py | `_ensure_dir_recursive`, `upload_files_to_ftp`, `upload_async`. |
| Klasör yapısı | [ftp_service.py:67-72](fullservice-backend/server/ftp_service.py#L67-L72) | `build_target_dir` — bu **bizim** şemamız; sen **kendi** klasör yapını tanımla. |

> **Önemli:** FTP de aynı `certs/ca.crt`'yi kullanır → **tek `certs/` klasörü** hem DB'ye hem FTP'ye yeter.

---

## 3 · Test Verisini DB'ye Yazma
📄 [`server/db_service.py`](fullservice-backend/server/db_service.py)

| Ne | Yer | Açıklama |
|----|-----|----------|
| Tablo adları (tek yer) | [db_service.py:26-33](fullservice-backend/server/db_service.py#L26-L33) | Kendi tablolarını burada tanımla. |
| Yazma kalıbı (örnek al) | [db_service.py:146-249](fullservice-backend/server/db_service.py#L146-L249) | `save_ping` / `save_iperf` / `save_wifi` — parametreli `INSERT` (SQLAlchemy `text`). |
| Oturum satırı | db_service.py | `create_session` / `update_session_end`. |
| Tip yardımcıları | db_service.py | `_f/_i/_s` — None-güvenli dönüştürme. |

> **Yapılacak:** cpeqadb'de sana ait tablolar açılır (biz `copy_` tablolarını nasıl açtıysak öyle),
> sonra bu dosyadaki fonksiyonları örnek alıp kendi `INSERT`'lerini yazarsın. Hepsi
> `firmware_db.SessionLocal`'ı ((0)) kullanır.

---

## 🔐 Sertifika Kurulumu (her iki iş için ortak)

Gereken 3 dosya: **`ca.crt`**, **`client.crt`**, **`client.key`**

1. Flash bellekle al → projende bir **`certs/`** klasörüne koy.
2. Kod sertifikaları `CERT_DIR` (= proje kökü/`certs/`) altında arar; kendi köküne göre ayarla.
3. **Linux/macOS'ta zorunlu:** `chmod 600 certs/client.key` — libpq herkese-okunur key'i reddeder, yoksa DB bağlanmaz.
4. **Aynı sertifikalar** hem DB (PostgreSQL SSL) hem FTP (FTPS) için geçerlidir → tek klasör yeter.
5. Yeni sertifika **üretme**; ekibin verdiği cpeqadb sertifikalarının aynısını kullan.

---

## ⚠️ Güvenlik Notu

- Sertifikalar ve kimlik bilgileri **sırdır**: GitHub'a **konmaz** (repo'nda `.gitignore`'a `certs/` ekle), USB'den iş bitince sil.
- `firmware_db.py`'deki `DB_URL` ve `ftp_service.py`'deki FTP kullanıcı/şifresi koda gömülü **default**'lardır. Örnek al ama **kendi tarafında ortam değişkeninden oku, koda yazma.**
