<template>
  <v-alert
    :type="alertType"
    variant="tonal"
    prominent
    class="mb-0"
  >
    <template #prepend>
      <v-icon :icon="statusIcon" size="32" />
    </template>
    <div class="d-flex flex-column">
      <div class="text-subtitle-1 font-weight-medium">{{ message }}</div>
      <div v-if="details" class="text-caption text-medium-emphasis mt-1">
        <span v-for="(value, key) in details" :key="key" class="mr-3">
          {{ key }}: {{ value }}
        </span>
      </div>
    </div>
  </v-alert>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { StatusCardPayload } from '@/types/pluginPanels'

const props = defineProps<{
  payload: StatusCardPayload
  config?: Record<string, any>
}>()

const status = computed(() => props.payload?.status || 'unknown')
const message = computed(() => props.payload?.message || '状态未知')
const details = computed(() => props.payload?.details)

const alertType = computed(() => {
  const map: Record<string, 'success' | 'warning' | 'error' | 'info'> = {
    ok: 'success',
    warning: 'warning',
    error: 'error',
    unknown: 'info',
  }
  return map[status.value] || 'info'
})

const statusIcon = computed(() => {
  if (props.payload?.icon) return props.payload.icon
  
  const map: Record<string, string> = {
    ok: 'mdi-check-circle',
    warning: 'mdi-alert',
    error: 'mdi-alert-circle',
    unknown: 'mdi-help-circle',
  }
  return map[status.value] || 'mdi-information'
})
</script>
