# Tek-Tık Başlatıcılar (durdur + çalıştır)

Bu klasördeki dosyalar, son kullanıcının **elle durdur / başlat** yapmasını ortadan
kaldırır. Her dosya sırayla şunu yapar:

1. O portta çalışan **eski süreci kapatır** (durdurmaya gerek kalmaz)
2. Süreci **yeniden başlatır**

Kullanıcı bundan sonra sadece ilgili dosyaya **çift tıklar**.

> 🔒 **Güvenlik kararı:** Bu başlatıcılar **git pull YAPMAZ.** Client makinelere GitHub
> erişimi verilmez (o makineleri başka ekipler de kullanıyor; repo'yu onlara açmak
> istemiyoruz). **Kod güncellemesi USB ile** dağıtılır: geliştirici, güncellenmiş
> kodu ve gerekiyorsa bu başlatıcıları flash bellekle ilgili makineye kopyalar.

---

## Hangi makinede hangi dosya?

| Makine | İşletim sistemi | Dosya |
|--------|-----------------|-------|
| Linux Sunucu | Linux | `baslat-server.sh` |
| WINDOWS (win_wifi) | Windows | `baslat-agent.bat` |
| MAC Kablo / MAC Wi-Fi | macOS | `baslat-agent.command` |

> ⚠️ `.bat` **yalnızca Windows'ta** çalışır; Mac ve Linux için `.command` / `.sh` gerekir.
> O yüzden tek bir dosya değil, platforma göre ayrı dosyalar var.

---

## Güncelleme akışı (geliştiricinin yapacağı)

1. Geliştirme makinesinde kodu güncelle/test et.
2. Güncel **kodu** (ör. `fullservice-backend/` klasörü veya değişen dosyalar) ve
   gerekiyorsa **başlatıcı dosyayı** flash belleğe kopyala.
3. İlgili client makinede kodu `REPO_DIR` konumuna **üzerine yaz**.
4. Kullanıcı başlatıcıya **çift tıklar** → eski süreç kapanır, güncel kod başlar.

> Sertifika (`certs/`) ve `secrets.json` de aynı şekilde **sadece USB ile** taşınır,
> hiçbir zaman GitHub'a konmaz.

---

## Kurulum (her makinede yalnızca BİR KEZ)

### 1) Dosyayı makineye koy
İlgili başlatıcıyı o makineye kopyala (Masaüstü uygun bir yer).

### 2) İçindeki ayarları düzenle
Dosyayı bir metin düzenleyiciyle aç, en üstteki **AYARLAR** bölümünü doldur:

- **`REPO_DIR`** → `fullservice_automation` klasörünün tam yolu.
- **Agent dosyalarında** ayrıca:
  - `NODE_ID` → o makinenin kimliği: `win_wifi`, `mac_cable` veya `mac_wifi`
  - `SERVER_URL` → Linux sunucunun adresi, örn. `http://192.168.1.10:8770`

### 3) (Yalnızca Mac ve Linux) çalıştırma izni ver — bir kez
Terminal'de:
```bash
chmod +x baslat-agent.command     # Mac
chmod +x baslat-server.sh         # Linux
```

---

## Kullanım (her seferinde)

- **Windows / Mac:** dosyaya **çift tıkla**. (Mac ilk açılışta "geliştirici doğrulanamadı"
  derse: sağ tık → **Aç** → **Aç**.)
- **Linux:** dosya yöneticisinde çift tıkla → **"Programı Çalıştır"**, ya da terminalde
  `./baslat-server.sh`.

Açılan pencere: eskisini kapatır, yenisini başlatır. Pencere açık kaldığı sürece süreç
çalışır; kapatınca durur.

---

## Ön koşullar (bir kez, kurulum rehberlerinde anlatıldı)

- `python` ve `fullservice-backend/venv` sanal ortamı kurulu olmalı
  (bkz. `KURULUM_SAHA_4_MAKINE.md`).
- Sunucuda `certs/` ve (bildirim için) `secrets.json` yerinde olmalı (USB ile).
