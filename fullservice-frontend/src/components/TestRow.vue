<template>
  <div class="test-row" :class="{ 'is-skipped': skipped }">
    <div class="row-line">
      <span class="row-name">
        <v-icon :icon="testIcon" size="14" class="mr-1 opacity-70" />
        {{ label }}
      </span>
      <span v-if="skipped" class="row-skip">ATLANDI</span>
      <span v-else-if="taskKey !== 'youtube'" class="row-pct">{{ pct }}%</span>
      <span v-else class="row-pct">▶</span>
    </div>
    <v-progress-linear
      :model-value="pct"
      :color="barColor"
      :indeterminate="false"
      height="8"
      rounded
      :class="status === 'running' ? 'bar-pulse' : ''"
    />
    <div class="row-msg text-caption text-medium-emphasis">
      {{ test.message || ' ' }}
    </div>
  </div>
</template>

<script setup>
// Tek bir testin canlı ilerleme satırı: ad + ikon + yüzde + renkli bar + mesaj.
// test objesi backend'den gelir ({ progress, status, message }); duruma göre
// bar rengi ve (running'de) yanıp sönme efekti seçilir.
import { computed } from 'vue'

const props = defineProps({
  taskKey: { type: String, required: true },   // TestType anahtarı (ping_modem, iperf, ...)
  label:   { type: String, required: true },   // insan-okunur etiket
  test:    { type: Object, default: () => ({}) }, // { progress, status, message }
})

const status = computed(() => props.test.status || 'idle')
const pct = computed(() => Math.round(props.test.progress || 0))
// Kullanıcı bu testin tikini kaldırmış: hiç başlatılmadı, satır gri durur.
const skipped = computed(() => status.value === 'skipped')

const barColor = computed(() => ({
  idle:      'grey-darken-2',
  running:   'warning',
  completed: 'success',
  error:     'error',
  stopped:   'orange',
  skipped:   'grey',
})[status.value] || 'grey-darken-2')

const testIcon = computed(() => ({
  ping_internet: 'mdi-earth',
  ping_modem:    'mdi-router-wireless',
  youtube:       'mdi-youtube',
  iperf:         'mdi-speedometer',
  torrent:       'mdi-download',
  wifi_track:    'mdi-signal-variant',
})[props.taskKey] || 'mdi-circle-medium')
</script>

<style scoped lang="scss">
.test-row { display: flex; flex-direction: column; gap: 4px; }
.row-line { display: flex; justify-content: space-between; align-items: center; font-size: 13px; }
.row-name { font-weight: 600; }
.row-pct  { font-size: 12px; opacity: 0.7; font-variant-numeric: tabular-nums; }
.row-msg  { min-height: 14px; }

/* Seçilmeyen test: satır tamamen soluk, adı üstü çizili, sağda ATLANDI rozeti */
.is-skipped { opacity: 0.45; }
.is-skipped .row-name { text-decoration: line-through; }
.row-skip {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 1px 6px;
  border-radius: 8px;
  color: rgba(var(--v-theme-on-surface), 0.7);
  background: rgba(var(--v-theme-on-surface), 0.10);
}

.bar-pulse :deep(.v-progress-linear__determinate) { animation: pulseBar 1.3s ease-in-out infinite; }
@keyframes pulseBar { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
</style>
