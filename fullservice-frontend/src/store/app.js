// Global uygulama durumu (dashboard):
//  • backend /api/state'i 1 sn'de bir polling ile çeker, nodes/session/labels
//    state'lerini tazeler.
//  • tema değişimini localStorage ile kalıcı kılar.
//  • testi başlat/durdur eylemlerini sarar.
import { defineStore } from 'pinia'
import { fetchState, startSession, stopSession } from '@/services/api'

export const useAppStore = defineStore('app', {
  state: () => ({
    isDarkMode: localStorage.getItem('fs_theme') !== 'light',

    // Backend'den gelen birleşik durum (orchestrator.get_state)
    session:     { session_id: null, running: false, started_at: null, ended_at: null, params: {} },
    nodes:       [],
    testLabels:  {},
    serverLanIp: null,

    // Polling kontrolü
    connected:    false,
    pollingTimer: null,

    // Kullanıcı override'ları (boş bırakılan config.json varsayılanını kullanır)
    overrides: { duration: '', modem_ip: '', internet_ip: '', youtube_link: '' },
  }),

  getters: {
    nodeCount:     (s) => s.nodes.length,
    onlineCount:   (s) => s.nodes.filter((n) => n.online).length,
    sessionStatus: (s) => (s.session.running ? 'running' : s.session.session_id ? 'done' : 'idle'),
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

    async startTest() {
      // Boş alanları göndermiyoruz → backend config.json varsayılanını kullanır.
      const body = {}
      const o = this.overrides
      if (o.duration)     body.duration     = parseInt(o.duration)
      if (o.modem_ip)     body.modem_ip     = o.modem_ip.trim()
      if (o.internet_ip)  body.internet_ip  = o.internet_ip.trim()
      if (o.youtube_link) body.youtube_link = o.youtube_link.trim()

      const res = await startSession(body)
      await this.refresh()
      return res
    },

    async stopTest() {
      await stopSession()
      await this.refresh()
    },

    toggleTheme() {
      this.isDarkMode = !this.isDarkMode
      localStorage.setItem('fs_theme', this.isDarkMode ? 'dark' : 'light')
    },
  },
})
