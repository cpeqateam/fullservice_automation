# FULL Servis — Frontend (Vue 3 + Vuetify 3)

Backend'in canlı durumunu (4 düğüm × her düğümün test ilerlemesi) tek ekranda
gösteren dashboard. Dağıtık testin tüm cihazlarından akan veriyi anlık birleştirir,
"FULL Servis Başlat / Durdur" tek tuşla işletir.

## Teknoloji
- **Vue 3** (Composition API, `<script setup>`)
- **Vuetify 3** (Material bileşenler) + `@mdi/font`
- **Pinia** (state + 1 sn polling)
- **Axios** (backend `/api`)
- **Vite** (dev + build)
- SCSS (glass-card + animasyonlu LiquidBackground)

## Tema
Türk Telekom magenta vurgulu **dark/light** tema. Logo
`asset.turktelekom.com.tr` üzerinden alınır; başlıkta sade Türk Telekom kimliği
ile **FULL SERVİS** branding'i kombinlenir.

## Çalıştırma

### Geliştirme (dev — HMR'lı)
Backend ayağa kalkmış olmalı (`fullservice-backend/` dizininde `python run_server.py`).

```bash
cd fullservice-frontend
npm install
npm run dev               # http://localhost:5173
```

Vite, `/api/*` isteklerini `http://localhost:8770`'e proxy'ler.

### Üretim (build)
```bash
npm run build             # dist/ oluşturur
```
`dist/` üretildikten sonra backend (kardeş klasör) bunu **otomatik olarak**
statik servis eder (bkz. `fullservice-backend/common/config.py → DASHBOARD_DIR`).
Tek başına backend'i çalıştırıp `http://<sunucu>:8770` adresinden aynı UI'a
ulaşırsın.

## Kaynak ağacı
```
src/
├── main.js                    # Vue + Pinia + Vuetify + global SCSS
├── App.vue                    # üst layout: arkaplan + topbar + control + grid
├── plugins/vuetify.js         # tema (TT magenta + secondary mavi)
├── store/
│   ├── index.js               # Pinia örneği
│   └── app.js                 # nodes/session/deviceInfo + polling + firmware + health-check
├── services/api.js            # axios + state/session + firmware + health-check
├── components/
│   ├── LiquidBackground.vue   # animasyonlu renk lekeleri (arkaplan)
│   ├── Topbar.vue             # logo + başlık + oturum chip + tema toggle
│   ├── DeviceForm.vue         # Marka/Model/Firmware + Süre + Başlat/Durdur (GRK Günlük Rutin sekmesi örnek)
│   ├── StatusPanel.vue        # sağ panel: aşamalı Health-Check + kırmızı/yeşil ışıklar
│   ├── NodeCard.vue           # tek düğüm kartı (4'lük gridin elemanı)
│   └── TestRow.vue            # tek test ilerleme satırı
└── assets/styles/main.scss    # global tipografi/scrollbar/tema overrideları
```

## Backend ile sözleşme

| Method | URL                                   | Kullanım                          |
|--------|---------------------------------------|-----------------------------------|
| GET    | `/api/state`                          | 1 sn polling — birleşik durum     |
| POST   | `/api/session/start`                  | Başlat (override + brand/model/firmware) |
| POST   | `/api/session/stop`                   | Durdur                            |
| GET    | `/api/health-check`                   | Aşamalı bağlantı kontrolü (ışıklar)|
| GET    | `/api/firmware/brands` · `/models/{b}` · `/versions/{b}/{m}` | combobox kaynağı (yoksa serbest metin) |

`fullservice-backend/server/main.py`'deki FastAPI router'ı tüm `/api/...` rotalarını
sağlar. Detay için repo kökündeki `MIMARI.md`.
