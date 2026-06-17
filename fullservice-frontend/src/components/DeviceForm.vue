<template>
  <v-card class="device-form pa-6" rounded="xl" elevation="0">
    <div class="d-flex align-center mb-5">
      <div class="icon-box mr-3">
        <v-icon icon="mdi-cog" color="white" size="20" />
      </div>
      <h2 class="text-h6 font-weight-bold mb-0">Cihaz ve Test Bilgileri</h2>
    </div>

    <!-- DB bağlantı hatası uyarısı — kompakt tek satır -->
    <div
      v-if="appStore.brandsDbFailed || appStore.firmwareDbFailed"
      class="db-warn-line mb-3"
    >
      <v-icon size="15" color="warning" class="mr-2">mdi-database-alert</v-icon>
      <span>DB yok — alanlar serbest metne açıldı.</span>
    </div>

    <v-form @submit.prevent="onStart" class="form-body d-flex flex-column flex-grow-1">
      <!-- Marka -->
      <div class="field-row">
        <label class="field-label">Marka</label>
        <v-select
          v-if="!appStore.brandsDbFailed"
          v-model="appStore.deviceInfo.brand"
          :items="appStore.brandOptions"
          placeholder="Marka Seçiniz…"
          variant="solo-filled" density="comfortable" hide-details flat
          menu-icon="mdi-chevron-down"
          @update:model-value="appStore.onBrandChange()"
        />
        <v-combobox
          v-else
          v-model="appStore.deviceInfo.brand"
          :items="appStore.brandOptions"
          placeholder="Marka Yazınız…"
          variant="solo-filled" density="comfortable" hide-details flat
          menu-icon="mdi-chevron-down"
          @update:model-value="appStore.onBrandChange()"
        />
      </div>

      <!-- Model -->
      <div class="field-row">
        <label class="field-label">Model</label>
        <v-select
          v-if="!appStore.brandsDbFailed"
          v-model="appStore.deviceInfo.model"
          :items="appStore.modelOptions"
          :disabled="!appStore.deviceInfo.brand"
          placeholder="Model Seçiniz…"
          variant="solo-filled" density="comfortable" hide-details flat
          menu-icon="mdi-chevron-down"
          @update:model-value="appStore.onModelChange()"
        />
        <v-combobox
          v-else
          v-model="appStore.deviceInfo.model"
          :items="appStore.modelOptions"
          :disabled="!appStore.deviceInfo.brand"
          placeholder="Model Yazınız…"
          variant="solo-filled" density="comfortable" hide-details flat
          menu-icon="mdi-chevron-down"
          @update:model-value="appStore.onModelChange()"
        />
      </div>

      <!-- Firmware -->
      <div class="field-row">
        <label class="field-label">Firmware</label>
        <v-select
          v-if="!appStore.brandsDbFailed && !appStore.firmwareDbFailed"
          v-model="appStore.deviceInfo.firmware"
          :items="appStore.firmwareOptions"
          :disabled="!appStore.deviceInfo.model"
          placeholder="Firmware Seçiniz…"
          variant="solo-filled" density="comfortable" hide-details flat
          menu-icon="mdi-chevron-down"
        />
        <v-combobox
          v-else
          v-model="appStore.deviceInfo.firmware"
          :items="appStore.firmwareOptions"
          :disabled="!appStore.deviceInfo.model"
          placeholder="Firmware Yazınız…"
          variant="solo-filled" density="comfortable" hide-details flat
          menu-icon="mdi-chevron-down"
        />
      </div>

      <!-- Süre -->
      <div class="field-row">
        <label class="field-label">Süre (sn)</label>
        <v-text-field
          v-model="appStore.overrides.duration"
          type="number"
          placeholder="varsayılan"
          variant="solo-filled"
          density="comfortable"
          hide-details
          flat
        />
      </div>

      <!-- Oturum & ilerleme özeti — boş alanı canlı bilgiyle doldurur -->
      <div class="summary mt-5">
        <div class="summary-head">
          <span class="summary-title">OTURUM DURUMU</span>
          <v-chip size="x-small" :color="statusChip.color" variant="flat" class="font-weight-bold">
            {{ statusChip.label }}
          </v-chip>
        </div>

        <div class="summary-row">
          <span class="sr-key">Cihaz</span>
          <span class="sr-val">{{ deviceLabel }}</span>
        </div>
        <div class="summary-row">
          <span class="sr-key">Süre</span>
          <span class="sr-val">{{ appStore.overrides.duration || 'varsayılan' }} sn</span>
        </div>
        <div class="summary-row">
          <span class="sr-key">Oturum</span>
          <span class="sr-val mono">{{ appStore.session.session_id || '—' }}</span>
        </div>

        <div class="summary-row mt-3">
          <span class="sr-key">Genel ilerleme</span>
          <span class="sr-val">%{{ appStore.testSummary.avg }}</span>
        </div>
        <v-progress-linear
          :model-value="appStore.testSummary.avg"
          color="primary" height="8" rounded class="mt-1"
        />

        <div class="counts mt-3">
          <span class="count"><span class="dot running" /> {{ appStore.testSummary.running }} çalışıyor</span>
          <span class="count"><span class="dot done" /> {{ appStore.testSummary.completed }} bitti</span>
          <span class="count"><span class="dot err" /> {{ appStore.testSummary.error }} hata</span>
          <v-spacer />
          <span class="count total">{{ appStore.testSummary.completed }}/{{ appStore.testSummary.total }}</span>
        </div>
      </div>

      <div class="d-flex action-buttons mt-auto pt-6">
        <v-btn
          color="primary"
          size="large"
          prepend-icon="mdi-play"
          :loading="starting"
          :disabled="appStore.session.running"
          class="flex-grow-1"
          rounded="lg"
          @click="onStart"
        >
          FULL Servis Başlat
        </v-btn>
        <v-btn
          color="error"
          size="large"
          variant="outlined"
          prepend-icon="mdi-stop"
          :disabled="!appStore.session.running"
          rounded="lg"
          @click="onStop"
        >
          Durdur
        </v-btn>
      </div>
    </v-form>

    <v-snackbar v-model="snack.show" :color="snack.color" :timeout="5000" location="top">
      {{ snack.text }}
    </v-snackbar>
  </v-card>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useAppStore } from '@/store/app'

const appStore = useAppStore()
const starting = ref(false)
const snack = reactive({ show: false, text: '', color: 'info' })

// Oturum durumu rozeti (HAZIR / ÇALIŞIYOR / TAMAMLANDI)
const statusChip = computed(() => {
  if (appStore.session.running) return { label: 'ÇALIŞIYOR', color: 'warning' }
  if (appStore.session.session_id) return { label: 'TAMAMLANDI', color: 'success' }
  return { label: 'HAZIR', color: 'grey' }
})

// Seçilen cihaz özeti (marka model · firmware)
const deviceLabel = computed(() => {
  const d = appStore.deviceInfo
  const base = [d.brand, d.model].filter(Boolean).join(' ')
  if (!base) return 'Seçilmedi'
  return d.firmware ? `${base} · ${d.firmware}` : base
})

async function onStart() {
  // 1. koşul: önce sağ paneldeki Health-Check başlatılmış olmalı.
  if (!appStore.requireHealthCheck()) {
    snack.text = 'Önce sağ paneldeki Health-Check\'i başlatın; bağlantı kontrolleri çalışmalı.'
    snack.color = 'warning'
    snack.show = true
    return
  }

  starting.value = true
  try {
    const res = await appStore.startTest()
    if (res.skipped && res.skipped.length) {
      snack.text = 'Şu düğümlere ulaşılamadı: ' + res.skipped.join(', ')
      snack.color = 'warning'
    } else {
      snack.text = 'Test başlatıldı: ' + res.session_id
      snack.color = 'success'
    }
    snack.show = true
  } catch (e) {
    snack.text = 'Başlatma hatası: ' + (e.response?.data?.detail || e.message)
    snack.color = 'error'
    snack.show = true
  } finally {
    starting.value = false
  }
}

async function onStop() {
  await appStore.stopTest()
  snack.text = 'Test durduruldu.'
  snack.color = 'info'
  snack.show = true
}
</script>

<style scoped lang="scss">
.device-form {
  background: rgba(20, 20, 28, 0.55) !important;
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.icon-box {
  width: 40px; height: 40px; border-radius: 14px;
  background: rgba(10, 132, 255, 0.2);
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.field-row {
  display: flex; align-items: center; gap: 16px; margin-bottom: 10px;
}
.field-label {
  width: 90px; flex-shrink: 0;
  font-size: 14px; font-weight: 500;
  /* Tema duyarlı: koyu temada açık, açık temada koyu (Vuetify değişkeni) */
  color: rgba(var(--v-theme-on-surface), 0.6);
}
.db-warn-line {
  display: flex; align-items: center;
  font-size: 12px;
  color: rgb(var(--v-theme-warning));
  background: rgba(var(--v-theme-warning), 0.10);
  border: 1px solid rgba(var(--v-theme-warning), 0.25);
  border-radius: 8px;
  padding: 6px 10px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}

/* Oturum & ilerleme özeti */
.summary {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 14px;
  padding: 14px 16px;
}
.summary-head {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 10px;
}
.summary-title {
  font-size: 11px; font-weight: 700; letter-spacing: 0.08em; opacity: 0.6;
}
.summary-row {
  display: flex; align-items: center; justify-content: space-between;
  font-size: 13px; padding: 3px 0;
}
.sr-key { opacity: 0.55; }
.sr-val {
  font-weight: 600; max-width: 60%;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.sr-val.mono { font-family: ui-monospace, "SF Mono", monospace; font-size: 11px; opacity: 0.8; }

.counts {
  display: flex; align-items: center; gap: 12px;
  font-size: 11.5px; opacity: 0.85;
}
.count { display: flex; align-items: center; gap: 5px; }
.count.total { font-weight: 700; opacity: 1; }
.dot {
  width: 8px; height: 8px; border-radius: 50%; display: inline-block;
  &.running { background: #FF9F0A; box-shadow: 0 0 6px rgba(255,159,10,0.6); }
  &.done    { background: #30D158; }
  &.err     { background: #FF453A; }
}

/* Başlat / Durdur butonları arası boşluk (eskiden bitişikti) */
.action-buttons { gap: 18px; }
</style>
