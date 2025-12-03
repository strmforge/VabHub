<template>
  <div class="empty-state text-center py-12">
    <v-icon :size="iconSize" :color="iconColor" class="mb-4">
      {{ icon }}
    </v-icon>
    <div class="text-h6 mb-2">{{ title }}</div>
    <div v-if="description" class="text-body-2 text-medium-emphasis mb-4" style="max-width: 400px; margin: 0 auto;">
      {{ description }}
    </div>
    <v-btn
      v-if="actionText"
      :color="actionColor"
      variant="flat"
      @click="$emit('action')"
    >
      {{ actionText }}
    </v-btn>
    <slot />
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  icon?: string
  iconSize?: number | string
  iconColor?: string
  title: string
  description?: string
  actionText?: string
  actionColor?: string
}>(), {
  icon: 'mdi-folder-open-outline',
  iconSize: 64,
  iconColor: 'grey-lighten-1',
  actionColor: 'primary'
})

defineEmits<{
  action: []
}>()
</script>

<style scoped>
.empty-state {
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>
