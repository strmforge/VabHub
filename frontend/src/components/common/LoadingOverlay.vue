<template>
  <v-overlay
    :model-value="modelValue"
    class="loading-overlay"
    persistent
  >
    <LogoLoader :size="80" :show-text="true" :loading-text="message" />
  </v-overlay>
</template>

<script setup lang="ts">
import LogoLoader from './LogoLoader.vue'

interface Props {
  modelValue: boolean
  message?: string
}

withDefaults(defineProps<Props>(), {
  message: '加载中...'
})
</script>

<style lang="scss" scoped>
.loading-overlay {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>

