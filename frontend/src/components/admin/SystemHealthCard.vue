<template>
  <v-card :loading="loading" rounded="xl" elevation="1" class="system-health-card pa-4">
    <div class="d-flex align-center mb-3">
      <v-icon :color="statusColor" class="mr-2">{{ statusIcon }}</v-icon>
      <h3 class="text-h6 m-0">系统健康</h3>
      <v-spacer />
      <v-btn
        icon
        size="small"
        variant="text"
        :loading="running"
        @click="runHealthCheck"
        title="立即检查"
      >
        <v-icon>mdi-refresh</v-icon>
      </v-btn>
    </div>
    
    <!-- 整体状态 -->
    <div class="d-flex align-center mb-3">
      <v-chip
        :color="statusColor"
        size="small"
        class="mr-2"
      >
        {{ statusText }}
      </v-chip>
      <span class="text-caption text-medium-emphasis">
        {{ lastCheckText }}
      </span>
    </div>
    
    <!-- 统计数字 -->
    <div class="d-flex justify-space-around text-center mb-3">
      <div>
        <div class="text-h5 text-success">{{ summary?.ok_count || 0 }}</div>
        <div class="text-caption">正常</div>
      </div>
      <div>
        <div class="text-h5 text-warning">{{ summary?.warning_count || 0 }}</div>
        <div class="text-caption">警告</div>
      </div>
      <div>
        <div class="text-h5 text-error">{{ summary?.error_count || 0 }}</div>
        <div class="text-caption">错误</div>
      </div>
    </div>
    
    <!-- 错误列表（简版） -->
    <div v-if="errorChecks.length > 0" class="error-list mb-3">
      <div class="text-caption text-error mb-1">故障项:</div>
      <div
        v-for="check in errorChecks.slice(0, 3)"
        :key="check.key"
        class="text-caption text-medium-emphasis"
      >
        • {{ check.key }}: {{ check.last_error || '未知错误' }}
      </div>
      <div v-if="errorChecks.length > 3" class="text-caption text-medium-emphasis">
        ... 还有 {{ errorChecks.length - 3 }} 项
      </div>
    </div>
    
    <!-- Runner 状态概览 -->
    <div v-if="summary?.runners.length" class="mb-3">
      <div class="text-caption text-medium-emphasis">
        Runner: {{ runnerOkCount }}/{{ summary.runners.length }} 正常
      </div>
    </div>
    
    <div v-if="showActions" class="mt-4">
      <v-btn
        variant="text"
        size="small"
        color="primary"
        @click="$emit('viewDetails')"
      >
        查看详情
      </v-btn>
    </div>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { systemHealthApi } from '@/services/api'
import type { SystemHealthSummary } from '@/types/systemHealth'
import { healthStatusColors, healthStatusIcons, healthStatusTexts } from '@/types/systemHealth'

defineProps<{
  showActions?: boolean
}>()

defineEmits<{
  viewDetails: []
}>()

const loading = ref(false)
const running = ref(false)
const summary = ref<SystemHealthSummary | null>(null)

const statusColor = computed(() => {
  return healthStatusColors[summary.value?.overall_status || 'unknown']
})

const statusIcon = computed(() => {
  return healthStatusIcons[summary.value?.overall_status || 'unknown']
})

const statusText = computed(() => {
  return healthStatusTexts[summary.value?.overall_status || 'unknown']
})

const lastCheckText = computed(() => {
  if (!summary.value?.last_check_time) return '尚未检查'
  const date = new Date(summary.value.last_check_time)
  return `上次检查: ${date.toLocaleString('zh-CN')}`
})

const errorChecks = computed(() => {
  return summary.value?.checks.filter(c => c.status === 'error') || []
})

const runnerOkCount = computed(() => {
  return summary.value?.runners.filter(r => r.last_exit_code === 0).length || 0
})

const loadSummary = async () => {
  try {
    loading.value = true
    summary.value = await systemHealthApi.getSummary()
  } catch (error) {
    console.error('加载健康状态失败:', error)
  } finally {
    loading.value = false
  }
}

const runHealthCheck = async () => {
  try {
    running.value = true
    summary.value = await systemHealthApi.runOnce()
  } catch (error) {
    console.error('运行健康检查失败:', error)
  } finally {
    running.value = false
  }
}

onMounted(() => {
  loadSummary()
})
</script>

<style scoped>
.system-health-card {
  min-height: 200px;
}
.error-list {
  background: rgba(var(--v-theme-error), 0.05);
  padding: 8px;
  border-radius: 4px;
}
</style>
