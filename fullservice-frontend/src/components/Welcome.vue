<template>
  <div class="landing">
    <img
      src="https://asset.turktelekom.com.tr/SiteAssets/images/logo.svg"
      alt="Türk Telekom"
      class="landing-logo mb-6"
    />
    <h1 class="landing-brand">TÜRK TELEKOM</h1>
    <h2 class="landing-title">FULL SERVİS<br />MODEM STRES TEST OTOMASYONU</h2>
    <p class="landing-desc">
      Hoş Geldiniz{{ auth.displayName ? ' ' + auth.displayName : '' }}
    </p>

    <v-btn
      color="primary"
      size="x-large"
      rounded="pill"
      prepend-icon="mdi-rocket-launch"
      class="landing-btn mt-8"
      @click="$emit('enter')"
    >
      Sisteme Giriş
    </v-btn>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/store/auth'
defineEmits(['enter'])
const auth = useAuthStore()
</script>

<style scoped>
.landing {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  min-height: calc(100vh - 176px);
  padding: 24px;
}
.landing-logo { height: 96px; object-fit: contain; }
.landing-brand {
  font-size: clamp(40px, 6vw, 72px);
  font-weight: 800;
  letter-spacing: 0.02em;
  line-height: 1;
  color: rgba(var(--v-theme-on-surface), 0.92);
}
.landing-title {
  font-size: clamp(20px, 2.6vw, 34px);
  font-weight: 800;
  line-height: 1.15;
  margin-top: 6px;
  background: linear-gradient(90deg, #0A84FF, #5AC8FA);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
}
.landing-desc {
  max-width: 560px;
  margin-top: 18px;
  font-size: 15px;
  line-height: 1.6;
  opacity: 0.7;
}
.landing-btn { font-weight: 700; letter-spacing: 0.4px; padding-inline: 32px; }
</style>
