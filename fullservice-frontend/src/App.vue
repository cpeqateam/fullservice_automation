<template>
  <v-app :theme="appStore.isDarkMode ? 'dark' : 'light'" class="app-root">
    <LiquidBackground />

    <Topbar />

    <v-main>
      <v-container fluid class="py-6">
        <ControlBar />

        <div v-if="!appStore.nodes.length" class="empty">
          <v-progress-circular indeterminate color="primary" size="48" />
          <p class="mt-4 text-body-2 text-medium-emphasis">Sunucuya bağlanılıyor…</p>
        </div>

        <div v-else class="node-grid">
          <NodeCard v-for="n in appStore.nodes" :key="n.node_id" :node="n" :labels="appStore.testLabels" />
        </div>
      </v-container>
    </v-main>

    <v-footer app class="foot text-caption">
      <span :class="appStore.connected ? 'text-success' : 'text-error'">●</span>
      <span class="ml-2">Sunucu: {{ appStore.serverLanIp || '—' }}</span>
      <v-spacer />
      <span>Türk Telekom · CPE QA · Otomatik yenileme 1 sn</span>
    </v-footer>
  </v-app>
</template>

<script setup>
import { onMounted, onBeforeUnmount } from 'vue'
import { useAppStore } from '@/store/app'
import LiquidBackground from '@/components/LiquidBackground.vue'
import Topbar from '@/components/Topbar.vue'
import ControlBar from '@/components/ControlBar.vue'
import NodeCard from '@/components/NodeCard.vue'

const appStore = useAppStore()

onMounted(() => appStore.startPolling(1000))
onBeforeUnmount(() => appStore.stopPolling())
</script>

<style>
.app-root .v-application__wrap { background: transparent !important; }
.empty { display: flex; flex-direction: column; align-items: center; padding: 80px 0; }
.node-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(340px, 1fr));
  gap: 18px;
  margin-top: 18px;
}
.foot {
  background: rgba(0,0,0,0.3) !important;
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255,255,255,0.06);
}
</style>
