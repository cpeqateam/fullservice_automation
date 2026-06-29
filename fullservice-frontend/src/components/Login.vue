<template>
  <div class="login-wrap">
    <v-card class="login-card pa-8" rounded="xl" elevation="0" width="400" max-width="92vw">
      <!-- Logo + başlık -->
      <div class="text-center mb-6">
        <img src="https://asset.turktelekom.com.tr/SiteAssets/images/logo.svg" alt="Türk Telekom" class="login-logo mb-4" @error="logoError = true" v-if="!logoError" />
        <v-icon v-else size="56" color="primary" class="mb-4">mdi-shield-account</v-icon>
        <h1 class="login-title">FULL Servis</h1>
        <p class="login-sub">Türk Telekom · CPE QA</p>
      </div>

      <v-form @submit.prevent="submit">
        <v-text-field
          v-model="username"
          label="Kullanıcı adı"
          prepend-inner-icon="mdi-account-outline"
          variant="outlined"
          density="comfortable"
          autofocus
          class="mb-2"
        />
        <v-text-field
          v-model="password"
          label="Şifre"
          :type="showPass ? 'text' : 'password'"
          prepend-inner-icon="mdi-lock-outline"
          :append-inner-icon="showPass ? 'mdi-eye-off' : 'mdi-eye'"
          variant="outlined"
          density="comfortable"
          @click:append-inner="showPass = !showPass"
        />

        <v-alert
          v-if="auth.error"
          type="error"
          variant="tonal"
          density="compact"
          class="mb-3"
          :text="auth.error"
        />

        <v-btn
          type="submit"
          color="primary"
          size="large"
          block
          rounded="lg"
          :loading="auth.loading"
          class="mt-2"
        >
          Giriş Yap
        </v-btn>
      </v-form>
    </v-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '@/store/auth'

const auth = useAuthStore()
const username = ref('')
const password = ref('')
const showPass = ref(false)
const logoError = ref(false)

async function submit() {
  if (!username.value || !password.value) {
    auth.error = 'Kullanıcı adı ve şifre gerekli.'
    return
  }
  await auth.login(username.value.trim(), password.value)
}
</script>

<style scoped>
.login-wrap {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.login-card {
  background: rgba(20, 26, 36, 0.62) !important;
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border: 1px solid rgba(255, 255, 255, 0.08);
}
.v-theme--light .login-card {
  background: rgba(255, 255, 255, 0.85) !important;
  border: 1px solid rgba(0, 0, 0, 0.06);
}
.login-logo { height: 48px; object-fit: contain; }
.login-title {
  font-size: 26px;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.1;
}
.login-sub {
  font-size: 12px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  opacity: 0.6;
  margin-top: 4px;
}
</style>
