<template>
  <v-card class="device-form pa-6" rounded="xl" elevation="0">
    <div class="d-flex align-center mb-5">
      <div class="icon-box mr-3">
        <v-icon icon="mdi-cog" color="white" size="20" />
      </div>
      <h2 class="text-h6 font-weight-bold mb-0">Cihaz ve Test Bilgileri</h2>
    </div>

    <!-- DB bağlantı hatası uyarısı -->
    <v-alert
      v-if="appStore.brandsDbFailed || appStore.firmwareDbFailed"
      type="warning"
      variant="tonal"
      density="compact"
      icon="mdi-database-alert"
      class="mb-4"
    >
      DB bağlantısı kurulamadı. Marka/Model/Firmware alanları geçici olarak serbest metin girişine açıldı.
    </v-alert>

    <v-form @submit.prevent="onStart">
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

      <!-- Gelişmiş parametreler (opsiyonel) -->
      <v-expansion-panels variant="accordion" class="adv-panel mt-2">
        <v-expansion-panel>
          <v-expansion-panel-title class="text-caption">Gelişmiş parametreler (opsiyonel)</v-expansion-panel-title>
          <v-expansion-panel-text>
            <v-text-field v-model="appStore.overrides.modem_ip" label="Modem IP" placeholder="varsayılan" variant="outlined" density="compact" hide-details class="mb-3" />
            <v-text-field v-model="appStore.overrides.internet_ip" label="İnternet IP" placeholder="varsayılan" variant="outlined" density="compact" hide-details class="mb-3" />
            <v-text-field v-model="appStore.overrides.youtube_link" label="YouTube linki" placeholder="varsayılan" variant="outlined" density="compact" hide-details />
          </v-expansion-panel-text>
        </v-expansion-panel>
      </v-expansion-panels>

      <div class="d-flex gap-3 mt-6">
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
import { ref, reactive } from 'vue'
import { useAppStore } from '@/store/app'

const appStore = useAppStore()
const starting = ref(false)
const snack = reactive({ show: false, text: '', color: 'info' })

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
  display: flex; align-items: center; gap: 16px; margin-bottom: 14px;
}
.field-label {
  width: 90px; flex-shrink: 0;
  font-size: 14px; font-weight: 500;
  color: rgba(255, 255, 255, 0.6);
}
.adv-panel :deep(.v-expansion-panel) {
  background: rgba(255, 255, 255, 0.03) !important;
  border-radius: 12px;
}
</style>
