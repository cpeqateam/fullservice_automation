<template>
  <v-card class="control-bar pa-4" rounded="xl" elevation="0">
    <div class="cb-row">
      <div class="cb-params">
        <v-text-field
          v-model="appStore.overrides.duration"
          label="Süre (sn)"
          type="number"
          variant="outlined"
          density="compact"
          hide-details
          placeholder="varsayılan"
          class="cb-input"
        />
        <v-text-field
          v-model="appStore.overrides.modem_ip"
          label="Modem IP"
          variant="outlined"
          density="compact"
          hide-details
          placeholder="varsayılan"
          class="cb-input"
        />
        <v-text-field
          v-model="appStore.overrides.internet_ip"
          label="İnternet IP"
          variant="outlined"
          density="compact"
          hide-details
          placeholder="varsayılan"
          class="cb-input"
        />
        <v-text-field
          v-model="appStore.overrides.youtube_link"
          label="YouTube linki"
          variant="outlined"
          density="compact"
          hide-details
          placeholder="varsayılan"
          class="cb-input cb-input--wide"
        />
      </div>

      <div class="cb-actions">
        <v-btn
          color="primary"
          size="large"
          prepend-icon="mdi-play"
          :loading="starting"
          :disabled="appStore.session.running"
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
          @click="onStop"
        >
          Durdur
        </v-btn>
      </div>
    </div>

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
.control-bar {
  background: rgba(20, 20, 28, 0.55) !important;
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.cb-row { display: flex; justify-content: space-between; gap: 24px; flex-wrap: wrap; align-items: flex-end; }
.cb-params { display: flex; gap: 12px; flex-wrap: wrap; flex: 1; min-width: 320px; }
.cb-input { flex: 0 0 150px; }
.cb-input--wide { flex: 0 0 260px; }
.cb-actions { display: flex; gap: 10px; }
</style>
