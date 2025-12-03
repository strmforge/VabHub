<template>
  <div class="system-resource-monitor">
    <!-- CPU使用率 -->
    <div class="mb-4">
      <div class="d-flex justify-space-between mb-2">
        <span class="text-caption">CPU</span>
        <span class="text-caption font-weight-bold">{{ cpuUsage }}%</span>
      </div>
      <v-progress-linear
        :model-value="cpuUsage"
        color="primary"
        height="8"
        rounded
      />
    </div>
    
    <!-- 内存使用率 -->
    <div class="mb-4">
      <div class="d-flex justify-space-between mb-2">
        <span class="text-caption">内存</span>
        <span class="text-caption font-weight-bold">{{ memoryUsage }}%</span>
      </div>
      <v-progress-linear
        :model-value="memoryUsage"
        color="success"
        height="8"
        rounded
      />
      <div class="text-caption text-medium-emphasis mt-1">
        {{ formatSize(memoryUsed) }} / {{ formatSize(memoryTotal) }}
      </div>
    </div>
    
    <!-- 磁盘使用率 -->
    <div>
      <div class="d-flex justify-space-between mb-2">
        <span class="text-caption">磁盘</span>
        <span class="text-caption font-weight-bold">{{ diskUsage }}%</span>
      </div>
      <v-progress-linear
        :model-value="diskUsage"
        color="warning"
        height="8"
        rounded
      />
      <div class="text-caption text-medium-emphasis mt-1">
        {{ formatSize(diskUsed) }} / {{ formatSize(diskTotal) }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  stats: {
    cpu_usage?: number
    memory_usage?: number
    memory_used_gb?: number
    memory_total_gb?: number
    disk_usage?: number
    disk_used_gb?: number
    disk_total_gb?: number
    // 兼容旧格式
    cpu?: number
    memory?: number
    disk?: number
  }
}

const props = defineProps<Props>()

const cpuUsage = computed(() => props.stats.cpu_usage ?? props.stats.cpu ?? 0)
const memoryUsage = computed(() => props.stats.memory_usage ?? props.stats.memory ?? 0)
const memoryUsed = computed(() => (props.stats.memory_used_gb ?? 0) * 1024 * 1024 * 1024)
const memoryTotal = computed(() => (props.stats.memory_total_gb ?? 0) * 1024 * 1024 * 1024)
const diskUsage = computed(() => props.stats.disk_usage ?? props.stats.disk ?? 0)
const diskUsed = computed(() => (props.stats.disk_used_gb ?? 0) * 1024 * 1024 * 1024)
const diskTotal = computed(() => (props.stats.disk_total_gb ?? 0) * 1024 * 1024 * 1024)

const formatSize = (bytes: number) => {
  if (!bytes || bytes === 0) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(2)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`
}
</script>

