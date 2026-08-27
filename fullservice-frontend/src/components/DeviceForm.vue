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

        <!-- Arayüzden Al — firmware alanının altında, aynı X ekseninde ve genişlikte -->
        <div class="field-row mt-2">
          <div class="field-label"></div>
          <v-btn
            class="flex-grow-1"
            variant="outlined"
            rounded="lg"
            size="small"
            :loading="fetchingFirmware"
            :disabled="!appStore.deviceInfo.brand || !appStore.deviceInfo.model || fetchingFirmware"
            prepend-icon="mdi-download-network-outline"
            @click="fetchFirmwareFromInterface"
          >
            Arayüzden Al
          </v-btn>
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

        <!-- Koşulacak Testler — varsayılan hepsi seçili, tik kaldırılan test hiç başlamaz -->
        <div class="field-row">
          <label class="field-label">Testler</label>
          <v-menu
            v-model="testMenu"
            :close-on-content-click="false"
            location="bottom end"
            offset="6"
          >
            <template #activator="{ props }">
              <v-btn
                v-bind="props"
                variant="tonal"
                density="comfortable"
                block
                rounded="lg"
                class="tests-btn"
                :append-icon="testMenu ? 'mdi-chevron-up' : 'mdi-chevron-down'"
              >
                <v-icon icon="mdi-format-list-checks" size="18" class="mr-2" />
                {{ testsBtnLabel }}
              </v-btn>
            </template>

            <div class="tests-panel">
              <div class="tp-head">
                <span class="tp-title">Koşulacak Testler</span>
                <div class="tp-bulk">
                  <button type="button" class="tp-link" :disabled="lockedSelection" @click="selectAll">Tümü</button>
                  <span class="tp-sep">·</span>
                  <button type="button" class="tp-link" :disabled="lockedSelection" @click="selectNone">Hiçbiri</button>
                </div>
              </div>

              <div v-if="lockedSelection" class="tp-locked">
                <v-icon icon="mdi-lock-outline" size="14" class="mr-1" />
                Test sürerken seçim değiştirilemez.
              </div>

              <div class="tp-list">
                <label
                  v-for="t in appStore.availableTests"
                  :key="t"
                  class="tp-item"
                  :class="{ off: appStore.deselectedTests.includes(t), locked: lockedSelection }"
                >
                  <input
                    type="checkbox"
                    class="tp-box"
                    :checked="!appStore.deselectedTests.includes(t)"
                    :disabled="lockedSelection"
                    @change="toggleTest(t)"
                  />
                  <span class="tp-name">{{ appStore.testLabels[t] || t }}</span>
                  <span class="tp-nodes">{{ appStore.nodesForTest(t).length }} düğüm</span>
                </label>
              </div>

              <div v-if="!appStore.availableTests.length" class="tp-empty">
                Düğümler yüklenince testler burada listelenir.
              </div>
            </div>
          </v-menu>
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
        :disabled="appStore.session.running || !appStore.selectedTests.length"
        block
        rounded="lg"
        class="mb-3"
        @click="onStart"
      >
        FULL Servis Başlat
      </v-btn>
      <p v-if="!appStore.selectedTests.length" class="no-test-warn">
        En az bir test seçilmeli.
      </p>
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

    <!-- Firmware çekiliyor — kullanıcı X ile kapatamasın diye persistent -->
    <v-dialog v-model="fetchingFirmware" max-width="360" persistent>
      <v-card rounded="xl" class="confirm-card pa-6 text-center" elevation="4">
        <v-progress-circular indeterminate color="primary" size="44" width="4" class="mb-4" />
        <h3 class="text-subtitle-1 font-weight-bold mb-2">Bilgiler cihazdan çekiliyor</h3>
        <p class="text-body-2 mb-0" style="opacity:0.75">
          Modem arayüzüne bağlanılıyor, lütfen bekleyin…
        </p>
      </v-card>
    </v-dialog>

    <!-- Firmware çekme hatası — başlık/ikon hata tipine göre değişir -->
    <v-dialog v-model="firmwareErrorDialog" max-width="480" persistent>
      <v-card rounded="xl" class="confirm-card pa-6" elevation="4">
        <div class="d-flex align-center mb-4">
          <v-icon :color="firmwareErrorColor" size="26" class="mr-3">{{ firmwareErrorIcon }}</v-icon>
          <h3 class="text-h6 font-weight-bold">{{ firmwareErrorTitle }}</h3>
        </div>
        <p class="text-body-2 mb-5" style="opacity:0.8">{{ firmwareErrorMessage }}</p>
        <div class="d-flex dialog-actions">
          <v-btn
            :color="firmwareErrorColor"
            rounded="lg"
            class="flex-grow-1"
            @click="firmwareErrorDialog = false"
          >Tamam</v-btn>
        </div>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snack.show" :color="snack.color" :timeout="5000" location="top">
      {{ snack.text }}
    </v-snackbar>
  </v-card>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useAppStore } from '@/store/app'
import { fetchModemFirmware } from '@/services/api'

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

// ── Test seçimi ───────────────────────────────────────────────────────────
// Varsayılan HEPSİ seçilidir; store yalnızca kullanıcının KAPATTIKLARINI tutar.
// Test sürerken seçim kilitlenir: listeyi oturum başlarken agent'lara gönderiyoruz,
// koşum ortasında tik açmak o testi başlatmaz — arayüz bunu vaat etmemeli.
const testMenu = ref(false)
const lockedSelection = computed(() => appStore.session.running)

const testsBtnLabel = computed(() => {
  const all = appStore.availableTests.length
  const sel = appStore.selectedTests.length
  if (!all) return 'Testler yükleniyor…'
  if (sel === all) return `Tüm testler (${all})`
  if (sel === 0) return 'Hiçbir test seçili değil'
  return `${sel} / ${all} test seçili`
})

function toggleTest(t) {
  if (lockedSelection.value) return
  const list = appStore.deselectedTests
  const i = list.indexOf(t)
  if (i >= 0) list.splice(i, 1)
  else list.push(t)
}

function selectAll() {
  if (lockedSelection.value) return
  appStore.deselectedTests.splice(0)
}

function selectNone() {
  if (lockedSelection.value) return
  appStore.deselectedTests.splice(0, appStore.deselectedTests.length, ...appStore.availableTests)
}

// ── Arayüzden firmware çekme ──────────────────────────────────────────────
const fetchingFirmware     = ref(false)   // loading dialog kontrolü + buton spinner
const firmwareErrorDialog  = ref(false)   // hata popup'ı
const firmwareErrorTitle   = ref('')
const firmwareErrorMessage = ref('')
const firmwareErrorIcon    = ref('mdi-alert-circle-outline')
const firmwareErrorColor   = ref('warning')

function _setFwError(title, message, icon = 'mdi-alert-circle-outline', color = 'warning') {
  firmwareErrorTitle.value   = title
  firmwareErrorMessage.value = message
  firmwareErrorIcon.value    = icon
  firmwareErrorColor.value   = color
  firmwareErrorDialog.value  = true
}

async function fetchFirmwareFromInterface() {
  if (!appStore.deviceInfo.brand || !appStore.deviceInfo.model) {
    _setFwError('Eksik Bilgi', 'Önce marka ve model seçmelisiniz.')
    return
  }

  fetchingFirmware.value = true
  try {
    const res = await fetchModemFirmware({
      brand: appStore.deviceInfo.brand,
      model: appStore.deviceInfo.model,
      modem_ip: appStore.overrides.modem_ip || undefined,
    })

    const finalFw = res.data.final_firmware
    if (!finalFw) {
      _setFwError(
        'Tarih Çıkarılamadı',
        'Cihaz arayüzünden firmware okundu ancak tarih bilgisi ayıklanamadı. Listeden seçim yapın.',
        'mdi-calendar-remove-outline',
        'warning',
      )
      return
    }

    // DB'ye yeni eklendiyse listeyi tazele ki yeni değer combobox'ta gözüksün
    if (res.data.was_added) {
      try {
        await appStore.loadFirmwares()
      } catch (err) {
        console.warn('Firmware listesi yenilenemedi:', err)
      }
    }

    // Combobox'a değeri ata (mevcut eşleşme veya yeni eklenmiş)
    appStore.deviceInfo.firmware = finalFw
  } catch (e) {
    const status = e?.response?.status
    const detail = e?.response?.data?.detail

    // Backend zaten her hata için sade Türkçe mesaj döner; başlık + ikonu tipine göre seç
    if (status === 404) {
      _setFwError('Cihaz Entegre Değil', detail || 'Cihazın entegrasyonu sistemde yok.', 'mdi-package-variant-closed-remove', 'warning')
    } else if (status === 502) {
      _setFwError('Modeme Bağlanılamadı', detail || 'Modem arayüzü açılamadı.', 'mdi-router-network', 'error')
    } else if (status === 503) {
      _setFwError('Tarayıcı Hatası', detail || 'Tarayıcı başlatılamadı.', 'mdi-web-off', 'error')
    } else {
      _setFwError('Hata', detail || 'Beklenmedik bir hata oluştu.', 'mdi-alert-circle', 'error')
    }
  } finally {
    fetchingFirmware.value = false
  }
}

function onStart() {
  if (!appStore.requireHealthCheck()) {
    snack.text = 'Önce sağ paneldeki Health-Check\'i başlatın; bağlantı kontrolleri çalışmalı.'
    snack.color = 'warning'
    snack.show = true
    return
  }
  // Uptime kontrolü: bir cihaz limitten uzun süredir açıksa (kırmızı) test başlatılamaz.
  const blocked = appStore.uptimeBlockedNodes
  if (blocked.length) {
    const fmt = (m) => (m < 60 ? `${m} dakika` : `${Math.floor(m / 60)} sa ${m % 60} dk`)
    const list = blocked.map((b) => `${b.label} (${fmt(b.minutes)}dır açık)`).join('; ')
    snack.text = `Test başlatılamaz. ${list} — bu cihaz(lar)ı kapatıp yeniden açın. `
      + 'Sağ panelde hepsi yeşil olunca başlatabilirsiniz.'
    snack.color = 'error'
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

/* ── Test seçim paneli ──────────────────────────────────────────────────────
   Renkler Vuetify tema değişkenlerinden türetilir (--v-theme-*), böylece açık
   ve karanlık temada ayrı kural yazmadan doğru görünür. */
.tests-btn {
  justify-content: flex-start;
  font-weight: 600;
  letter-spacing: 0;
  text-transform: none;
}

.tests-panel {
  width: 290px;
  padding: 10px 0 6px;
  border-radius: 12px;
  background: rgb(var(--v-theme-surface));
  border: 1px solid rgba(var(--v-theme-on-surface), 0.12);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.22);
}

.tp-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 14px 8px;
  border-bottom: 1px solid rgba(var(--v-theme-on-surface), 0.08);
}
.tp-title {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: rgba(var(--v-theme-on-surface), 0.75);
}
.tp-bulk { display: flex; align-items: center; gap: 6px; }
.tp-link {
  background: none;
  border: 0;
  padding: 0;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
}
.tp-link:disabled { opacity: 0.4; cursor: not-allowed; }
.tp-sep { color: rgba(var(--v-theme-on-surface), 0.3); font-size: 11px; }

.tp-locked {
  display: flex;
  align-items: center;
  margin: 8px 10px 2px;
  padding: 5px 8px;
  border-radius: 7px;
  font-size: 11px;
  color: rgb(var(--v-theme-warning));
  background: rgba(var(--v-theme-warning), 0.10);
  border: 1px solid rgba(var(--v-theme-warning), 0.25);
}

.tp-list { display: flex; flex-direction: column; padding: 6px 6px 0; }

.tp-item {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 7px 9px;
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.12s ease;
}
.tp-item:hover { background: rgba(var(--v-theme-on-surface), 0.06); }
.tp-item.locked { cursor: not-allowed; opacity: 0.55; }
.tp-item.off .tp-name { opacity: 0.45; text-decoration: line-through; }

.tp-box {
  width: 15px;
  height: 15px;
  flex: none;
  accent-color: rgb(var(--v-theme-primary));
  cursor: inherit;
}

.tp-name {
  flex: 1;
  font-size: 13px;
  font-weight: 600;
  color: rgba(var(--v-theme-on-surface), 0.9);
}
.tp-nodes {
  font-size: 10.5px;
  color: rgba(var(--v-theme-on-surface), 0.45);
  font-variant-numeric: tabular-nums;
}

.tp-empty {
  padding: 12px 14px;
  font-size: 12px;
  color: rgba(var(--v-theme-on-surface), 0.5);
}

.no-test-warn {
  margin: -6px 0 10px;
  text-align: center;
  font-size: 11.5px;
  color: rgb(var(--v-theme-warning));
}
</style>
