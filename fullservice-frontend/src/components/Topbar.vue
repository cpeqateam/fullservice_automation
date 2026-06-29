<template>
  <v-app-bar app flat class="topbar" height="88">
    <v-btn
      icon="mdi-menu"
      variant="text"
      size="large"
      class="ml-2 menu-btn"
      @click="appStore.toggleDrawer()"
    />
    <div
      class="brand pl-2 pr-2 d-flex align-center brand-clickable"
      role="button"
      title="Karşılama ekranına dön"
      @click="appStore.setView('landing')"
    >
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

    <!-- Sağ üstte giriş yapan kullanıcı (GRK gibi) -->
    <v-chip
      v-if="auth.user"
      class="user-chip mr-3"
      color="primary"
      prepend-icon="mdi-account-circle"
      variant="elevated"
      density="comfortable"
    >
      {{ auth.displayName }}
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
// Üst bar: logo/başlık + giriş yapan kullanıcı + tema toggle.
import { useAppStore } from '@/store/app'
import { useAuthStore } from '@/store/auth'
const appStore = useAppStore()
const auth = useAuthStore()
</script>

<style scoped lang="scss">
.topbar {
  background: rgba(0, 0, 0, 0.35) !important;
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.brand-clickable { cursor: pointer; border-radius: 12px; transition: opacity 0.15s; }
.brand-clickable:hover { opacity: 0.85; }
.brand-logo { height: 58px; transition: height 0.2s; }
.brand-text { line-height: 1.15; }
.brand-title {
  font-family: "Inter", "Segoe UI", system-ui, sans-serif;
  font-weight: 800;
  font-size: 26px;
  letter-spacing: 0.5px;
  background: linear-gradient(90deg, #0A84FF, #5AC8FA);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.brand-sub {
  font-family: "Inter", "Segoe UI", system-ui, sans-serif;
  font-size: 13px;
  font-weight: 500;
  opacity: 0.6;
  letter-spacing: 0.3px;
}
.menu-btn { opacity: 0.85; }
.user-chip { font-weight: 600; letter-spacing: 0.3px; }
</style>
