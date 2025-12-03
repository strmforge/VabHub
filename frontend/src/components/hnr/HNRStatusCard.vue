<template>
  <div class="hnr-status-card">
    <!-- 风险概览 -->
    <div class="mb-4">
      <div class="d-flex justify-space-between align-center mb-2">
        <span class="text-caption">当前风险评分</span>
        <v-chip
          :color="getRiskColor(overallRisk)"
          size="small"
          variant="flat"
        >
          {{ getRiskLevel(overallRisk) }} ({{ displayRisk }}%)
        </v-chip>
      </div>
      <v-progress-linear
        :model-value="overallRisk"
        :color="getRiskColor(overallRisk)"
        height="8"
        rounded
      />
    </div>
    
    <!-- 风险任务列表 -->
    <div v-if="riskTasks.length > 0" class="mt-4">
      <div class="text-caption text-medium-emphasis mb-2">高风险任务 ({{ riskTasks.length }})</div>
      <v-list density="compact">
        <v-list-item
          v-for="task in riskTasks.slice(0, 5)"
          :key="task.id"
          :title="task.title"
          :subtitle="`风险评分: ${(task.risk_score * 100).toFixed(1)}% | 分享率: ${task.current_ratio.toFixed(2)} | 做种时间: ${task.seed_time_hours.toFixed(1)}h`"
        >
          <template v-slot:prepend>
            <v-icon :color="getRiskColor(task.risk_score * 100)">
              mdi-alert
            </v-icon>
          </template>
        </v-list-item>
      </v-list>
      <div v-if="riskTasks.length > 5" class="text-caption text-center text-medium-emphasis mt-2">
        还有 {{ riskTasks.length - 5 }} 个高风险任务...
      </div>
    </div>
    
    <div v-else class="text-center text-medium-emphasis py-4">
      <v-icon size="48" color="success" class="mb-2">mdi-shield-check</v-icon>
      <div>当前无高风险任务</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  riskTasks: any[]
  overallRisk: number
}

const props = defineProps<Props>()

const getRiskColor = (score: number) => {
  if (score < 30) return 'success'
  if (score < 70) return 'warning'
  return 'error'
}

const getRiskLevel = (score: number) => {
  if (score < 30) return '低风险'
  if (score < 70) return '中风险'
  return '高风险'
}

const displayRisk = computed(() => {
  return Math.round(props.overallRisk)
})
</script>

