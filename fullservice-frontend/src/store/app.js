// Global uygulama durumu (dashboard):
//  • backend /api/state'i 1 sn'de bir polling ile çeker, nodes/session/labels
//    state'lerini tazeler.
//  • Marka/Model/Firmware listelerini firmware DB'den yükler (yoksa serbest-metin).
//  • Health-Check: aşamalı aralıklarla düğüm erişilebilirliğini ölçer.
//  • tema değişimini localStorage ile kalıcı kılar.
//  • testi başlat/durdur eylemlerini sarar.
import { defineStore } from 'pinia'
import {
  fetchState, startSession, stopSession,
  healthCheck, getBrands, getVersions,
} from '@/services/api'

// Aşamalı health-check planı (kullanıcı isteri):
//   1sn'de bir × 3 → 3sn × 3 → 5sn × 3 → 15sn × 1 → 30sn × 1 → sonra sürekli 60sn.
const HC_SCHEDULE = [
  { interval: 1000,  count: 3 },
  { interval: 3000,  count: 3 },
  { interval: 5000,  count: 3 },
  { interval: 15000, count: 1 },
  { interval: 30000, count: 1 },
  { interval: 60000, count: Infinity },
]

export const useAppStore = defineStore('app', {
  state: () => ({
    isDarkMode: localStorage.getItem('fs_theme') !== 'light',

    // Backend'den gelen birleşik durum (orchestrator.get_state)
    session:     { session_id: null, running: false, started_at: null, ended_at: null, params: {}, device: {} },
    nodes:       [],
    testLabels:  {},
    serverLanIp: null,

    // Polling kontrolü
    connected:    false,
    pollingTimer: null,

    // Cihaz bilgisi (Günlük Rutin Kontrol formu)
    deviceInfo: { brand: null, model: null, firmware: null },
    overrides:  { duration: '', modem_ip: '', internet_ip: '', youtube_link: '' },

    // Firmware DB
    brandsData:      [],     // [{ title, value, models: [...] }]
    firmwareOptions: [],
    brandsDbFailed:   false, // DB erişilemezse true → serbest-metin girişi
    firmwareDbFailed: false,

    // Health-Check
    health: {
      running:   false,
      checkedAt: null,
      results:   {},   // { node_id: { reachable, latency_ms } }
    },
    _hcTimer: null,
  }),

  getters: {
    nodeCount:     (s) => s.nodes.length,
    onlineCount:   (s) => s.nodes.filter((n) => n.online).length,
    sessionStatus: (s) => (s.session.running ? 'running' : s.session.session_id ? 'done' : 'idle'),
    brandOptions:  (s) => s.brandsData.map((b) => b.title),
    modelOptions:  (s) => {
      const b = s.brandsData.find((x) => x.title === s.deviceInfo.brand)
      return b ? b.models : []
    },
  },

  actions: {
    async refresh() {
      try {
        const data = await fetchState()
        this.session     = data.session     || this.session
        this.nodes       = data.nodes       || []
        this.testLabels  = data.test_labels || {}
        this.serverLanIp = data.server_lan_ip || null
        this.connected   = true
      } catch (e) {
        this.connected = false
      }
    },

    startPolling(intervalMs = 1000) {
      this.refresh()
      this.stopPolling()
      this.pollingTimer = setInterval(() => this.refresh(), intervalMs)
    },

    stopPolling() {
      if (this.pollingTimer) {
        clearInterval(this.pollingTimer)
        this.pollingTimer = null
      }
    },

    // ── Firmware DB ──────────────────────────────────────────
    async loadBrands() {
      try {
        this.brandsData = await getBrands()
        this.brandsDbFailed = false
      } catch (e) {
        console.warn('Marka/Model DB\'den alınamadı, serbest girişe açılıyor:', e)
        this.brandsData = []
        this.brandsDbFailed = true
      }
    },

    async loadFirmwares() {
      const { brand, model } = this.deviceInfo
      if (!brand || !model) { this.firmwareOptions = []; return }
      try {
        this.firmwareOptions = await getVersions(brand, model)
        this.firmwareDbFailed = false
      } catch (e) {
        console.warn('Firmware listesi alınamadı, serbest girişe açılıyor:', e)
        this.firmwareOptions = []
        this.firmwareDbFailed = true
      }
    },

    onBrandChange() {
      this.deviceInfo.model = null
      this.deviceInfo.firmware = null
      this.firmwareOptions = []
    },

    async onModelChange() {
      this.deviceInfo.firmware = null
      await this.loadFirmwares()
    },

    // ── Test başlat / durdur ─────────────────────────────────
    async startTest() {
      const body = {}
      const o = this.overrides
      if (o.duration)     body.duration     = parseInt(o.duration)
      if (o.modem_ip)     body.modem_ip     = o.modem_ip.trim()
      if (o.internet_ip)  body.internet_ip  = o.internet_ip.trim()
      if (o.youtube_link) body.youtube_link = o.youtube_link.trim()

      const d = this.deviceInfo
      if (d.brand)    body.brand    = d.brand
      if (d.model)    body.model    = d.model
      if (d.firmware) body.firmware = d.firmware

      const res = await startSession(body)
      await this.refresh()
      return res
    },

    async stopTest() {
      await stopSession()
      await this.refresh()
    },

    // ── Health-Check (aşamalı) ───────────────────────────────
    async _runHealthCheck() {
      try {
        const data = await healthCheck()
        this.health.results   = data.results || {}
        this.health.checkedAt = data.checked_at || null
      } catch (e) {
        // Sunucuya ulaşılamadıysa hepsini erişilemez işaretle
        const r = {}
        for (const n of this.nodes) r[n.node_id] = { reachable: false, latency_ms: null }
        this.health.results = r
      }
    },

    // Buton bir kez basılınca: aşamalı plan boyunca ilerler, son aşamada
    // sürekli 60sn'de bir devam eder (program/sayfa kapanana dek).
    startHealthCheck() {
      this.stopHealthCheck()   // tekrar basılırsa mükerrer timer engellenir
      this.health.running = true

      let stage = 0
      let done  = 0   // mevcut aşamada yapılan kontrol sayısı

      const tick = async () => {
        await this._runHealthCheck()
        if (!this.health.running) return

        done += 1
        const cur = HC_SCHEDULE[stage]
        if (done >= cur.count && stage < HC_SCHEDULE.length - 1) {
          stage += 1
          done = 0
        }
        const interval = HC_SCHEDULE[stage].interval
        this._hcTimer = setTimeout(tick, interval)
      }

      // İlk kontrol hemen, sonra plana göre zincirle.
      tick()
    },

    stopHealthCheck() {
      this.health.running = false
      if (this._hcTimer) {
        clearTimeout(this._hcTimer)
        this._hcTimer = null
      }
    },

    toggleTheme() {
      this.isDarkMode = !this.isDarkMode
      localStorage.setItem('fs_theme', this.isDarkMode ? 'dark' : 'light')
    },
  },
})
