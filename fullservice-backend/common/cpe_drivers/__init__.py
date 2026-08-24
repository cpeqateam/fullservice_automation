"""
CPE driver registry — auto-discovery.

cpe_drivers/ altındaki her alt-paket içinde bir driver.py dosyası beklenir.
driver.py modülü `BRAND` ve `MODEL` sembolleri tanımladıysa otomatik kayda
alınır. Yeni modem eklemek için: yeni bir alt-klasör + driver.py açmak yeterli.

Kullanım:
    from common.cpe_drivers import get_driver
    drv = get_driver("ZTE", "EX20V")
    drv.connect(selenium_driver, "192.168.1.1")
"""
import os
import pkgutil
import importlib
from typing import Optional

_cache: Optional[dict] = None


def _driver_paketleri() -> list:
    """Driver alt-paketlerinin adlarını döndürür.

    İKİ ORTAMDA DA çalışmak zorundadır:
      • Kaynaktan çalışırken → alt-klasörler diskte durur, ikisi de görür.
      • PyInstaller ile PAKETLENMİŞKEN → modüller diskte DEĞİL, uygulamanın
        arşivinin içindedir. Orada os.path.dirname(__file__) var olmayan bir
        yol verir ve os.listdir() FileNotFoundError fırlatır — eski kod tam
        burada patlıyordu. pkgutil, PyInstaller'ın kendi yükleyicisine
        sorduğu için doğru listeyi döndürür; bu yüzden ÖNCE o denenir.
    """
    adlar = [m.name for m in pkgutil.iter_modules(__path__)
             if m.ispkg and not m.name.startswith("_")]
    if adlar:
        return sorted(adlar)

    # Yedek: pkgutil boş döndüyse (beklenmedik ortam) diskten okumayı dene.
    try:
        kok = os.path.dirname(__file__)
        return sorted(a for a in os.listdir(kok)
                      if not a.startswith("_") and os.path.isdir(os.path.join(kok, a)))
    except OSError as e:
        print(f"[cpe_drivers] Driver klasorleri listelenemedi: {e}")
        return []


def _load_all() -> dict:
    """Tüm driver alt-paketlerini bir kez yükle ve (BRAND, MODEL) → mod sözlüğü döndür."""
    global _cache # _cache, modüller yüklendikten sonra burada saklanır; sonraki çağrılarda yeniden yüklenmez.
    if _cache is not None: # Eğer zaten yüklendiyse, önbelleği döndür.
        return _cache #

    _cache = {} # Driver modülleri burada saklanır; anahtar (BRAND, MODEL) çiftidir. BRAND boş olabilir, bu durumda sadece MODEL'e bakılır.

    for entry in _driver_paketleri():
        # driver.py var mı diye diske BAKILMAZ (paketlenmiş uygulamada disk yok);
        # doğrudan import denenir, yoksa aşağıdaki except zaten yakalar.
        try:
            mod = importlib.import_module(f"common.cpe_drivers.{entry}.driver") # driver.py modülünü içe aktarır; hata olursa atlanır
        except Exception as e:
            print(f"[cpe_drivers] '{entry}' yüklenemedi: {e}")
            continue

        if not hasattr(mod, "MODEL"):
            print(f"[cpe_drivers] '{entry}/driver.py' MODEL tanımlamamış, atlandı.")
            continue

        brand = (getattr(mod, "BRAND", "") or "").upper().strip()
        model = mod.MODEL.upper().strip()
        _cache[(brand, model)] = mod

    return _cache


def _norm(s: str) -> str:
    """Karşılaştırma için normalize: BÜYÜK harf + boşluk yok + trim."""
    return (s or "").upper().replace(" ", "").strip()


def get_driver(brand: str, model: str):
    """
    Verilen marka/model için driver modülünü döndür.

    Lookup üç aşamalı (ilk eşleşen kazanır):
      1. (BRAND, MODEL) tam eşleşme
      2. Sadece MODEL tam eşleşme (brand göz ardı)
      3. Substring eşleşmesi — iki yönlü, normalize edilmiş (boşluk yok, uppercase):
           a) DIRECT  (öncelik 2): driver MODEL fmodel içinde
              Örn. 'H298A' in 'ZXHNH298AV1.0' → eşleşir
                   'H3600' in 'H3600V9'       → eşleşir
                   'H3600' in 'H3600PV9.0'    → eşleşir (H3600 alt-substring)
           b) REVERSE (öncelik 1): fmodel driver MODEL içinde
              Örn. 'DX3300' in 'DX3300-T1' → eşleşir
                   'H1601'  in 'H1601P'    → eşleşir
         Tüm eşleşmeler en az 4 karakter olmalı (over-match önler).
         Aynı öncelikte birden çok aday varsa EN UZUN eşleşme kazanır.

    Bulunamazsa KeyError fırlatır.
    """
    drivers = _load_all()
    nbrand = (brand or "").upper().strip()
    nmodel_raw = (model or "").upper().strip()
    key = (nbrand, nmodel_raw)
    fmodel_n = _norm(model)

    # 1) Tam (brand, model) eşleşmesi (uppercase ile)
    if key in drivers:
        return drivers[key]

    # 2) Sadece MODEL tam eşleşme (boşluk dahil exact)
    for (_b, m), mod in drivers.items():
        if m == nmodel_raw and nmodel_raw:
            return mod

    # 3) Normalize edilmiş substring eşleşmesi (iki yönlü)
    if fmodel_n:
        MIN_LEN = 4  # 3 karakter ve kısa eşleşmeleri ele (false positive önle)
        candidates = []  # (öncelik, eşleşme_uzunluğu, mod)

        for (_b, m), mod in drivers.items():
            if not m:
                continue
            m_norm = _norm(m)

            # a) DIRECT — driver MODEL frontend modelinde geçiyor (normalize)
            if len(m_norm) >= MIN_LEN and m_norm in fmodel_n:
                candidates.append((2, len(m_norm), mod))
                continue

            # b) REVERSE — frontend modeli driver MODEL içinde
            if len(fmodel_n) >= MIN_LEN and fmodel_n in m_norm:
                candidates.append((1, len(fmodel_n), mod))

        if candidates:
            # Önce yüksek öncelik, sonra uzun eşleşme
            candidates.sort(reverse=True)
            return candidates[0][2]

    supported = [f"{b}/{m}" if b else m for (b, m) in drivers.keys()]
    raise KeyError(
        f"'{brand}/{model}' için CPE driver bulunamadı. "
        f"Desteklenen: {supported}"
    )


def list_supported() -> list[dict]:
    """Kayıtlı tüm marka/model çiftlerini döndürür."""
    drivers = _load_all()
    return [{"brand": b, "model": m} for (b, m) in drivers.keys()]
