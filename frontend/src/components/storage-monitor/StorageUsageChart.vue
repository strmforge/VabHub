<template>
  <div>
    <!-- 图表容器 -->
    <div class="chart-container">
      <div class="chart-header mb-4">
        <div class="d-flex align-center justify-space-between">
          <div>
            <div class="text-h6">存储使用趋势</div>
            <div class="text-caption text-medium-emphasis">
              最近 {{ days }} 天的使用情况
            </div>
          </div>
          <div class="d-flex align-center">
            <v-chip
              color="primary"
              variant="flat"
              size="small"
              class="mr-2"
            >
              <v-icon start size="small">mdi-circle</v-icon>
              已用空间
            </v-chip>
            <v-chip
              color="success"
              variant="flat"
              size="small"
            >
              <v-icon start size="small">mdi-circle</v-icon>
              可用空间
            </v-chip>
          </div>
        </div>
      </div>

      <!-- 简化的趋势展示 -->
      <div class="trends-list">
        <v-card
          v-for="(trend, index) in sortedTrends"
          :key="index"
          variant="outlined"
          class="mb-2"
        >
          <v-card-text>
            <div class="d-flex align-center justify-space-between mb-2">
              <div class="text-body-2 font-weight-medium">
                {{ formatDate(trend.timestamp) }}
              </div>
              <div class="text-body-2">
                使用率: {{ trend.usage_percent.toFixed(1) }}%
              </div>
            </div>

            <v-progress-linear
              :model-value="trend.usage_percent"
              :color="getUsageColor(trend.usage_percent)"
              height="20"
              rounded
              class="mb-2"
            >
              <template v-slot:default>
                <strong class="text-white">{{ trend.usage_percent.toFixed(1) }}%</strong>
              </template>
            </v-progress-linear>

            <v-row dense>
              <v-col cols="4">
                <div class="text-caption text-medium-emphasis">总空间</div>
                <div class="text-body-2 font-weight-bold">{{ formatBytes(trend.total_bytes) }}</div>
              </v-col>
              <v-col cols="4">
                <div class="text-caption text-medium-emphasis">已用</div>
                <div class="text-body-2 font-weight-bold text-primary">{{ formatBytes(trend.used_bytes) }}</div>
              </v-col>
              <v-col cols="4">
                <div class="text-caption text-medium-emphasis">可用</div>
                <div class="text-body-2 font-weight-bold text-success">{{ formatBytes(trend.free_bytes) }}</div>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </div>

      <!-- 空状态 -->
      <v-alert
        v-if="sortedTrends.length === 0"
        type="info"
        variant="tonal"
        class="mt-4"
      >
        暂无趋势数据
      </v-alert>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  trends: any[]
  days: number
}>()

// 排序后的趋势数据（按时间倒序）
const sortedTrends = computed(() => {
  return [...props.trends].sort((a, b) => {
    return new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  })
})

// 格式化字节数
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 根据使用率获取颜色
const getUsageColor = (percent: number): string => {
  if (percent >= 90) return 'error'
  if (percent >= 80) return 'warning'
  if (percent >= 50) return 'info'
  return 'success'
}

// 格式化日期
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.chart-container {
  min-height: 400px;
}

.trends-list {
  max-height: 600px;
  overflow-y: auto;
}
</style>

