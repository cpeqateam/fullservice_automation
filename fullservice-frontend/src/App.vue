<template>
  <v-app :theme="appStore.isDarkMode ? 'dark' : 'light'" class="app-root">
    <LiquidBackground />

    <Topbar />

    <v-main>
      <v-container fluid class="py-6">
        <v-row>
          <!-- Ana içerik: cihaz formu + canlı test izleme -->
          <v-col cols="12" lg="9">
            <!-- Cihaz/test formu dar tutulur; alttaki ilerleme kartları tam genişlikte kalır -->
            <div class="form-wrap mb-5">
              <DeviceForm />
            </div>

            <div v-if="!appStore.nodes.length" class="empty">
              <v-progress-circular indeterminate color="primary" size="48" />
              <p class="mt-4 text-body-2 text-medium-emphasis">Sunucuya bağlanılıyor…</p>
            </div>

            <div v-else class="node-grid">
              <NodeCard v-for="n in appStore.nodes" :key="n.node_id" :node="n" :labels="appStore.testLabels" />
            </div>
          </v-col>

          <!-- Sağ panel: health-check + bağlantı ışıkları -->
          <v-col cols="12" lg="3">
            <StatusPanel />
          </v-col>
        </v-row>
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
import DeviceForm from '@/components/DeviceForm.vue'
import StatusPanel from '@/components/StatusPanel.vue'
import NodeCard from '@/components/NodeCard.vue'

const appStore = useAppStore()

onMounted(() => {
  appStore.startPolling(1000)
  appStore.loadBrands()
})
onBeforeUnmount(() => {
  appStore.stopPolling()
  appStore.stopHealthCheck()
})
</script>

<style>
.app-root .v-application__wrap { background: transparent !important; }
/* Cihaz/test formu kartı dar tutulur — eskiden tüm kolonu kaplıyordu */
.form-wrap { max-width: 600px; }
.empty { display: flex; flex-direction: column; align-items: center; padding: 80px 0; }
.node-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 18px;
}
.foot {
  background: rgba(0,0,0,0.3) !important;
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255,255,255,0.06);
}
</style>
