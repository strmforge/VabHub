<template>
  <div class="history-data-tab">
    <!-- 操作栏 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="6">
            <v-btn
              color="warning"
              prepend-icon="mdi-delete-sweep"
              @click="showCleanupDialog = true"
            >
              清理历史数据
            </v-btn>
          </v-col>
          <v-col cols="12" md="6" class="text-right">
            <v-text-field
              v-model="daysToKeep"
              label="保留天数"
              type="number"
              density="compact"
              variant="outlined"
              style="max-width: 200px; display: inline-block;"
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 历史统计 -->
    <v-card variant="outlined">
      <v-card-title>历史统计</v-card-title>
      <v-card-text>
        <div v-if="loading" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64" />
          <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
        </div>
        <div v-else-if="!statistics || Object.keys(statistics).length === 0" class="text-center py-12">
          <v-icon size="64" color="grey-lighten-1">mdi-chart-line</v-icon>
          <div class="mt-4 text-body-1 text-medium-emphasis">暂无历史数据</div>
        </div>
        <v-table v-else>
          <thead>
            <tr>
              <th>操作</th>
              <th>总请求数</th>
              <th>缓存命中数</th>
              <th>缓存未命中数</th>
              <th>缓存命中率</th>
              <th>平均响应时间</th>
              <th>最小响应时间</th>
              <th>最大响应时间</th>
              <th>错误数</th>
              <th>错误率</th>
              <th>最大并发数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(stats, op) in statistics" :key="op">
              <td>{{ getOperationName(op) }}</td>
              <td>{{ stats.total_requests || 0 }}</td>
              <td class="text-success">{{ stats.cache_hits || 0 }}</td>
              <td class="text-warning">{{ stats.cache_misses || 0 }}</td>
              <td>
                <span :class="getCacheHitRateClass(stats.cache_hit_rate)">
                  {{ formatPercent(stats.cache_hit_rate) }}
                </span>
              </td>
              <td>{{ formatDuration(stats.avg_duration) }}</td>
              <td>{{ formatDuration(stats.min_duration) }}</td>
              <td>{{ formatDuration(stats.max_duration) }}</td>
              <td>
                <span :class="getErrorRateClass(stats.error_rate)">
                  {{ stats.error_count || 0 }}
                </span>
              </td>
              <td>
                <span :class="getErrorRateClass(stats.error_rate)">
                  {{ formatPercent(stats.error_rate) }}
                </span>
              </td>
              <td>{{ stats.max_concurrent || 0 }}</td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>
    </v-card>

    <!-- 清理对话框 -->
    <v-dialog v-model="showCleanupDialog" max-width="500">
      <v-card>
        <v-card-title>清理历史数据</v-card-title>
        <v-card-text>
          <p>确定要清理{{ daysToKeep }}天前的历史数据吗？</p>
          <p class="text-caption text-medium-emphasis">此操作不可恢复</p>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showCleanupDialog = false">取消</v-btn>
          <v-btn color="error" variant="text" @click="handleCleanup">确定</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  loading: boolean
  statistics: Record<string, any>
}

const props = defineProps<Props>()

const emit = defineEmits<{
  refresh: []
  cleanup: [days: number]
}>()

const showCleanupDialog = ref(false)
const daysToKeep = ref(30)

const handleCleanup = () => {
  emit('cleanup', daysToKeep.value)
  showCleanupDialog.value = false
}

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
.history-data-tab {
  padding: 16px 0;
}
</style>

