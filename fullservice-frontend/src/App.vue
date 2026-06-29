<template>
  <v-app :theme="appStore.isDarkMode ? 'dark' : 'light'" class="app-root">
    <LiquidBackground />

    <!-- Giriş yapılmadıysa sadece login ekranı -->
    <Login v-if="!auth.isAuthenticated" />

    <!-- Giriş yapıldıysa tüm uygulama (üst bar + çekmece + içerik) -->
    <template v-else>
    <Topbar />

    <!-- Sol gezinme çekmecesi (hamburger ile açılır) -->
    <v-navigation-drawer v-model="appStore.drawerOpen" temporary width="270" class="nav-drawer">
      <div class="nav-head d-flex align-center px-4 py-4">
        <v-icon color="primary" size="22" class="mr-2">mdi-view-grid-outline</v-icon>
        <span class="nav-title">MENÜ</span>
      </div>
      <v-divider class="border-opacity-15" />
      <v-list nav density="comfortable" class="pa-2">
        <v-list-item
          :active="appStore.currentView === 'dashboard'"
          prepend-icon="mdi-view-dashboard-outline"
          title="Panel"
          rounded="lg"
          @click="appStore.setView('dashboard')"
        />
        <v-list-item
          :active="appStore.currentView === 'settings'"
          prepend-icon="mdi-cog-outline"
          title="Ayarlar"
          rounded="lg"
          @click="appStore.setView('settings')"
        />
        <v-list-item
          :active="appStore.currentView === 'profile'"
          prepend-icon="mdi-account-circle-outline"
          title="Profil"
          rounded="lg"
          @click="appStore.setView('profile')"
        />
      </v-list>

      <!-- Alt: giriş yapan kullanıcı + çıkış -->
      <template #append>
        <v-divider class="border-opacity-15" />
        <div class="pa-3">
          <div class="d-flex align-center px-2 mb-2">
            <v-icon size="20" class="mr-2">mdi-account-circle</v-icon>
            <span class="text-body-2 font-weight-medium">{{ auth.displayName }}</span>
          </div>
          <v-btn
            block
            variant="tonal"
            color="error"
            prepend-icon="mdi-logout"
            rounded="lg"
            @click="onLogout"
          >
            Çıkış Yap
          </v-btn>
        </div>
      </template>
    </v-navigation-drawer>

    <v-main>
      <v-container fluid class="py-6">
        <!-- ── KARŞILAMA (landing) ── -->
        <v-row v-if="appStore.currentView === 'landing'">
          <v-col cols="12" md="9" lg="9">
            <Welcome @enter="goPanel" />
          </v-col>
          <v-col cols="12" md="3" lg="3">
            <StatusPanel />
          </v-col>
        </v-row>

        <!-- ── PANEL (dashboard) ── -->
        <v-row v-else-if="appStore.currentView === 'dashboard'">
          <!-- Sol: cihaz/test formu — tam yükseklik -->
          <v-col cols="12" md="4" lg="3">
            <DeviceForm class="fill-col" />
          </v-col>

          <!-- Orta: 2×2 düğüm kartları -->
          <v-col cols="12" md="5" lg="6">
            <div v-if="!appStore.nodes.length" class="empty">
              <v-progress-circular indeterminate color="primary" size="48" />
              <p class="mt-4 text-body-2 text-medium-emphasis">Sunucuya bağlanılıyor…</p>
            </div>
            <div v-else class="node-grid-2x2">
              <NodeCard v-for="n in appStore.nodes" :key="n.node_id" :node="n" :labels="appStore.testLabels" />
            </div>
          </v-col>

          <!-- Sağ panel: health-check + bağlantı ışıkları -->
          <v-col cols="12" md="3" lg="3">
            <StatusPanel />
          </v-col>
        </v-row>

        <!-- ── AYARLAR / PROFİL (şimdilik boş yer tutucu) ── -->
        <v-row v-else justify="center">
          <v-col cols="12" md="8" lg="6">
            <v-card class="placeholder-card pa-10 text-center" rounded="xl" elevation="0">
              <v-icon :icon="viewMeta.icon" size="56" color="primary" class="mb-4" />
              <h2 class="text-h5 font-weight-bold mb-2">{{ viewMeta.title }}</h2>
              <p class="text-body-2 text-medium-emphasis">
                Bu bölüm yakında eklenecek.
              </p>
            </v-card>
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
    </template>
  </v-app>
</template>

<script setup>
import { onMounted, onBeforeUnmount, computed, watch } from 'vue'
import { useAppStore } from '@/store/app'
import { useAuthStore } from '@/store/auth'
import LiquidBackground from '@/components/LiquidBackground.vue'
import Login from '@/components/Login.vue'
import Welcome from '@/components/Welcome.vue'
import Topbar from '@/components/Topbar.vue'
import DeviceForm from '@/components/DeviceForm.vue'
import StatusPanel from '@/components/StatusPanel.vue'
import NodeCard from '@/components/NodeCard.vue'

const appStore = useAppStore()
const auth = useAuthStore()

function startApp() {
  appStore.startPolling(1000)
  appStore.loadBrands()
}
function stopApp() {
  appStore.stopPolling()
  appStore.stopHealthCheck()
}
// Karşılama ekranındaki "Sisteme Giriş" butonu → panel sayfası
function goPanel() {
  appStore.setView('dashboard')
}
function onLogout() {
  stopApp()
  appStore.setView('landing')   // sonraki girişte yine karşılama ekranı
  appStore.drawerOpen = false
  auth.logout()
}

// Giriş yapıldıysa veri akışını başlat, çıkışta durdur (canlı izleme/sağ panel için)
watch(() => auth.isAuthenticated, (v) => (v ? startApp() : stopApp()))

// Ayarlar/Profil placeholder başlık + ikonu
const viewMeta = computed(() => {
  if (appStore.currentView === 'settings') return { title: 'Ayarlar', icon: 'mdi-cog-outline' }
  if (appStore.currentView === 'profile') return { title: 'Profil', icon: 'mdi-account-circle-outline' }
  return { title: '', icon: '' }
})

onMounted(() => {
  if (auth.isAuthenticated) startApp()   // sayfa yenilendiyse oturum localStorage'dan gelir
})
onBeforeUnmount(() => stopApp())
</script>

<style>
.app-root .v-application__wrap { background: transparent !important; }
.empty { display: flex; flex-direction: column; align-items: center; padding: 80px 0; }

/* Orta sütun: 4 düğüm kartı 2×2 (2 üst, 2 alt) */
.node-grid-2x2 {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}
/* md+ ekranlarda: ekran yüksekliğine sığsın, taşarsa kendi içinde kayar
   (monitörde uzun, laptopta kısa → vh ile otomatik uyum) */
@media (min-width: 960px) {
  .node-grid-2x2 {
    max-height: calc(100vh - 176px);
    overflow-y: auto;
    align-content: start;
    padding-right: 4px;
  }
}
@media (max-width: 600px) {
  .node-grid-2x2 { grid-template-columns: 1fr; }
}

/* Sol form kartı kolonu doldursun (md+ ekranda ekrana sığsın) */
.fill-col.device-form {
  display: flex;
  flex-direction: column;
}
@media (min-width: 960px) {
  .fill-col.device-form { height: calc(100vh - 176px); }
}

/* Sol gezinme çekmecesi — tema duyarlı (açık temada beyaz, koyuda koyu) */
.v-theme--dark .nav-drawer {
  background: rgba(18, 24, 34, 0.92) !important;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
}
.v-theme--light .nav-drawer {
  background: rgba(255, 255, 255, 0.94) !important;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
}
.nav-head .nav-title {
  font-size: 12px; font-weight: 700; letter-spacing: 0.1em; opacity: 0.85;
}

/* Ayarlar / Profil boş yer tutucu kartı */
.placeholder-card {
  background: rgba(20, 26, 36, 0.55) !important;
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border: 1px solid rgba(255, 255, 255, 0.06);
  margin-top: 40px;
}

.foot {
  background: rgba(0,0,0,0.3) !important;
  backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255,255,255,0.06);
}
</style>
