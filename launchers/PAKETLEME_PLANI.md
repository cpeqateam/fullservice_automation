# Tek-Tık Paketleme (Installer) Planı — PyInstaller

Amaç: Client makinelere **kaynak kod / Python / git çekmeden**, sadece **çift-tıklanan
bir uygulama + bir gizli ayar klasörü** koyup tüm sistemi çalıştırmak.

Yöntem: Kodu **PyInstaller** ile "dondurmak" (freeze). Python yorumlayıcısı + tüm kod +
bağımlılıklar tek çalıştırılabilir dosyaya paketlenir.

---

## Client'ta oluşacak sonuç

```
FULLSERVIS/                     (client makinede tek klasör)
├── fullservis-agent(.exe/.app) ← çift tıklanır (agent makineleri)
│   veya
├── fullservis-server(.exe)     ← çift tıklanır (Linux sunucu)
└── ayarlar/                    ← GİZLİ ayar klasörü (exe'nin yanında)
    ├── config.json
    ├── certs/                  (ca.crt, client.crt, client.key)   [yalnız sunucu]
    └── secrets.json            (Telegram/mail)                    [yalnız sunucu]
```

- **Python YOK, venv YOK, git YOK, okunabilir `.py` YOK.**
- Kullanıcı sadece uygulamaya çift tıklar.

---

## Kısıtlar (baştan bilinmeli)

1. **Her OS için ayrı derleme.** Windows `.exe` → Windows'ta, Mac `.app` → Mac'te,
   Linux binary → Linux'ta üretilir. Çapraz derleme yok. (Üç OS de elimizde var.)
2. **Harici programlar client'ta kurulu kalmalı:** `iperf3`, Chrome, (Windows) qBittorrent.
   Bunlar Python değil; exe'ye gömülmez. iperf3 binary'si uygulama yanına konabilir.
3. **Sırlar exe'ye gömülmez.** DB/FTP/Telegram kimlikleri dış `ayarlar/` klasöründen
   (secrets.json / env) okunur → exe içinde sır kalmaz, güncellemesi kolay olur.
4. **Küçük kod düzenlemesi gerekir:** dosya yolları (config.json, certs, secrets,
   frontend dist) donmuş modda farklı çözülür — "exe'nin yanındaki klasör" mantığına
   çekilecek.

---

## Adım adım yol haritası

### 0) Hazırlık (kod tarafı, bir kez)
- [ ] `common/config.py`: yol çözümünü donmuş modda (`sys.frozen`) **exe'nin bulunduğu
      klasöre** göre yap (config.json / certs / secrets / dist dışarıda kalsın).
- [ ] Sırların yalnızca dış dosyadan/env'den okunduğunu doğrula (zaten `get_secret` var).

### 1) Windows Agent (ilk hedef)
- [ ] `agent.spec` yaz (giriş: `run_agent.py`; gizli import'lar: uvicorn, fastapi,
      psutil, selenium, requests, sqlalchemy, psycopg2 vb.).
- [ ] `pyinstaller agent.spec` → `dist/fullservis-agent.exe`.
- [ ] Test: exe'yi `ayarlar/` ile birlikte bir makinede çalıştır, panelde online olsun.

### 2) Windows/Linux Server
- [ ] `server.spec` yaz (giriş: `run_server.py`; **frontend `dist/`'i veri olarak göm**).
- [ ] Linux'ta `pyinstaller server.spec` → tek dosya sunucu.
- [ ] Test: dashboard açılıyor mu, DB/FTP/bildirim çalışıyor mu.

### 3) Mac Agent
- [ ] Mac'te `pyinstaller agent.spec` → `fullservis-agent.app`.
- [ ] Gatekeeper notu: ilk açılışta sağ tık → Aç → Aç (imzasız uygulama).
- [ ] iperf3'ün Mac'te kurulu/erişilebilir olduğunu doğrula.

### 4) Dağıtım
- [ ] Her OS'un çıktısını + `ayarlar/` klasörünü flash belleğe koy.
- [ ] Client'a kopyala; kullanıcı uygulamaya çift tıklar.
- [ ] Güncelleme = yeni exe'yi USB ile üzerine yaz.

---

## Notlar / riskler

- İlk `.spec` ayarı deneme-yanılma ister (eksik "hidden import" → çalışırken hata).
  Sık sorun: `uvicorn`, `selenium`, `psycopg2` gizli import'ları ve `dist/` veri gömme.
- Antivüs bazen imzasız exe'yi karantinaya alır → gerekiyorsa istisna eklenir.
- Bu, şu anki `launchers/` (venv + `python run_*.py`) yönteminin **yerini alır**;
  paketleme oturana kadar `launchers/` çalışmaya devam eder (geçiş güvenli).

> Bu belge planı anlatır. Uygulamaya "0) Hazırlık" adımından başlanır; her adım
> çalıştıkça yukarıdaki kutucuklar işaretlenir.
