# FULL Servis — Uygulama Yapma ve Odaya Kurma Rehberi

Bu klasör, FULL Servis'i **çift tıklanan bir uygulamaya** çevirir.
Odadaki 4 bilgisayarda artık Python, venv, GitHub, terminal komutu **gerekmez**.

---

## 1. Bu klasörde ne var?

```
launchers/
├── KURULUM.md          ← şu an okuduğun dosya
└── build/
    ├── derle-linux.sh          ← LINUX'ta çalıştır  → sunucu uygulamasını yapar
    ├── derle-mac.sh            ← MAC'te çalıştır    → iki mac uygulamasını yapar
    ├── derle-windows.bat       ← WINDOWS'ta çalıştır→ windows uygulamasını yapar
    │
    ├── server_app.py           ← sunucu uygulamasının içindeki program
    ├── agent_app.py            ← client uygulamalarının içindeki program
    ├── fullservis_server.spec  ← sunucu için "paketleme tarifi"
    ├── fullservis_agent.spec   ← client için "paketleme tarifi"
    │
    └── cikti/                  ← derleme sonucu buraya düşer (USB'ye kopyalanacak klasör)
```

Sadece **3 dosyayı sen çalıştırırsın**: `derle-linux.sh`, `derle-mac.sh`,
`derle-windows.bat`. Diğerleri (`*.py`, `*.spec`) bu üçünün arka planda kullandığı
malzemedir; onlara dokunmana gerek yok.

**Terim:** *derlemek* = kodu, içinde Python'u da olan tek bir uygulamaya paketlemek.
Bu yüzden karşı makinede Python kurmaya gerek kalmıyor.

---

## 2. Hangi makinede hangi uygulama olacak?

| Makine | Uygulama adı | Ne yapar |
|---|---|---|
| LINUX | `FULLSERVIS-SUNUCU` | Sunucu + panel. **İlk bu açılır.** |
| MAC (Kablo) | `FULLSERVIS-MAC-KABLO` | Kendini sunucuya tanıtır, testlerini koşar |
| MAC (Wi-Fi) | `FULLSERVIS-MAC-WIFI` | 〃 |
| WINDOWS | `FULLSERVIS-WINDOWS-WIFI.exe` | 〃 |

Uygulama **kendi adına bakarak** hangi bilgisayar olduğunu anlar ve sunucuya öyle
kaydolur. Yani senin eskiden yazdığın `python run_agent.py mac_wifi http://192.168.1.10:8770`
komutunun işini uygulama kendisi yapıyor.

> ⚠️ Uygulamanın **adını değiştirme.** Adı değişirse hangi bilgisayar olduğunu anlayamaz.

---

## 3. Uygulamaları yapma (her makinede BİR KEZ)

Uygulamalar sadece kendi işletim sisteminde yapılabilir: Windows uygulaması
Windows'ta, Mac uygulaması Mac'te, Linux uygulaması Linux'ta. Yani **3 makinede de
bir kez derleme yapacaksın.** Kodu şu an nasıl çekiyorsan (GitHub) öyle çek, sonra:

### 3.1 LINUX bilgisayarda

Terminalde, proje klasöründe:

```bash
chmod +x launchers/build/derle-linux.sh
./launchers/build/derle-linux.sh
```

**Beklenen sonuç:** Birkaç dakika sürer, sonunda "TAMAM" yazar ve şu klasör oluşur:

```
launchers/build/cikti/FULLSERVIS-SUNUCU/
├── FULLSERVIS-SUNUCU               ← uygulama
├── FULL-Servis-Sunucu.desktop      ← masaüstü kısayolu
└── ayarlar/
    ├── config.json                 ← IP'ler, süre, hangi makine hangi testi koşacak
    ├── secrets.json                ← Telegram/mail/DB şifreleri
    └── certs/                      ← FTP/DB sertifikaları
```

> `secrets.json` ve `certs/` GitHub'da yoktur. Linux makinede bunlar zaten varsa script
> kendisi kopyalar; yoksa USB ile getirip `ayarlar/` içine elle koy. **Bunlar olmadan
> Telegram/mail bildirimi ve DB kaydı çalışmaz.**

### 3.2 MAC bilgisayarlardan BİRİNDE

```bash
chmod +x launchers/build/derle-mac.sh
./launchers/build/derle-mac.sh
```

**Beklenen sonuç:** İki klasör birden oluşur (tek komutla ikisi de):

```
launchers/build/cikti/FULLSERVIS-MAC-WIFI/
launchers/build/cikti/FULLSERVIS-MAC-KABLO/
```

Yani iki Mac'te de derleme yapmana gerek yok; birinde yap, diğerine USB ile götür.
(İki Mac de aynı işlemci ailesinden olmalı — ikisi de Apple Silicon ya da ikisi de Intel.)

### 3.3 WINDOWS bilgisayarda

`launchers\build\derle-windows.bat` dosyasına **çift tıkla.**

**Beklenen sonuç:** Pencere açılır, birkaç dakika sonra "TAMAM" yazar ve şu klasör oluşur:

```
launchers\build\cikti\FULLSERVIS-WINDOWS-WIFI\
├── FULLSERVIS-WINDOWS-WIFI.exe
└── ayarlar\config.json
```

---

## 4. Odaya kurulum (USB ile, her makineye bir kez)

`cikti/` içindeki klasörü **olduğu gibi, içindeki `ayarlar/` klasörüyle beraber**
o makinenin **Masaüstüne** kopyala:

| Klasör | Hangi makineye |
|---|---|
| `FULLSERVIS-SUNUCU/` | LINUX |
| `FULLSERVIS-MAC-KABLO/` | MAC (kablolu) |
| `FULLSERVIS-MAC-WIFI/` | MAC (Wi-Fi) |
| `FULLSERVIS-WINDOWS-WIFI/` | WINDOWS |

**Beklenen sonuç:** Her makinenin masaüstünde tek bir klasör olur, içinde uygulama +
`ayarlar` klasörü. Kullanıcı sadece uygulamaya çift tıklayacak.

### Bir kerelik ek adımlar

- **Mac'lerde:** İlk açılışta "geliştirici doğrulanamadı" derse → uygulamaya
  **sağ tık → Aç → Aç**. Bir kez yapılır, sonra normal çift tık yeter.
- **Linux'ta:** `FULL-Servis-Sunucu.desktop` dosyasına sağ tık → "Çalıştırmaya izin ver".
- **Windows'ta:** Defender uyarı verirse "Yine de çalıştır" de.

### Bu programlar makinelerde kurulu olmalı (uygulamanın içine giremezler)

- **iperf3** → Mac'lerde (`brew install iperf3`)
- **Google Chrome** → YouTube testi için hepsinde
- **qBittorrent** → sadece Windows'ta

---

## 5. Günlük kullanım (odaya giren kullanıcı ne yapacak?)

Sırayla çift tıklamak, hepsi bu:

1. **LINUX** → `FULL Servis Sunucu`
   → Siyah pencere açılır, birkaç saniye sonra **panel tarayıcıda kendiliğinden açılır.**
2. **MAC (Kablo)** → `FULLSERVIS-MAC-KABLO`
   → Panelde bu makine **yeşil** yanar.
3. **MAC (Wi-Fi)** → `FULLSERVIS-MAC-WIFI` → yeşil yanar.
4. **WINDOWS** → `FULLSERVIS-WINDOWS-WIFI` → yeşil yanar.

Sonra panelde: giriş yap → Marka/Model/Firmware seç → süreyi gir → **BAŞLAT**.

> Açılan pencereleri **kapatma.** Kapatırsan o makine panelden düşer.
> Yanlışlıkla iki kere tıklarsan sorun olmaz; uygulama eskisini kendi kapatır.

Test bitince sonuçlar FTP'ye + veritabanına yazılır, Telegram ve mail bildirimi gider.

---

## 6. Sonradan değişiklik yapmak

| Ne değişti? | Ne yapmalısın |
|---|---|
| IP, test süresi, hangi makine hangi testi koşacak | Sadece o makinedeki `ayarlar/config.json`'u düzenle. **Yeniden derleme yok.** |
| Telegram/mail/DB şifresi | Linux'taki `ayarlar/secrets.json`'u düzenle. |
| Kodda bir şey (yeni özellik, hata düzeltme) | O işletim sisteminde derleme scriptini tekrar çalıştır, yeni klasörü USB ile eskisinin üzerine kopyala. |

---

## 7. Bir şeyler ters giderse

| Belirti | Sebep / çözüm |
|---|---|
| Panelde bir makine kırmızı | O makinedeki uygulama kapalı → çift tıkla, 10 sn içinde yeşile döner |
| "Bu uygulamanın hangi bilgisayara ait olduğu anlaşılamadı" | Uygulamanın adı değişmiş → eski adına geri çevir |
| Panel tarayıcıda açılmadı | Tarayıcıya elle yaz: `http://192.168.1.10:8770` |
| Telegram/mail gelmedi | Linux'ta `ayarlar/secrets.json` eksik ya da hatalı |
| Marka/Model listeleri boş geliyor | DB'ye ulaşılamıyor → `ayarlar/certs/` ve `secrets.json`'u kontrol et (sistem yine çalışır, alanları elle yazabilirsin) |
| Derleme scripti hata verdi | Ekrandaki son satırları oku; genelde `pip install` ya da `npm` eksikliğidir |

---

## 8. Geliştirme yaparken (senin için)

Kodu değiştirirken her seferinde derlemene gerek yok; eskisi gibi çalışmaya devam ediyor:

```bash
python run_server.py      # Linux'ta sunucu
python run_agent.py mac_wifi http://192.168.1.10:8770   # client'ta agent
```

Derleme sadece **odaya dağıtacağın** sürüm için gerekir.
