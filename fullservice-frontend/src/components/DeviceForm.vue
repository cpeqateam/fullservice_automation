<template>
  <v-card class="device-form" rounded="xl" elevation="0">

    <!-- Sabit başlık -->
    <div class="df-header px-5 pt-5 pb-0">
      <div class="d-flex align-center mb-3">
        <div class="icon-box mr-3">
          <v-icon icon="mdi-cog" color="white" size="20" />
        </div>
        <h2 class="text-h6 font-weight-bold mb-0">Cihaz ve Test Bilgileri</h2>
      </div>

      <div
        v-if="appStore.brandsDbFailed || appStore.firmwareDbFailed"
        class="db-warn-line mb-3"
      >
        <v-icon size="15" color="warning" class="mr-2">mdi-database-alert</v-icon>
        <span>DB yok — alanlar serbest metne açıldı.</span>
      </div>
    </div>

    <!-- Kaydırılabilir alan -->
    <div class="df-scroll px-5 pb-2">
      <v-form @submit.prevent="onStart">

        <!-- Marka -->
        <div class="field-row">
          <label class="field-label">Marka</label>
          <v-select
            v-if="!appStore.brandsDbFailed"
            v-model="appStore.deviceInfo.brand"
            :items="appStore.brandOptions"
            placeholder="Marka Seçiniz…"
            variant="solo-filled" density="compact" hide-details flat
            menu-icon="mdi-chevron-down"
            @update:model-value="appStore.onBrandChange()"
          />
          <v-combobox
            v-else
            v-model="appStore.deviceInfo.brand"
            :items="appStore.brandOptions"
            placeholder="Marka Yazınız…"
            variant="solo-filled" density="compact" hide-details flat
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
            variant="solo-filled" density="compact" hide-details flat
            menu-icon="mdi-chevron-down"
            @update:model-value="appStore.onModelChange()"
          />
          <v-combobox
            v-else
            v-model="appStore.deviceInfo.model"
            :items="appStore.modelOptions"
            :disabled="!appStore.deviceInfo.brand"
            placeholder="Model Yazınız…"
            variant="solo-filled" density="compact" hide-details flat
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
            variant="solo-filled" density="compact" hide-details flat
            menu-icon="mdi-chevron-down"
          />
          <v-combobox
            v-else
            v-model="appStore.deviceInfo.firmware"
            :items="appStore.firmwareOptions"
            :disabled="!appStore.deviceInfo.model"
            placeholder="Firmware Yazınız…"
            variant="solo-filled" density="compact" hide-details flat
            menu-icon="mdi-chevron-down"
          />
        </div>

        <!-- Süre -->
        <div class="field-row">
          <label class="field-label">Süre (sn)</label>
          <v-text-field
            v-model="appStore.overrides.duration"
            type="number"
            variant="solo-filled" density="compact" hide-details flat
          />
        </div>

        <!-- iperf bölümü -->
        <div class="section-divider mt-4 mb-3">
          <span class="section-label">iperf Parametreleri</span>
        </div>

        <!-- Yön -->
        <div class="field-row">
          <label class="field-label">Yön</label>
          <v-select
            v-model="appStore.iperfParams.direction"
            :items="directionItems"
            item-title="label"
            item-value="value"
            variant="solo-filled" density="compact" hide-details flat
            menu-icon="mdi-chevron-down"
          />
        </div>

        <!-- Pair -->
        <div class="field-row">
          <label class="field-label">Pair</label>
          <v-text-field
            v-model.number="appStore.iperfParams.parallel"
            type="number"
            variant="solo-filled" density="compact" hide-details flat
          />
        </div>

        <!-- Port -->
        <div class="field-row">
          <label class="field-label">Port</label>
          <v-text-field
            v-model.number="appStore.iperfParams.port"
            type="number"
            variant="solo-filled" density="compact" hide-details flat
          />
        </div>

      </v-form>
    </div>

    <!-- Sabit butonlar (her zaman altta) -->
    <div class="df-actions px-5 pb-5">
      <v-divider class="border-opacity-10 mb-4" />
      <v-btn
        color="primary"
        size="default"
        prepend-icon="mdi-play"
        :disabled="appStore.session.running"
        block
        rounded="lg"
        class="mb-3"
        @click="onStart"
      >
        FULL Servis Başlat
      </v-btn>
      <v-btn
        color="error"
        size="default"
        variant="outlined"
        prepend-icon="mdi-stop"
        :disabled="!appStore.session.running"
        block
        rounded="lg"
        @click="stopDialog = true"
      >
        Durdur
      </v-btn>
    </div>

    <!-- Başlatma onayı -->
    <v-dialog v-model="confirmDialog" max-width="420" persistent>
      <v-card rounded="xl" class="confirm-card pa-6" elevation="4">
        <div class="d-flex align-center mb-4">
          <v-icon color="warning" size="26" class="mr-3">mdi-alert-circle-outline</v-icon>
          <h3 class="text-h6 font-weight-bold">Testi Başlatmadan Önce</h3>
        </div>
        <div class="checklist">
          <div class="check-item">
            <v-icon size="18" color="primary" class="mr-2">mdi-checkbox-blank-circle-outline</v-icon>
            STB'nin bağlı ve yayının açık olduğundan emin olun.
          </div>
          <div class="check-item">
            <v-icon size="18" color="primary" class="mr-2">mdi-checkbox-blank-circle-outline</v-icon>
            iPad ve Android tabletlerin bağlı ve açık olduğundan emin olun.
          </div>
          <div class="check-item">
            <v-icon size="18" color="primary" class="mr-2">mdi-checkbox-blank-circle-outline</v-icon>
            Cihazlar şarja takılı durumda mı kontrol ediniz
          </div>
        </div>
        <div class="d-flex dialog-actions mt-5">
          <v-btn variant="outlined" rounded="lg" class="flex-grow-1" @click="confirmDialog = false">Vazgeç</v-btn>
          <v-btn color="primary" rounded="lg" class="flex-grow-1" :loading="starting" @click="confirmAndStart">Başlat</v-btn>
        </div>
      </v-card>
    </v-dialog>

    <!-- Durdurma onayı -->
    <v-dialog v-model="stopDialog" max-width="420" persistent>
      <v-card rounded="xl" class="confirm-card pa-6" elevation="4">
        <div class="d-flex align-center mb-4">
          <v-icon color="error" size="26" class="mr-3">mdi-stop-circle-outline</v-icon>
          <h3 class="text-h6 font-weight-bold">Testi Durdur</h3>
        </div>
        <p class="text-body-2 mb-5" style="opacity:0.8">
          Tüm client'lardaki çalışan görevler durdurulacak (torrent, YouTube dahil). Emin misiniz?
        </p>
        <div class="d-flex dialog-actions">
          <v-btn variant="outlined" rounded="lg" class="flex-grow-1" @click="stopDialog = false">Vazgeç</v-btn>
          <v-btn color="error" rounded="lg" class="flex-grow-1" :loading="stopping" @click="confirmAndStop">Durdur</v-btn>
        </div>
      </v-card>
    </v-dialog>

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
const stopping = ref(false)
const confirmDialog = ref(false)
const stopDialog = ref(false)
const snack = reactive({ show: false, text: '', color: 'info' })

const directionItems = [
  { label: 'Reverse', value: 'reverse' },
  { label: 'Normal', value: 'normal' },
]

function onStart() {
  if (!appStore.requireHealthCheck()) {
    snack.text = 'Önce sağ paneldeki Health-Check\'i başlatın; bağlantı kontrolleri çalışmalı.'
    snack.color = 'warning'
    snack.show = true
    return
  }
  confirmDialog.value = true
}

async function confirmAndStart() {
  confirmDialog.value = false
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

async function confirmAndStop() {
  stopDialog.value = false
  stopping.value = true
  try {
    await appStore.stopTest()
    snack.text = 'Test durduruldu.'
    snack.color = 'info'
    snack.show = true
  } finally {
    stopping.value = false
  }
}
</script>

<style scoped lang="scss">
.device-form {
  background: rgba(20, 20, 28, 0.55) !important;
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* Kaydırılabilir alan: flex-grow ile tüm kalan yüksekliği doldurur */
.df-scroll {
  flex: 1 1 0;
  overflow-y: auto;
  /* ince scroll çubuğu */
  scrollbar-width: thin;
  scrollbar-color: rgba(255,255,255,0.12) transparent;
  &::-webkit-scrollbar { width: 4px; }
  &::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.12); border-radius: 4px; }
}

/* Buton alanı: asla küçülmez, her zaman altta */
.df-actions { flex-shrink: 0; }

.icon-box {
  width: 36px; height: 36px; border-radius: 12px;
  background: rgba(10, 132, 255, 0.2);
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
}
.field-row {
  display: flex; align-items: center; gap: 14px; margin-bottom: 8px;
}
.field-label {
  width: 82px; flex-shrink: 0;
  font-size: 13px; font-weight: 500;
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

.section-divider {
  display: flex; align-items: center; gap: 10px;
  &::before, &::after {
    content: ''; flex: 1; height: 1px;
    background: rgba(255, 255, 255, 0.08);
  }
}
.section-label {
  font-size: 10.5px; font-weight: 700; letter-spacing: 0.08em;
  color: rgba(var(--v-theme-on-surface), 0.45);
  white-space: nowrap;
}

/* Onay popup — tema duyarlı (Vuetify surface rengi) */
.confirm-card {
  border: 1px solid rgba(var(--v-border-color), 0.12);
}
.checklist {
  display: flex; flex-direction: column; gap: 12px;
  padding: 4px 0;
}
.check-item {
  display: flex; align-items: center;
  font-size: 13px; line-height: 1.5;
  color: rgba(var(--v-theme-on-surface), 0.85);
}
.dialog-actions { gap: 12px; }
</style>
