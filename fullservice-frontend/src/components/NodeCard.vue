<template>
  <v-card class="node-card" rounded="xl" elevation="0">
    <div class="node-head">
      <div class="head-left">
        <div class="title-row">
          <v-icon :icon="connIcon" size="20" class="mr-2" />
          <span class="node-label">{{ node.label }}</span>
        </div>
        <div class="meta-row text-caption text-medium-emphasis">
          {{ metaText }}
        </div>
      </div>
      <div class="head-right">
        <span class="status-dot" :class="dotClass" :title="stateText"></span>
        <span class="ml-2 text-caption">{{ stateText }}</span>
      </div>
    </div>

    <v-divider class="opacity-10" />

    <div class="tests-wrap pa-4">
      <p v-if="!node.roles?.length" class="empty-line text-body-2 text-medium-emphasis">
        Bu düğüme atanmış test yok.
      </p>
      <TestRow
        v-for="r in node.roles"
        :key="r"
        :task-key="r"
        :label="labels[r] || r"
        :test="node.tests?.[r] || {}"
      />
    </div>
  </v-card>
</template>

<script setup>
import { computed } from 'vue'
import TestRow from '@/components/TestRow.vue'
import { useAppStore } from '@/store/app'

const props = defineProps({
  node:   { type: Object, required: true },
  labels: { type: Object, default: () => ({}) },
})

const appStore = useAppStore()

// Online ışığı, sağ panelle AYNI health-check sonucundan beslenir (aynı periyotlar).
// Health-check başlatılana kadar nötr (gri) durur — baştan online göstermez.
const hc = computed(() => appStore.health.results[props.node.node_id])
const dotClass = computed(() => {
  if (!appStore.health.run || !hc.value) return ''            // nötr/gri
  return hc.value.reachable ? 'online' : 'offline'
})
const stateText = computed(() => {
  if (!appStore.health.run) return 'kontrol bekleniyor'
  if (!hc.value) return appStore.health.running ? 'kontrol…' : '—'
  return hc.value.reachable ? 'ÇEVRİMİÇİ' : 'ÇEVRİMDIŞI'
})

const connIcon = computed(() => (props.node.conn === 'wifi' ? 'mdi-wifi' : props.node.conn === 'cable' ? 'mdi-ethernet' : 'mdi-server'))
const metaText = computed(() => {
  const parts = [props.node.platform, props.node.ip].filter(Boolean)
  return parts.length ? parts.join(' · ') : 'çevrimdışı'
})
</script>

<style scoped lang="scss">
.node-card {
  background: rgba(22, 22, 30, 0.55) !important;
  backdrop-filter: blur(30px);
  -webkit-backdrop-filter: blur(30px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  display: flex; flex-direction: column;
}
.node-head { display: flex; justify-content: space-between; align-items: center; padding: 14px 18px; }
.title-row { display: flex; align-items: center; }
.node-label { font-weight: 700; font-size: 15px; letter-spacing: 0.4px; }
.meta-row { margin-top: 2px; opacity: 0.7; }

.status-dot {
  width: 9px; height: 9px; border-radius: 50%;
  background: #555; display: inline-block; transition: background 0.3s;
}
.status-dot.online {
  background: #30D158;
  box-shadow: 0 0 8px #30D158;
}
.status-dot.offline {
  background: #FF453A;
  box-shadow: 0 0 6px rgba(255,69,58,0.5);
}

.tests-wrap { display: flex; flex-direction: column; gap: 14px; }
.empty-line { font-style: italic; }
</style>
