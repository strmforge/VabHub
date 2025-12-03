<template>
  <div class="page-header mb-6">
    <div class="d-flex justify-space-between align-center">
      <div>
        <h1 class="text-h4 font-weight-bold mb-1">{{ title }}</h1>
        <p v-if="subtitle" class="text-subtitle-1 text-medium-emphasis mb-0">
          {{ subtitle }}
        </p>
      </div>
      <div v-if="$slots.actions" class="d-flex align-center">
        <slot name="actions" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  title: string
  subtitle?: string
}

defineProps<Props>()
</script>

<style lang="scss" scoped>
.page-header {
  padding: 16px 0;
}
</style>

