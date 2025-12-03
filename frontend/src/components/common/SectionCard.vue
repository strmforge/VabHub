<template>
  <v-card :rounded="rounded" class="section-card mb-4">
    <v-card-title v-if="title || $slots.title" class="d-flex align-center">
      <v-icon v-if="icon" class="mr-2" :color="iconColor">{{ icon }}</v-icon>
      <slot name="title">{{ title }}</slot>
      <v-spacer />
      <slot name="actions" />
    </v-card-title>
    <v-card-subtitle v-if="subtitle || $slots.subtitle">
      <slot name="subtitle">{{ subtitle }}</slot>
    </v-card-subtitle>
    <v-card-text :class="noPadding ? 'pa-0' : ''">
      <slot />
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  title?: string
  subtitle?: string
  icon?: string
  iconColor?: string
  rounded?: string
  noPadding?: boolean
}>(), {
  rounded: 'lg',
  iconColor: 'primary',
  noPadding: false
})
</script>

<style scoped>
.section-card {
  overflow: hidden;
}
</style>
