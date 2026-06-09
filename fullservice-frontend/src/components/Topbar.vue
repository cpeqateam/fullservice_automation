<template>
  <v-app-bar app flat class="topbar" height="74">
    <div class="brand pl-4 pr-2 d-flex align-center">
      <img
        src="https://asset.turktelekom.com.tr/SiteAssets/images/logo.svg"
        alt="Türk Telekom"
        class="brand-logo"
      />
      <div class="brand-text ml-4">
        <div class="brand-title">FULL SERVİS</div>
        <div class="brand-sub">Modem Stres Test Orkestrasyonu</div>
      </div>
    </div>

    <v-spacer />

    <v-chip
      class="session-chip mr-3"
      :color="chipColor"
      :prepend-icon="chipIcon"
      variant="elevated"
      density="comfortable"
    >
      {{ chipLabel }}
      <span v-if="appStore.session.session_id" class="ml-2 session-id">
        {{ appStore.session.session_id }}
      </span>
    </v-chip>

    <v-btn
      :icon="appStore.isDarkMode ? 'mdi-weather-night' : 'mdi-white-balance-sunny'"
      variant="text"
      @click="appStore.toggleTheme()"
      class="mr-2"
    />
  </v-app-bar>
</template>

<script setup>
import { computed } from 'vue'
import { useAppStore } from '@/store/app'
const appStore = useAppStore()

const chipLabel = computed(() => {
  if (appStore.session.running) return 'ÇALIŞIYOR'
  if (appStore.session.session_id) return 'TAMAMLANDI'
  return 'HAZIR'
})
const chipColor = computed(() => {
  if (appStore.session.running) return 'warning'
  if (appStore.session.session_id) return 'success'
  return 'grey-darken-1'
})
const chipIcon = computed(() => {
  if (appStore.session.running) return 'mdi-play-circle'
  if (appStore.session.session_id) return 'mdi-check-circle'
  return 'mdi-circle-outline'
})
</script>

<style scoped lang="scss">
.topbar {
  background: rgba(0, 0, 0, 0.35) !important;
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.brand-logo { height: 28px; }
.brand-text { line-height: 1.1; }
.brand-title {
  font-weight: 800;
  font-size: 18px;
  letter-spacing: 1.5px;
}
.brand-sub {
  font-size: 11px;
  opacity: 0.65;
  letter-spacing: 0.5px;
}
.session-chip { font-weight: 600; letter-spacing: 0.6px; }
.session-id { font-family: ui-monospace, "SF Mono", monospace; font-size: 11px; opacity: 0.8; }
</style>
