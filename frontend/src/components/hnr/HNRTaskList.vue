<template>
  <v-list>
    <v-list-item
      v-for="task in sortedTasks"
      :key="task.id"
      class="hnr-task-item"
    >
      <template v-slot:prepend>
        <v-avatar :color="getRiskColor(task.risk_score)" size="40">
          <v-icon color="white">mdi-shield-alert</v-icon>
        </v-avatar>
      </template>
      
      <v-list-item-title class="font-weight-medium">
        {{ task.title }}
      </v-list-item-title>
      <v-list-item-subtitle>
        <div class="d-flex align-center flex-wrap ga-3 mt-2">
          <v-chip
            :color="getRiskColor(task.risk_score)"
            size="x-small"
            variant="flat"
          >
            {{ getRiskLevel(task.risk_score) }} ({{ (task.risk_score * 100).toFixed(1) }}%)
          </v-chip>
          <span class="text-caption">
            <v-icon size="small" class="me-1">mdi-timer</v-icon>
            做种: {{ formatTime(task.seed_time_hours) }} / {{ formatTime(task.required_seed_time_hours) }}
          </span>
          <span class="text-caption">
            <v-icon size="small" class="me-1">mdi-swap-vertical</v-icon>
            分享率: {{ formatRatio(task.current_ratio) }} / {{ formatRatio(task.required_ratio) }}
          </span>
          <span v-if="task.site_name" class="text-caption text-medium-emphasis">
            {{ task.site_name }}
          </span>
        </div>
      </v-list-item-subtitle>
      
      <template v-slot:append>
        <v-btn
          icon="mdi-information"
          size="small"
          variant="text"
          @click="handleAction(task)"
        />
      </template>
    </v-list-item>
  </v-list>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import api from '@/services/api'

interface Props {
  tasks: any[]
}

const props = defineProps<Props>()
const emit = defineEmits(['refresh'])

const getRiskColor = (score: number) => {
  if (score < 0.3) return 'success'
  if (score < 0.7) return 'warning'
  return 'error'
}

const getRiskLevel = (score: number) => {
  if (score < 0.3) return '低风险'
  if (score < 0.7) return '中风险'
  return '高风险'
}

const formatTime = (hours: number) => {
  if (hours < 1) return `${Math.round(hours * 60)}分钟`
  if (hours < 24) return `${hours.toFixed(1)}小时`
  return `${Math.floor(hours / 24)}天${Math.round(hours % 24)}小时`
}

const formatRatio = (ratio: number) => {
  return ratio.toFixed(2)
}

const handleAction = async (task: any) => {
  // TODO: 实现管理操作（查看详情、调整做种等）
  console.log('Manage task:', task)
}

const sortedTasks = computed(() => {
  return [...props.tasks].sort((a, b) => b.risk_score - a.risk_score)
})
</script>

<style lang="scss" scoped>
.hnr-task-item {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
}
</style>

