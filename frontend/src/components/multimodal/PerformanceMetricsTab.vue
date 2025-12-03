<template>
  <div class="performance-metrics-tab">
    <!-- 性能概览卡片 -->
    <v-row class="mb-4">
      <v-col cols="12" sm="6" md="3" v-for="(op, key) in operations" :key="key">
        <v-card variant="outlined">
          <v-card-title class="text-caption">{{ getOperationName(key) }}</v-card-title>
          <v-card-text>
            <div class="text-h6">{{ op.total_requests || 0 }}</div>
            <div class="text-caption text-medium-emphasis">总请求数</div>
            <v-divider class="my-2" />
            <div class="d-flex justify-space-between">
              <span class="text-caption">缓存命中率</span>
              <span class="text-caption font-weight-bold">{{ formatPercent(op.cache_hit_rate) }}</span>
            </div>
            <div class="d-flex justify-space-between mt-1">
              <span class="text-caption">平均响应时间</span>
              <span class="text-caption font-weight-bold">{{ formatDuration(op.avg_duration) }}</span>
            </div>
            <div class="d-flex justify-space-between mt-1">
              <span class="text-caption">错误率</span>
              <span class="text-caption font-weight-bold" :class="getErrorRateClass(op.error_rate)">
                {{ formatPercent(op.error_rate) }}
              </span>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 缓存统计 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title>缓存统计</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="4">
            <div class="text-center">
              <div class="text-h4">{{ cacheStats?.total_requests || 0 }}</div>
              <div class="text-caption text-medium-emphasis">总请求数</div>
            </div>
          </v-col>
          <v-col cols="12" md="4">
            <div class="text-center">
              <div class="text-h4 text-success">{{ cacheStats?.cache_hits || 0 }}</div>
              <div class="text-caption text-medium-emphasis">缓存命中</div>
            </div>
          </v-col>
          <v-col cols="12" md="4">
            <div class="text-center">
              <div class="text-h4 text-warning">{{ cacheStats?.cache_misses || 0 }}</div>
              <div class="text-caption text-medium-emphasis">缓存未命中</div>
            </div>
          </v-col>
        </v-row>
        <v-divider class="my-4" />
        <div class="text-center">
          <div class="text-h5">总体缓存命中率</div>
          <div class="text-h3" :class="getCacheHitRateClass(cacheStats?.cache_hit_rate)">
            {{ formatPercent(cacheStats?.cache_hit_rate) }}
          </div>
        </div>
      </v-card-text>
    </v-card>

    <!-- 操作详细指标 -->
    <v-card variant="outlined">
      <v-card-title>操作详细指标</v-card-title>
      <v-card-text>
        <v-table>
          <thead>
            <tr>
              <th>操作</th>
              <th>总请求数</th>
              <th>缓存命中率</th>
              <th>平均响应时间</th>
              <th>错误率</th>
              <th>最大并发数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(op, key) in operations" :key="key">
              <td>{{ getOperationName(key) }}</td>
              <td>{{ op.total_requests || 0 }}</td>
              <td>
                <span :class="getCacheHitRateClass(op.cache_hit_rate)">
                  {{ formatPercent(op.cache_hit_rate) }}
                </span>
              </td>
              <td>{{ formatDuration(op.avg_duration) }}</td>
              <td>
                <span :class="getErrorRateClass(op.error_rate)">
                  {{ formatPercent(op.error_rate) }}
                </span>
              </td>
              <td>{{ op.max_concurrent || 0 }}</td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  loading: boolean
  metrics: Record<string, any>
  summary: any
  cacheStats: any
}

const props = defineProps<Props>()

const emit = defineEmits<{
  refresh: []
}>()

const operations = computed(() => {
  return props.metrics || {}
})

const getOperationName = (key: string) => {
  const names: Record<string, string> = {
    video_analysis: '视频分析',
    audio_analysis: '音频分析',
    text_analysis: '文本分析',
    feature_fusion: '特征融合',
    similarity_calculation: '相似度计算'
  }
  return names[key] || key
}

const formatPercent = (value: number) => {
  if (value === undefined || value === null) return '0%'
  return (value * 100).toFixed(2) + '%'
}

const formatDuration = (value: number) => {
  if (value === undefined || value === null) return '0ms'
  if (value < 1) {
    return (value * 1000).toFixed(2) + 'ms'
  }
  return value.toFixed(2) + 's'
}

const getCacheHitRateClass = (rate: number) => {
  if (rate >= 0.8) return 'text-success'
  if (rate >= 0.5) return 'text-warning'
  return 'text-error'
}

const getErrorRateClass = (rate: number) => {
  if (rate === 0) return 'text-success'
  if (rate < 0.1) return 'text-warning'
  return 'text-error'
}
</script>

<style scoped>
.performance-metrics-tab {
  padding: 16px 0;
}
</style>

