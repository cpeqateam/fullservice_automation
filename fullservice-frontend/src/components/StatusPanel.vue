<template>
  <v-card class="status-panel pa-0" rounded="xl" elevation="0">
    <!-- Başlık -->
    <div class="sp-header d-flex align-center gap-2 px-4 py-3">
      <v-icon size="18" color="primary">mdi-monitor-dashboard</v-icon>
      <span class="sp-title">BAĞLANTI DURUMU</span>
      <v-spacer />
      <span v-if="appStore.health.checkedAt" class="sp-time">{{ shortTime }}</span>
    </div>

    <v-divider class="border-opacity-15 mx-3 mb-2" />

    <!-- Düğüm kartları (kaydırılabilir alan; paneli alta kadar doldurur) -->
    <div class="sp-body px-3 py-2">
      <div
        v-for="n in appStore.nodes"
        :key="n.node_id"
        class="node-block"
      >
        <!-- Üst satır: ışık + ad + durum -->
        <div class="node-top">
          <span class="conn-dot" :class="dotClass(n.node_id)" />
          <span class="node-name">{{ n.label }}</span>
          <v-spacer />
          <span class="node-state" :class="stateClass(n.node_id)">{{ stateText(n.node_id) }}</span>
        </div>

        <!-- 2×2 açıklayıcı bilgi ızgarası -->
        <div class="info-grid">
          <div class="info-cell">
            <v-icon size="13" class="info-ic">mdi-laptop</v-icon>
            <div class="info-text">
              <span class="info-label">İşletim Sistemi</span>
              <span class="info-value">{{ osText(n) }}</span>
            </div>
          </div>
          <div class="info-cell">
            <v-icon size="13" class="info-ic">mdi-ip-network</v-icon>
            <div class="info-text">
              <span class="info-label">IP Adresi</span>
              <span class="info-value">{{ n.ip || '—' }}</span>
            </div>
          </div>
          <div class="info-cell">
            <v-icon size="13" class="info-ic">mdi-lan-connect</v-icon>
            <div class="info-text">
              <span class="info-label">Bağlantı Durumu</span>
              <span class="info-value" :class="stateClass(n.node_id)">{{ connStatusText(n.node_id) }}</span>
            </div>
          </div>
          <div class="info-cell">
            <v-icon size="13" class="info-ic">{{ connMethodIcon(n) }}</v-icon>
            <div class="info-text">
              <span class="info-label">Bağlantı Yöntemi</span>
              <span class="info-value">{{ connMethodText(n) }}</span>
            </div>
          </div>
        </div>

        <!-- Uptime satırı -->
        <div class="uptime-row mt-2">
          <v-icon size="13" class="info-ic mr-1">mdi-clock-outline</v-icon>
          <span class="info-label mr-1">Uptime:</span>
          <span class="uptime-val" :class="appStore.health.run ? uptimeClass(n) : ''">{{ appStore.health.run ? uptimeText(n) : '—' }}</span>
        </div>
      </div>

      <p v-if="!appStore.nodes.length" class="text-caption text-medium-emphasis text-center py-4">
        Düğümler yükleniyor…
      </p>
    </div>

    <!-- Health-Check Butonu (panelin altına sabit) -->
    <div class="sp-footer px-3 pb-3 pt-1">
      <v-divider class="border-opacity-15 mb-3" />
      <v-btn
        block
        size="small"
        variant="outlined"
        :color="appStore.health.running ? 'primary' : 'grey'"
        rounded="lg"
        class="hc-btn"
        @click="onHealthCheck"
      >
        <v-icon size="15" class="mr-1">mdi-shield-search</v-icon>
        {{ appStore.health.running ? 'Kontrol Çalışıyor…' : 'Health-Check' }}
      </v-btn>
    </div>
  </v-card>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/store/app'

const appStore = useAppStore()

const shortTime = computed(() => {
  const t = appStore.health.checkedAt
  if (!t) return ''
  try { return new Date(t).toLocaleTimeString('tr-TR', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) }
  catch { return t }
})

function result(nodeId) {
  return appStore.health.results[nodeId]
}

function dotClass(nodeId) {
  const r = result(nodeId)
  if (!r) return 'conn-dot--idle'
  return r.reachable ? 'conn-dot--on' : 'conn-dot--off'
}

function stateClass(nodeId) {
  const r = result(nodeId)
  if (!r) return 'text-medium-emphasis'
  return r.reachable ? 'text-green-lighten-2' : 'text-red-lighten-2'
}

function stateText(nodeId) {
  const r = result(nodeId)
  if (!r) return appStore.health.running ? 'kontrol…' : '—'
  return r.reachable ? 'ÇEVRİMİÇİ' : 'ÇEVRİMDIŞI'
}

// "Bağlantı Durumu" hücresi için daha açıklayıcı metin
function connStatusText(nodeId) {
  const r = result(nodeId)
  if (!r) return appStore.health.running ? 'Kontrol ediliyor…' : 'Bilinmiyor'
  if (!r.reachable) return 'ÇEVRİMDIŞI'
  return r.latency_ms != null ? `ÇEVRİMİÇİ · ${r.latency_ms} ms` : 'ÇEVRİMİÇİ'
}

// İşletim sistemini insan-okunur ada çevirir (platform: "Linux"|"Darwin"|"Windows")
function osText(n) {
  const p = (n.platform || '').toLowerCase()
  if (p.includes('darwin') || p.includes('mac')) return 'macOS'
  if (p.includes('win')) return 'Windows'
  if (p.includes('linux')) return 'Linux'
  return n.platform || '—'
}

function connMethodText(n) {
  if (n.conn === 'wifi') return 'Wi-Fi'
  if (n.conn === 'cable') return 'Kablo (Ethernet)'
  return '—'
}
function connMethodIcon(n) {
  if (n.conn === 'wifi') return 'mdi-wifi'
  if (n.conn === 'cable') return 'mdi-ethernet'
  return 'mdi-help-network'
}

function uptimeMinutes(n) {
  if (!n.agent_started_at) return null
  try {
    const ms = Date.now() - new Date(n.agent_started_at).getTime()
    return Math.floor(ms / 60000)
  } catch { return null }
}
function uptimeText(n) {
  const m = uptimeMinutes(n)
  if (m === null) return '—'
  if (m < 60) return `${m} dakikadır açık.`
  const h = Math.floor(m / 60), rem = m % 60
  return `${h} sa ${rem} dakikadır açık.`
}
function uptimeClass(n) {
  const m = uptimeMinutes(n)
  if (m === null) return ''
  return m >= 45 ? 'uptime-warn' : 'uptime-ok'
}

function onHealthCheck() {
  // Buton bir kez basılınca aşamalı kontrol başlar; program kapanana dek sürer.
  // Tekrar basılırsa store mükerrer timer'ı engelleyip yeniden başlatır.
  appStore.startHealthCheck()
}
</script>

<style scoped lang="scss">
.status-panel {
  background: rgba(20, 26, 36, 0.55) !important;
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  position: sticky;
  top: 104px;
  // Ekran yüksekliğine sığar (monitör/laptop'a göre vh ile uyum); içerik taşarsa
  // gövde kendi içinde kayar, Health-Check butonu HEP altta görünür kalır.
  height: calc(100vh - 176px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.sp-header .sp-title {
  font-size: 12px; font-weight: 700; letter-spacing: 0.08em;
  opacity: 0.9;
}
.sp-time {
  font-size: 12px; opacity: 0.4;
  font-variant-numeric: tabular-nums;
}

// Düğüm kartları alanı büyür (flex:1) → buton dibe yapışır.
.sp-body {
  flex: 1 1 auto;
  overflow-y: auto;
}

.node-block {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  padding: 7px 10px;
  margin-bottom: 7px;
  &:last-child { margin-bottom: 4px; }
}
.node-top {
  display: flex; align-items: center; gap: 7px;
  margin-bottom: 6px;
}
.node-name { font-size: 12px; font-weight: 600; }
.node-state { font-size: 11px; font-weight: 600; }

.info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 5px 8px;
}
.info-cell {
  display: flex; align-items: flex-start; gap: 4px;
  min-width: 0;
}
.info-ic { opacity: 0.45; margin-top: 1px; }
.info-text { display: flex; flex-direction: column; min-width: 0; }
.info-label {
  font-size: 8.5px; letter-spacing: 0.04em; text-transform: uppercase;
  opacity: 0.45;
}
.info-value {
  font-size: 11px; font-weight: 500;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

.uptime-row {
  display: flex; align-items: center;
  font-size: 10.5px; margin-top: 5px;
}
.uptime-val { font-weight: 700; font-size: 11px; }
.uptime-ok   { color: #30D158; }
.uptime-warn { color: #FF453A; }

.sp-footer { flex-shrink: 0; }

.conn-dot {
  width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0;
  &--on  { background: #30D158; box-shadow: 0 0 8px rgba(48,209,88,0.7); animation: pulse-green 2s infinite; }
  &--off { background: #FF453A; box-shadow: 0 0 6px rgba(255,69,58,0.5); }
  &--idle { background: #555; }
}
.hc-btn { font-size: 12px; font-weight: 600; letter-spacing: 0.04em; }
@keyframes pulse-green {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.5; }
}
</style>
