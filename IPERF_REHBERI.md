# iperf / iperf3 — Sıfırdan Tam Rehber (+ FULL Servis'te kullanımı)

> Bu doküman ağ konusunda yeni biri için bile eksiksiz olacak şekilde yazıldı.
> İki bölüm var:
> **A) iperf'in kendisi** (nedir, neden, nasıl, komutlar, çıktı okuma).
> **B) FULL Servis projesinde iperf** (hangi dosya, hangi yapı, mevcut durum).

---

# BÖLÜM A — iperf'in kendisi

## 1. iperf nedir?
**iperf**, iki bilgisayar arasındaki ağ bağlantısının **ne kadar hızlı veri
taşıyabildiğini** (bant genişliği / throughput) ölçen ücretsiz bir komut satırı
aracıdır. Yani "bu iki nokta arasında saniyede kaç megabit/gigabit veri akıyor?"
sorusunu yanıtlar.

Basit benzetme: Bir **su borusu** düşün. iperf, boruya basınçla su pompalayıp
"bu boru saniyede kaç litre taşıyor?" diye ölçer. Borudaki darboğazı (modem, switch,
Wi-Fi, kablo) bulmanı sağlar.

> **Önemli ayrım:** iperf bir **hız testi** aracıdır, internet hızını (speedtest.net)
> ölçmez. İki **kendi** cihazın arasındaki **yerel** hattı ölçer. İnternet hızı
> ölçmek istersen iki uçtan biri internette olmalı; biz lokal ağda kullanıyoruz.

## 2. iperf vs iperf3 — fark ne?
- **iperf (iperf2):** Eski sürüm (2.x). Hâlâ kullanılır ama geliştirme yavaşladı.
- **iperf3:** Sıfırdan yeniden yazılmış modern sürüm. Daha temiz çıktı, **JSON**
  desteği, tek çalıştırılabilir dosya, `-J`, `--reverse` gibi yeni bayraklar.
- **UYUMSUZ:** iperf2 ile iperf3 **birbirine bağlanamaz.** İki uçta da **aynı**
  sürüm (tercihen iperf3) olmalı.
- Biz projede **iperf3** kullanıyoruz. Bu dokümanda komutlar iperf3'tür.

## 3. Neden iperf testi yapılır?
- **Hattın gerçek kapasitesini ölçmek:** "1 Gbit kablo dedik ama gerçekten 1 Gbit mi
  akıyor?"
- **Darboğaz bulmak:** Yavaşlık modemde mi, Wi-Fi'de mi, kabloda mı, switch'te mi?
- **Cihaz/firmware stres testi:** Hattı **maksimuma kadar doldurup** cihazın
  (modem/router) yük altında çökmeden dayanıp dayanmadığını görmek. **FULL Servis'te
  iperf'i tam bu yüzden kullanıyoruz** — modeme "abandırmak" (stres) için.
- **Wi-Fi performansı:** Mesafe/kanal/girişim throughput'u nasıl etkiliyor?

## 4. Nasıl çalışır? — Server / Client modeli
iperf **iki rol** ile çalışır; ikisi de aynı anda gerekir:

```
   ┌─────────────────┐         veri akışı          ┌─────────────────┐
   │   CLIENT         │ ───────────────────────────▶│   SERVER        │
   │ iperf3 -c <ip>   │   (TCP/UDP paketleri)        │ iperf3 -s       │
   │ (gönderir/ölçer) │ ◀───────────────────────────│ (dinler/alır)   │
   └─────────────────┘         sonuç özeti           └─────────────────┘
```

- **SERVER** (`iperf3 -s`): Önce çalıştırılır. Bir port açar (varsayılan **5201**)
  ve bağlantı **bekler**. Pasiftir.
- **CLIENT** (`iperf3 -c <server_ip>`): Server'a bağlanır, belirtilen süre boyunca
  olabildiğince hızlı veri **gönderir** ve sonucu raporlar.

Sıra önemlidir: **önce server, sonra client.** Server kapalıyken client bağlanamaz
("Connection refused" verir).

### TCP mi UDP mi?
- **TCP (varsayılan):** Güvenilir; gerçek "ne kadar hızlı dosya çekerim" cevabını
  verir. throughput + retransmit (yeniden gönderim) ölçer.
- **UDP (`-u`):** Hız + **paket kaybı (loss)** + **jitter** (gecikme oynaması) ölçer.
  VoIP/video gibi gerçek-zamanlı trafiği taklit eder. UDP'de hedef hızı `-b` ile verirsin.

## 5. Kurulum
| Platform | Komut |
|----------|-------|
| **Linux (Ubuntu/Debian)** | `sudo apt install iperf3` |
| **macOS (Homebrew)** | `brew install iperf3` |
| **macOS (brew yoksa, eski)** | Kaynaktan: `curl -L -o iperf3.tar.gz https://downloads.es.net/pub/iperf/iperf-3.17.1.tar.gz && tar xzf iperf3.tar.gz && cd iperf-3.17.1 && ./configure && make && sudo make install` |
| **Windows** | https://files.budman.pw/ veya https://iperf.fr → win64 zip indir → klasöre çıkar (iperf3.exe + cygwin1.dll birlikte) → PATH'e ekle |
| Doğrulama | `iperf3 --version` |

## 6. Komutlar — eksiksiz başvuru

### Temel kullanım
```bash
# 1) SERVER makinesinde (önce bunu başlat):
iperf3 -s
# "Server listening on 5201" yazar, bekler.

# 2) CLIENT makinesinde (server'ın IP'siyle):
iperf3 -c 192.168.1.11
# 10 saniye TCP testi yapar, sonucu basar.
```

### En çok kullanılan bayraklar
| Bayrak | Ne yapar | Örnek |
|--------|----------|-------|
| `-s` | Server modu (dinle) | `iperf3 -s` |
| `-c <ip>` | Client modu (bağlan) | `iperf3 -c 192.168.1.11` |
| `-p <port>` | Port (varsayılan 5201) | `-p 5201` |
| `-t <sn>` | Süre (saniye, varsayılan 10) | `-t 60` |
| `-P <n>` | **Paralel akış sayısı** (hattı daha çok doldurur) | `-P 4` |
| `-i <sn>` | Ara rapor aralığı | `-i 1` |
| `-u` | UDP modu | `-u -b 100M` |
| `-b <hız>` | UDP hedef hızı (0 = sınırsız) | `-b 200M` |
| `-R` / `--reverse` | Ters yön: server gönderir, client alır (indirme ölçer) | `-c <ip> -R` |
| `--bidir` | Çift yönlü aynı anda | `-c <ip> --bidir` |
| `-J` | Çıktıyı **JSON** ver (programdan ayrıştırmak için) | `-c <ip> -J` |
| `-w <boyut>` | TCP pencere boyutu (ileri seviye ayar) | `-w 256K` |
| `-4` / `-6` | IPv4 / IPv6 zorla | `-4` |
| `-D` | Server'ı arka planda (daemon) çalıştır | `iperf3 -s -D` |
| `-1` | Server tek bağlantıdan sonra kapanır | `iperf3 -s -1` |

### Sık senaryolar
```bash
# Hattı 60 sn boyunca 4 paralel akışla DOLDUR (stres):
iperf3 -c 192.168.1.11 -t 60 -P 4

# İndirme yönünü ölç (server→client):
iperf3 -c 192.168.1.11 -R

# UDP ile paket kaybı + jitter ölç, 200 Mbit hedefle:
iperf3 -c 192.168.1.11 -u -b 200M -t 30

# Sonucu JSON al (script ile işlemek için):
iperf3 -c 192.168.1.11 -t 10 -J

# Farklı port (5201 doluysa / birden çok test):
iperf3 -s -p 5202
iperf3 -c 192.168.1.11 -p 5202
```

## 7. Çıktı nasıl okunur?
TCP client çıktısı örneği:
```
[ ID] Interval           Transfer     Bitrate         Retr
[  5]   0.00-1.00   sec  112 MBytes   940 Mbits/sec    0
...
[  5]   0.00-10.00  sec  1.10 GBytes  944 Mbits/sec    0   sender
[  5]   0.00-10.00  sec  1.10 GBytes  942 Mbits/sec        receiver
```
- **Transfer:** Toplam taşınan veri (1.10 GBytes).
- **Bitrate:** **En önemli sayı** — hız (944 Mbits/sec ≈ 1 Gbit hattın dolu olduğu).
- **Retr (Retransmits):** Yeniden gönderilen TCP paketi. Yüksekse hat/cihaz sorunlu.
- **sender / receiver:** Gönderen ve alan tarafın ölçtüğü hız (ikisi yakın olmalı).

UDP'de ekstra: **Jitter** (ms) ve **Lost/Total Datagrams** (kayıp %). Kayıp yüksekse
hat o hızı kaldıramıyor demektir.

## 8. iperf testi yapılmazsa ne olur?
- Hattın/cihazın **gerçek kapasitesini bilemezsin** — "1 Gbit" yazısına güvenirsin
  ama gerçekte 300 Mbit olabilir.
- **Yük altındaki davranışı göremezsin:** Modem normalde iyi görünür ama hat
  dolunca (yoğun saatte) çöküyorsa, bunu ancak iperf gibi bir araçla **kontrollü**
  doldurarak yakalarsın.
- FULL Servis bağlamında: iperf, modeme bindirdiğimiz stresin **en ağır bileşenidir**;
  olmadan "abanma" testi eksik kalır (sadece ping/youtube/torrent yükü olur).

## 9. Sık hatalar / sorun giderme
| Mesaj | Sebep | Çözüm |
|-------|-------|-------|
| `Connection refused` | Server çalışmıyor / yanlış IP-port | Önce `iperf3 -s` çalıştır, IP/portu doğrula |
| `unable to connect / timed out` | Güvenlik duvarı 5201'i kapatıyor | Server'da portu aç (Win: Defender Firewall; Linux: `ufw allow 5201`) |
| `the server is busy running a test` | Server zaten bir testte | Bitmesini bekle ya da ayrı port kullan |
| `error: control socket has closed unexpectedly` | Sürüm uyumsuz (iperf2↔iperf3) | İki uçta da iperf3 kullan |
| `command not found` | iperf3 kurulu değil | Bölüm 5'teki kurulum |
| Çok düşük hız | Wi-Fi/kablo/CPU darboğazı | `-P 4` paralel dene; kabloyu/kartı kontrol et |

---

# BÖLÜM B — FULL Servis projesinde iperf

## 10. Bizim topolojimiz (ÖNEMLİ — değişti)
Eskiden Linux sunucu iperf server'dı. **Artık değil.** Güncel kurulum:

```
   ┌──────────────────────┐     iperf3 trafiği      ┌──────────────────────┐
   │  MAC (Wi-Fi)         │ ───────(modem)─────────▶│  MAC (Kablo)         │
   │  mac_wifi            │                         │  mac_cable           │
   │  rol: "iperf"        │                         │  rol: "iperf_server" │
   │  iperf3 -c <kablo_ip>│ ◀───────────────────────│  iperf3 -s :5201     │
   └──────────────────────┘                         └──────────────────────┘
         CLIENT (yük basar)                              SERVER (dinler)
```

- **Kablolu Mac (`mac_cable`)** = iperf **SERVER** → `iperf3 -s -p 5201`.
- **Wi-Fi Mac (`mac_wifi`)** = iperf **CLIENT** → `iperf3 -c <kablolu_mac_ip> -P 4`.
- Trafik iki Mac arasında **modem üzerinden** akar → modem yük altında zorlanır.
- Linux sunucu iperf'e karışmaz (sadece orkestrasyon + kendi ping/youtube testleri).

## 11. Hangi dosyalar? (kod haritası)
| Dosya | Görevi |
|-------|--------|
| [`common/runners/iperf_server_runner.py`](fullservice-backend/common/runners/iperf_server_runner.py) | Kablolu Mac'te `iperf3 -s -p <port>` çalıştırır; süre boyunca dinler, durdurulunca/bitince kapanır. |
| [`common/runners/iperf_runner.py`](fullservice-backend/common/runners/iperf_runner.py) | Wi-Fi Mac'te `iperf3 -c <server> -p <port> -t <süre> -P <paralel>` çalıştırır; server hazır değilse **5 kez yeniden dener**; özeti (gönderen/alıcı hız) log'dan ayrıştırır. |
| [`common/runners/registry.py`](fullservice-backend/common/runners/registry.py) | `"iperf_server" → iperf_server_runner.run`, `"iperf" → iperf_runner.run` eşlemesi. |
| [`common/protocol.py`](fullservice-backend/common/protocol.py) | `TestType.IPERF_SERVER`/`IPERF`; `TestParams` içinde `iperf_server` (hedef IP), `iperf_port` (5201), `iperf_parallel` (4). |
| [`server/orchestrator.py`](fullservice-backend/server/orchestrator.py) | `_iperf_server_ip()` → client'ın bağlanacağı adresi (kablolu Mac'in kayıtlı IP'si; yoksa config `network.assignments`) çözer ve `TestParams.iperf_server`'a koyar. |
| [`config.json`](fullservice-backend/config.json) | `nodes`: mac_cable rolünde `iperf_server`, mac_wifi rolünde `iperf`. `defaults.iperf_port=5201`, `iperf_parallel=4`. |

## 12. Akış (oturum başlayınca)
1. Dashboard "Başlat" → orchestrator `TestParams` hazırlar; `iperf_server` =
   kablolu Mac'in IP'si (`_iperf_server_ip()`).
2. Fan-out: kablolu Mac agent'ı `iperf_server` rolüyle **`iperf3 -s`'i kendi başlatır**.
3. Wi-Fi Mac agent'ı `iperf` rolüyle `iperf3 -c <kablolu_mac_ip> -P 4` başlatır.
4. Client server'a bağlanır (hazır değilse 5 kez retry) → hattı doldurur →
   ilerleme + özet dashboard'a yansır → log dosyası sunucuya yüklenir
   (`logs/MAC_WIFI/<session>/`).

## 13. Ön koşullar
- **Her iki Mac'te `iperf3` kurulu** olmalı (Bölüm 5). Yoksa kutu kırmızı olur.
- Kablolu Mac'te **5201 portu** girişe açık olmalı (macOS güvenlik duvarı kapalıysa
  sorun yok; açıksa iperf3'e izin ver).
- İki Mac **aynı modemde** olmalı (aynı `192.168.1.x` ağı) ki birbirini görsünler.

## 14. Elle test (otomasyondan bağımsız doğrulama)
Otomasyon çalışmadan önce iperf'in kendisini elle test et:
```bash
# Kablolu Mac'te (server):
iperf3 -s

# Wi-Fi Mac'te (client) — kablolu Mac'in IP'siyle:
iperf3 -c 192.168.1.11 -t 10 -P 4
```
Hız satırı (Mbits/sec) geliyorsa iperf altyapısı sağlam demektir; sorun otomasyon
tarafındadır.

## 15. Mevcut durum (2026-06-17)
⚠️ **iperf otomasyon içinden henüz düzgün başlamıyor** ("başlatılamıyor"). Yarın
bakılacak. İlk kontrol noktaları:
- İki Mac'te `iperf3 --version` çalışıyor mu?
- `_iperf_server_ip()` doğru IP'yi mi döndürüyor? (kablolu Mac kayıt olmuş mu,
  IP'si `192.168.1.11` mi)
- Elle test (Bölüm 14) çalışıyor mu? Çalışıyorsa sorun runner/timing'de.
- Kablolu Mac'te `iperf3 -s` gerçekten ayağa kalkıyor mu (port 5201 dinleniyor mu:
  `lsof -i :5201` / `netstat`)?
- Client log'unda hata ne? (`logs/MAC_WIFI/<session>/...iperf...txt`)

> Bu rehber, yarın iperf sorununu çözerken elindeki tam başvuru olsun diye yazıldı.
> Mimari için [`MIMARI.md`](MIMARI.md) §5.3, kod gezisi için
> [`KOD_HAKIMIYETI.md`](KOD_HAKIMIYETI.md).
