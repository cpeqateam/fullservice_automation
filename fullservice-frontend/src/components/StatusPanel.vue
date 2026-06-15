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

    <!-- Düğüm ışıkları -->
    <div class="px-4 py-2">
      <div
        v-for="n in appStore.nodes"
        :key="n.node_id"
        class="node-row"
      >
        <span class="conn-dot" :class="dotClass(n.node_id)" />
        <div class="node-info">
          <span class="node-name">{{ n.label }}</span>
          <span class="node-sub">{{ subText(n) }}</span>
        </div>
        <span class="node-state" :class="stateClass(n.node_id)">{{ stateText(n.node_id) }}</span>
      </div>

      <p v-if="!appStore.nodes.length" class="text-caption text-medium-emphasis text-center py-4">
        Düğümler yükleniyor…
      </p>
    </div>

    <v-divider class="border-opacity-15 mx-3 my-2" />

    <!-- Health-Check Butonu -->
    <div class="px-3 pb-3">
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
      <p class="hc-hint">
        Aşamalı kontrol: 1sn×3 → 3sn×3 → 5sn×3 → 15sn → 30sn → sürekli 60sn.
      </p>
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
  return r.reachable ? 'Bağlı' : 'Yok'
}

function subText(n) {
  const r = result(n.node_id)
  const parts = [n.platform, n.ip].filter(Boolean)
  if (r?.reachable && r.latency_ms != null) parts.push(`${r.latency_ms} ms`)
  return parts.join(' · ') || (n.is_server ? 'sunucu' : 'bağlı değil')
}

function onHealthCheck() {
  // Buton bir kez basılınca aşamalı kontrol başlar; program kapanana dek sürer.
  // Tekrar basılırsa store mükerrer timer'ı engelleyip yeniden başlatır.
  appStore.startHealthCheck()
}
</script>

<style scoped lang="scss">
.status-panel {
  background: rgba(20, 20, 28, 0.55) !important;
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  position: sticky;
  top: 88px;
}
.sp-header .sp-title {
  font-size: 12px; font-weight: 700; letter-spacing: 0.08em;
  opacity: 0.9;
}
.sp-time {
  font-size: 12px; opacity: 0.4;
  font-variant-numeric: tabular-nums;
}
.node-row {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 2px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  &:last-child { border-bottom: none; }
}
.node-info { display: flex; flex-direction: column; flex: 1; min-width: 0; }
.node-name { font-size: 13px; font-weight: 600; }
.node-sub  {
  font-size: 11px; opacity: 0.5;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.node-state { font-size: 12px; font-weight: 600; }

.conn-dot {
  width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0;
  &--on  { background: #30D158; box-shadow: 0 0 8px rgba(48,209,88,0.7); animation: pulse-green 2s infinite; }
  &--off { background: #FF453A; box-shadow: 0 0 6px rgba(255,69,58,0.5); }
  &--idle { background: #555; }
}
.hc-btn { font-size: 12px; font-weight: 600; letter-spacing: 0.04em; }
.hc-hint {
  font-size: 10px; opacity: 0.4; margin-top: 6px; line-height: 1.4;
  text-align: center;
}
@keyframes pulse-green {
  0%, 100% { opacity: 1; }
  50%      { opacity: 0.5; }
}
</style>
