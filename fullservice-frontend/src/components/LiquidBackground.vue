<template>
  <div class="liquid-background" :class="{ 'light-mode': !appStore.isDarkMode }">
    <div class="blob blob-1"></div>
    <div class="blob blob-2"></div>
    <div class="blob blob-3"></div>
    <div class="blob blob-4"></div>
    <div class="overlay"></div>
  </div>
</template>

<script setup>
import { useAppStore } from '@/store/app'
const appStore = useAppStore()
</script>

<style scoped lang="scss">
// Sayfanın arkasında animasyonlu, bulanık renk lekeleri. Türk Telekom mavisi
// hakim; karanlık modda derin koyu, açık modda yumuşak gri-mavi zemin.
.liquid-background {
  position: fixed;
  top: 0; left: 0;
  width: 100vw; height: 100vh;
  overflow: hidden;
  z-index: -1;
  background: #060A12;
  transition: background 0.5s ease;
  pointer-events: none;

  &.light-mode {
    background: #F4F7FB;
    .blob { opacity: 0.45; }
    .overlay { background: transparent; backdrop-filter: none; -webkit-backdrop-filter: none; }
  }
}

.blob {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.55;
  animation: float 22s infinite ease-in-out alternate;
  transition: opacity 0.5s ease;
}
.blob-1 { top: -10%; left: -10%; width: 52vw; height: 52vw;
  background: linear-gradient(135deg, #0A84FF, #5AC8FA); animation-duration: 26s; }
.blob-2 { bottom: -12%; right: -10%; width: 60vw; height: 60vw;
  background: linear-gradient(135deg, #0050C8, #0A84FF); animation-duration: 31s; animation-delay: -6s; }
.blob-3 { top: 38%; left: 42%; width: 42vw; height: 42vw;
  background: linear-gradient(135deg, #0A84FF, #00C2DE); animation-duration: 24s; animation-delay: -10s; }
.blob-4 { top: 28%; left: 8%;  width: 36vw; height: 36vw;
  background: linear-gradient(45deg,  #0050C8, #5AC8FA); opacity: 0.35; animation-duration: 36s; animation-delay: -16s; }

.overlay {
  position: absolute; inset: 0;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(70px);
  -webkit-backdrop-filter: blur(70px);
}

@keyframes float {
  0%   { transform: translate(0, 0) rotate(0deg); }
  25%  { transform: translate(30px, -30px) scale(1.05); }
  50%  { transform: translate(-20px, 20px) scale(0.95); }
  100% { transform: translate(50px, 50px) rotate(20deg); }
}
</style>
