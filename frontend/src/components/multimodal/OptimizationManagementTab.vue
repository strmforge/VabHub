<template>
  <div class="optimization-management-tab">
    <!-- 优化操作 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title>优化操作</v-card-title>
      <v-card-text>
        <v-row>
          <v-col cols="12" md="4">
            <v-btn
              color="primary"
              block
              prepend-icon="mdi-auto-fix"
              @click="handleOptimize('all')"
              :loading="optimizing"
            >
              优化所有操作
            </v-btn>
          </v-col>
          <v-col cols="12" md="4">
            <v-btn
              color="secondary"
              block
              prepend-icon="mdi-cached"
              @click="handleOptimize('cache-ttl')"
              :loading="optimizing"
            >
              优化缓存TTL
            </v-btn>
          </v-col>
          <v-col cols="12" md="4">
            <v-btn
              color="secondary"
              block
              prepend-icon="mdi-sync"
              @click="handleOptimize('concurrency')"
              :loading="optimizing"
            >
              优化并发数
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 当前配置 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-title>当前配置</v-card-title>
      <v-card-text>
        <v-row v-if="config">
          <v-col cols="12" md="6">
            <h3 class="mb-2">缓存TTL</h3>
            <v-table density="compact">
              <tbody>
                <tr v-for="(ttl, op) in config.cache_ttl" :key="op">
                  <td>{{ getOperationName(op) }}</td>
                  <td>{{ formatTTL(ttl) }}</td>
                </tr>
              </tbody>
            </v-table>
          </v-col>
          <v-col cols="12" md="6">
            <h3 class="mb-2">并发数</h3>
            <v-table density="compact">
              <tbody>
                <tr v-for="(conc, op) in config.concurrency" :key="op">
                  <td>{{ getOperationName(op) }}</td>
                  <td>{{ conc }}</td>
                </tr>
              </tbody>
            </v-table>
          </v-col>
        </v-row>
        <div v-else class="text-center py-4 text-medium-emphasis">
          暂无配置信息
        </div>
      </v-card-text>
    </v-card>

    <!-- 优化历史 -->
    <v-card variant="outlined">
      <v-card-title>优化历史</v-card-title>
      <v-card-text>
        <div v-if="loading" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64" />
          <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
        </div>
        <div v-else-if="history.length === 0" class="text-center py-12">
          <v-icon size="64" color="grey-lighten-1">mdi-history</v-icon>
          <div class="mt-4 text-body-1 text-medium-emphasis">暂无优化历史</div>
        </div>
        <v-table v-else>
          <thead>
            <tr>
              <th>时间</th>
              <th>操作</th>
              <th>优化类型</th>
              <th>旧值</th>
              <th>新值</th>
              <th>改进</th>
              <th>原因</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in history" :key="item.id">
              <td>{{ formatTime(item.timestamp) }}</td>
              <td>{{ getOperationName(item.operation) }}</td>
              <td>{{ getOptimizationTypeName(item.optimization_type) }}</td>
              <td>{{ formatValue(item.optimization_type, item.old_value) }}</td>
              <td>{{ formatValue(item.optimization_type, item.new_value) }}</td>
              <td>
                <span :class="getImprovementClass(item.improvement)">
                  {{ formatImprovement(item.improvement) }}
                </span>
              </td>
              <td class="text-caption">{{ item.reason || '-' }}</td>
            </tr>
          </tbody>
        </v-table>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  loading: boolean
  config: any
  history: any[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'refresh'): void
  (e: 'optimize', type: 'all' | 'cache-ttl' | 'concurrency', operation?: string): void
  (e: 'updateConfig', config: any): void
}>()

const optimizing = ref(false)

const handleOptimize = (type: 'all' | 'cache-ttl' | 'concurrency') => {
  emit('optimize', type)
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

const getOptimizationTypeName = (type: string) => {
  const names: Record<string, string> = {
    cache_ttl: '缓存TTL',
    concurrency: '并发数'
  }
  return names[type] || type
}

const formatTTL = (seconds: number) => {
  if (seconds < 60) return `${seconds}秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
  return `${Math.floor(seconds / 3600)}小时`
}

const formatValue = (type: string, value: number) => {
  if (type === 'cache_ttl') {
    return formatTTL(value)
  }
  return value?.toString() || '-'
}

const formatImprovement = (improvement: number) => {
  if (improvement === null || improvement === undefined) return '-'
  const sign = improvement > 0 ? '+' : ''
  return `${sign}${improvement.toFixed(2)}%`
}

const getImprovementClass = (improvement: number) => {
  if (improvement > 0) return 'text-success'
  if (improvement < 0) return 'text-error'
  return ''
}

const formatTime = (timestamp: string) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleString('zh-CN')
}
</script>

<style scoped>
.optimization-management-tab {
  padding: 16px 0;
}
</style>
