<template>
  <div class="log-stream">
    <div v-if="entries.length === 0" class="text-center text-medium-emphasis pa-4">
      暂无日志
    </div>
    <div
      v-for="(entry, index) in entries"
      :key="index"
      class="log-entry d-flex align-center py-1"
    >
      <v-chip
        :color="levelColor(entry.level)"
        size="x-small"
        variant="tonal"
        class="mr-2 log-level"
      >
        {{ entry.level.toUpperCase() }}
      </v-chip>
      <span class="text-caption text-medium-emphasis mr-2 log-time">
        {{ formatTime(entry.timestamp) }}
      </span>
      <span class="log-message">{{ entry.message }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { LogEntry } from '@/types/pluginPanels'

const props = defineProps<{
  payload: { entries: LogEntry[] }
  config?: Record<string, any>
}>()

const entries = computed(() => props.payload?.entries || [])

function levelColor(level: string): string {
  const map: Record<string, string> = {
    info: 'info',
    warn: 'warning',
    error: 'error',
    debug: 'grey',
  }
  return map[level] || 'grey'
}

function formatTime(timestamp: string): string {
  try {
    const date = new Date(timestamp)
    return date.toLocaleTimeString()
  } catch {
    return timestamp
  }
}
</script>

<style scoped>
.log-stream {
  font-family: 'Fira Code', 'Consolas', monospace;
  font-size: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.log-entry {
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.log-entry:last-child {
  border-bottom: none;
}

.log-level {
  min-width: 50px;
  justify-content: center;
}

.log-time {
  min-width: 80px;
}

.log-message {
  flex: 1;
  word-break: break-word;
}
</style>
