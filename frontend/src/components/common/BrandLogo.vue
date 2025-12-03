<template>
  <div class="brand-logo-wrapper">
    <VabHubLogo 
      :size="size" 
      :show-text="showText" 
      :glow="glow" 
      :variant="variant"
      class="brand-logo"
    />
  </div>
</template>

<script setup lang="ts">
import VabHubLogo from './VabHubLogo.vue'

interface Props {
  size?: number
  showText?: boolean
  glow?: boolean
  variant?: 'light' | 'dark'
}

withDefaults(defineProps<Props>(), {
  size: 48,
  showText: false,
  glow: true,
  variant: 'dark'
})
</script>

<style lang="scss" scoped>
.brand-logo-wrapper {
  display: inline-block;
  
  .brand-logo {
    transition: transform 0.3s ease;
    
    &:hover {
      transform: scale(1.05);
    }
  }
}
</style>

