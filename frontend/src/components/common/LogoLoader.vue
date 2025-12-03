<template>
  <div class="logo-loader">
    <VabHubLogo 
      :size="size" 
      :show-text="showText" 
      :glow="true" 
      variant="dark"
      class="animated-logo"
    />
    <div v-if="showText" class="loading-text">{{ loadingText }}</div>
  </div>
</template>

<script setup lang="ts">
import VabHubLogo from './VabHubLogo.vue'

interface Props {
  size?: number
  showText?: boolean
  loadingText?: string
}

withDefaults(defineProps<Props>(), {
  size: 80,
  showText: true,
  loadingText: '加载中...'
})
</script>

<style lang="scss" scoped>
.logo-loader {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 16px;
  
  .animated-logo {
    animation: pulse 2s ease-in-out infinite;
  }
  
  .loading-text {
    color: rgb(var(--v-theme-on-surface));
    font-size: 0.875rem;
    opacity: 0.7;
    animation: fade 1.5s ease-in-out infinite;
  }
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 1;
  }
  50% {
    transform: scale(1.05);
    opacity: 0.9;
  }
}

@keyframes fade {
  0%, 100% {
    opacity: 0.7;
  }
  50% {
    opacity: 1;
  }
}
</style>

