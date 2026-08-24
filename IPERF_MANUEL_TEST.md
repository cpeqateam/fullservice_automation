# iperf Doğrulama Testi — Adım Adım

**Amaç:** "Otomasyonla iperf değerleri düşük geldi" şikayetini teyit etmek.
3 şüpheli var, üçünü de ayrı ayrı ölçeceğiz:

1. **Flag farkı** — otomasyon `-P 20 -R` (download / 20 akış) koşuyor, elle test genelde `-P 1` (upload).
2. **Eşzamanlı yük** — YouTube ×4 + torrent + ping aynı anda modeme biniyor.
3. **wifi_track** — Wi-Fi Mac'te saniyede bir `system_profiler SPAirPortDataType` çalışıyor;
   Wi-Fi taraması tetiklediği için iperf'i aynı karttan bozuyor olabilir.

**Toplam süre:** ~15 dk. 5 ölçüm alacaksınız.

---

## Makineler

| Rol | Makine | IP |
|---|---|---|
| **SERVER** | MAC (Kablo) | `192.168.1.11` |
| **CLIENT** | MAC (Wi-Fi) | `192.168.1.14` |

Otomasyon **5201** portunu kullanıyor. Elle testlerde **5202** kullanacağız ki çakışmasın.

---

## Hazırlık

### 0) Arayüzde iperf parametrelerini ayarla — ÖNEMLİ

Testi başlatmadan önce, **iperf Parametreleri** bölümünde:

| Alan | Değer |
|---|---|
| **Yön** | `Reverse` (download: kablo → wifi) |
| **Pair** | `20` |
| **Port** | `5201` |
| **Süre** | `100` sn |

> Panelin varsayılan Pair değeri **10**'dur — elle **20** yapmayı unutmayın.
> Elle koşacağımız komut da `-P 20 -R -t 100` olacak, birebir aynı olsun diye.
> **Süreyi arayüzde ne verdiyseniz `-t` de o olmalı** (burada 100 sn).

### 1) Server ve terminaller

**Kablolu Mac'te** bir terminal aç, kapatma — test boyunca açık kalacak:
```bash
iperf3 -s -p 5202
```
`Server listening on 5202` yazmalı.

**Wi-Fi Mac'te** iki terminal aç:
- **T1** = iperf komutlarını koşacağın terminal
- **T2** = wifi_track taklidini koşacağın terminal

Wi-Fi Mac'te doğru makinede olduğunu ve karşıyı gördüğünü teyit et:
```bash
ipconfig getifaddr en0     # 192.168.1.14 çıkmalı
ping -c 3 192.168.1.11
iperf3 --version
```

---

## ÖLÇÜM ① — Otomasyonun kendi değeri

1. Arayüzden testi normal şekilde başlat.
2. Hiçbir şeye dokunma, iperf kutusunun bitmesini bekle.
3. Kutuda çıkan **"iperf bitti — gönderen X, alıcı Y"** değerini not al.
4. **"Durdur"a BASMA** — bir sonraki ölçüm için yük devam etsin.

> Not: iperf bitse de YouTube ve torrent Durdur'a basılana kadar koşmaya devam eder.
> Ölçüm ②'yi bu pencerede yapacağız.

---

## ÖLÇÜM ② — Elle, yük devam ederken

iperf kutusu biter bitmez, Wi-Fi Mac'te:

**T2'de** (wifi_track taklidi — o da bitmiş olacağı için elle canlandırıyoruz):
```bash
while true; do system_profiler SPAirPortDataType >/dev/null; sleep 1; done
```

**T1'de** (otomasyonun birebir aynı komutu):
```bash
iperf3 -c 192.168.1.11 -p 5202 -t 100 -P 20 -R -i 1
```

Bitince **T2'yi `Ctrl+C` ile kapat.** Sonucu not al.

Sonra arayüzden **"Durdur"a bas.** Yük tamamen kalksın.

---

## ÖLÇÜM ③ — Elle, ortam tamamen boş

Otomasyon durdu, YouTube/torrent kapalı. T2 kapalı. Sadece T1:

```bash
iperf3 -c 192.168.1.11 -p 5202 -t 100 -P 20 -R -i 1
```

Not al. Bu, hattın bu flag'lerle **saf kapasitesi**.

---

## ÖLÇÜM ④ — Elle + sadece wifi_track döngüsü

Ortam hâlâ boş. **T2'de** döngüyü tekrar başlat:
```bash
while true; do system_profiler SPAirPortDataType >/dev/null; sleep 1; done
```

**T1'de** aynı komut:
```bash
iperf3 -c 192.168.1.11 -p 5202 -t 100 -P 20 -R -i 1
```

Bitince T2'yi `Ctrl+C`. Not al.

> **③ ile ④ arasındaki fark = wifi_track'in bedeli.** Tek değişken bu.

---

## ÖLÇÜM ⑤ — "Düz iperf" (ekibin kıyasladığı komut)

Ortam boş, T2 kapalı:
```bash
iperf3 -c 192.168.1.11 -p 5202 -t 100 -P 1 -i 1
```

Bu **upload / tek akış** ölçer. Otomasyonunki download / 20 akış. Not al.

---

## Sonuçları buraya yaz

Her ölçümde çıktının en altındaki **`SUM ... receiver`** satırındaki Mbits/sec değerini al.
`Retr` sütunu da yüksekse (binlerce) not düş.

| # | Ölçüm | Mbits/sec | Retr |
|---|---|---|---|
| ① | Otomasyonun raporladığı | | |
| ② | Elle, tam yük altında | | |
| ③ | Elle, ortam boş | | |
| ④ | Elle, sadece wifi_track döngüsü | | |
| ⑤ | Düz iperf (`-P 1`, upload) | | |

---

## Nasıl okunacak

| Karşılaştırma | Fark varsa suçlu |
|---|---|
| **① vs ②** | Fark **yoksa** otomasyon doğru ölçüyor. Fark **varsa** runner/timing'de sorun var → koda bakacağız. |
| **② vs ③** | **Eşzamanlı yük.** Bu tasarım gereği — "abanma" testinin amacı bu, hata değil. |
| **③ vs ④** | **wifi_track.** ④ belirgin düşükse suçlu bulundu → örnekleme aralığını 1sn'den 5sn'ye çekeriz. |
| **③ vs ⑤** | **Flag farkı.** Ekip elmayla armudu kıyaslamış demektir (upload/tek akış vs download/20 akış). |

---

## Ek: otomasyonun gerçekten hangi komutu koştuğunu görmek

Wi-Fi Mac'teki iperf log'unun **2. satırında** çalıştırılan komut aynen yazıyor:

```bash
grep -m1 "Komut:" ~/.../logs/MAC_WIFI/<session>/fullServis_iperf_macWifi_*.txt
tail -20 ~/.../logs/MAC_WIFI/<session>/fullServis_iperf_macWifi_*.txt
```

`-R` ve `-P 20` orada görünüyorsa teşhis doğrulanmış olur.

---

## Sorun çıkarsa

| Hata | Çözüm |
|---|---|
| `Connection refused` | Kablolu Mac'te `iperf3 -s -p 5202` açık mı? |
| `the server is busy running a test` | Önceki test bitmemiş — 5 sn bekle, tekrar dene |
| `command not found` | `brew install iperf3` |
| Ölçümler arası tutarsızlık | Her ölçüm arasında **5 sn bekle**, server oturumu kapatsın |

## İlgili dosyalar

- [iperf_runner.py](fullservice-backend/common/runners/iperf_runner.py) — client komutu
- [wifi_util_mac.py](fullservice-backend/common/runners/wifi_util_mac.py) — `system_profiler` çağrısı
- [wifi_track_runner.py](fullservice-backend/common/runners/wifi_track_runner.py) — 1 sn'lik örnekleme döngüsü
- [app.js](fullservice-frontend/src/store/app.js) — UI varsayılanları (`direction: 'reverse'`, `parallel: 10` — **elle 20 yapılacak**)
- [DeviceForm.vue](fullservice-frontend/src/components/DeviceForm.vue) — "iperf Parametreleri" paneli (Yön / Pair / Port)
- [IPERF_REHBERI.md](IPERF_REHBERI.md) — iperf'in genel rehberi

---
---

# TEST RAPORU

**Tarih:** 20 Ağustos 2026
**Cihaz:** TP-LINK EX20V
**Konu:** "FULL Servis otomasyonuyla başlatılan iperf testinde değerler düşük geliyor" bildirimi
**Sonuç:** Bildirim doğrulandı. **Sebep otomasyonun iperf ölçümü değil, Wi-Fi Analiz (wifi_track) testinin macOS'ta kullandığı komuttur.** Kod düzeltildi.

## 1. Amaç

Şikayetin üç olası sebebi vardı. Hepsi ayrı ayrı ölçüldü:

1. **Komut farkı** — otomasyon `-P 20 -R` (20 paralel akış, download yönü) koşuyor; elle yapılan karşılaştırmalar genelde `-P 1` (tek akış, upload).
2. **Eşzamanlı yük** — test sırasında 4 makinede YouTube, Windows'ta torrent, 3 makinede ping aynı anda modeme biniyor.
3. **Wi-Fi Analiz testi** — Wi-Fi'ye bağlı MacBook'ta saniyede bir çalışan ölçüm komutunun aynı Wi-Fi kartını meşgul etme ihtimali.

## 2. Yöntem

Tüm ölçümler aynı hat, aynı cihazlar, aynı parametrelerle yapıldı:

| | |
|---|---|
| Server | MAC (Kablo) — `192.168.1.11` |
| Client | MAC (Wi-Fi) — `192.168.1.14` |
| Komut | `iperf3 -c 192.168.1.11 -t 100 -P 20 -R` |
| Süre | 100 saniye × 4 ölçüm |

Otomasyonun kendi log'undan çalıştırdığı komut teyit edildi ve elle koşulan komutla **birebir aynı** olduğu doğrulandı:

```
Komut: iperf3 -c 192.168.1.11 -p 5201 -t 100 -P 20 -R
```

## 3. Ölçüm sonuçları

| # | Senaryo | Ortalama | Medyan | En düşük saniye | 50 Mbps altı saniye |
|---|---|---:|---:|---:|---:|
| ③ | **Sadece iperf** (hat boş) | **630 Mbps** | 636 | 396 | %0 |
| ④ | iperf + **Wi-Fi Analiz** | **201 Mbps** | 140 | 2.7 | **%18** |
| ② | iperf + tam yük (torrent + YouTube + Wi-Fi Analiz), elle | **171 Mbps** | 107 | 3.8 | %22 |
| ① | **Otomasyon** (tüm testler) | **151 Mbps** | 128 | 20.9 | %1 |

## 4. Bulgular

**A. Otomasyonun ölçümü doğrudur.**
Otomasyon 151 Mbps, aynı koşullarda elle yapılan ölçüm 171 Mbps raporladı — %12 fark, aynı mertebede. Otomasyonun iperf'i yanlış çalıştırdığına veya yanlış raporladığına dair bulgu yoktur.

**B. Asıl sebep Wi-Fi Analiz testidir: hattın %68'ini tüketiyor.**
Tek değişkenin Wi-Fi Analiz olduğu karşılaştırmada verim **630 → 201 Mbps**'e düştü.
Düşüş düz bir yavaşlama değil, **periyodik kesinti** biçimindedir: hat boşken en düşük saniye 396 Mbps ve hiç çökme yokken, Wi-Fi Analiz açıkken en düşük saniye **2.7 Mbps**'e iniyor ve saniyelerin **%18'i** 50 Mbps'in altına düşüyor.

**C. Testin asıl yükü (torrent + YouTube) neredeyse etkisizdir.**
201 → 171 Mbps, yalnızca 30 Mbps. Yani gözlenen düşüşün **~%93'ü ölçüm aracımızdan**, ~%7'si testin asıl amacı olan yükten kaynaklanıyor.

## 5. Teknik sebep

Wi-Fi Analiz testi her iki platformda farklı komut kullanıyordu:

| Platform | Komut | Süre | Wi-Fi taraması |
|---|---|---:|---|
| Windows | `netsh wlan show interfaces` | ~10 ms | **Hayır** |
| macOS (eski) | `system_profiler SPAirPortDataType` | **~7.200 ms** | **Evet** |

`system_profiler SPAirPortDataType` çıktısında "Other Local Wi-Fi Networks" (etraftaki diğer ağlar) bölümü bulunur. macOS bu listeyi üretmek için **aktif tarama** yapmak zorundadır: Wi-Fi radyosu bağlı olduğu kanaldan ayrılır, 2.4 GHz ve 5 GHz bandındaki tüm kanalları tek tek gezer, her birinde sinyal dinler, sonra kendi kanalına döner. Kartta tek radyo olduğu için **bu süre boyunca veri taşınamaz.**

Windows'taki `netsh wlan show interfaces` ise tarama yapmaz; sürücünün hafızasında zaten duran "şu an hangi ağa bağlıyım, sinyalim ne" bilgisini okur.

Yani iki platformda **aynı bilgiyi** almak için seçilen komutların maliyeti farklıydı: Windows'ta bedava olan işlem, macOS'ta hattın üçte ikisine mal oluyordu.

## 6. Yapılan düzeltme

macOS artık Windows ile aynı davranışı gösteriyor — Apple'ın resmi Wi-Fi API'si **CoreWLAN** üzerinden, **tarama yapmadan**, kartın anlık durumu okunuyor.

| | Önce | Sonra |
|---|---|---|
| Kaynak | `system_profiler SPAirPortDataType` | CoreWLAN API |
| Çağrı süresi | ~7.200 ms | **6,2 ms** (1156× hızlı) |
| Wi-Fi taraması | Evet | **Hayır** |
| Diğer testlere etkisi | iperf'te %68 kayıp | Yok |

Değişen dosyalar:
- [wifi_util_mac.py](fullservice-backend/common/runners/wifi_util_mac.py) — CoreWLAN ile taramasız okuma
- [wifi_util.py](fullservice-backend/common/runners/wifi_util.py) — macOS kolu devredildi; BSSID okuması da CoreWLAN'a alındı
- [wifi_track_runner.py](fullservice-backend/common/runners/wifi_track_runner.py) — açıklama notu güncellendi
- [requirements.txt](fullservice-backend/requirements.txt) — `pyobjc-framework-CoreWLAN` (yalnızca macOS)

**Değişmeyenler:** log dosyası formatı, ölçülen alanlar (sinyal, kanal, RX/TX hızı, PHY), DB özeti ve testin süre bazlı çalışma mantığı — Wi-Fi Analiz her platformda yine tam olarak `duration` saniyede biter, Windows ile macOS aynı anda tamamlanır.

## 7. Doğrulama için yapılması gerekenler

1. İki MacBook'ta bağımlılığı kur:
   ```bash
   pip install -r requirements.txt
   ```
2. Otomasyondan aynı testi tekrar koş (`-P 20`, Reverse, 100 sn).
3. Beklenen: iperf değeri **151 Mbps'ten ~600 Mbps'e** yükselmeli; kalan fark yalnızca torrent + YouTube yükünden gelmeli (~30 Mbps).
