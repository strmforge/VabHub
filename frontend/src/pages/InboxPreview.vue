<template>
  <div class="inbox-preview-page">
    <v-container>
      <!-- 标题区 -->
      <v-card class="mb-6">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="warning">mdi-inbox</v-icon>
          <span>统一收件箱预览（Dev）</span>
          <v-chip size="small" color="warning" class="ml-2">开发工具</v-chip>
        </v-card-title>
        <v-card-subtitle>
          预览统一待整理目录中的文件及其自动分类结果。此功能仅用于开发/调试。
        </v-card-subtitle>
      </v-card>

      <!-- 操作按钮 -->
      <v-card class="mb-6">
        <v-card-text>
          <div class="d-flex gap-2">
            <v-btn
              color="primary"
              prepend-icon="mdi-refresh"
              @click="loadPreview"
              :loading="loading"
            >
              刷新预览
            </v-btn>
            <v-btn
              color="success"
              prepend-icon="mdi-play"
              @click="runOnce"
              :loading="processing"
              :disabled="loading"
            >
              运行一次处理
            </v-btn>
          </div>
        </v-card-text>
      </v-card>

      <!-- 错误提示 -->
      <v-alert v-if="errorMessage" type="error" class="mb-4">
        {{ errorMessage }}
      </v-alert>

      <!-- 成功提示 -->
      <v-alert v-if="successMessage" type="success" class="mb-4">
        {{ successMessage }}
      </v-alert>

      <!-- 数据表格 -->
      <v-card>
        <v-card-title>
          收件箱项目 ({{ items.length }})
        </v-card-title>
        <v-divider />
        <v-card-text>
          <v-data-table
            :headers="headers"
            :items="items"
            :items-per-page="20"
            class="elevation-0"
            no-data-text="暂无待处理项目"
            :loading="loading || processing"
          >
            <template v-slot:item.path="{ item }">
              <span class="text-caption" :title="item.path">
                {{ truncatePath(item.path) }}
              </span>
            </template>
            <template v-slot:item.media_type="{ item }">
              <v-chip
                :color="getMediaTypeColor(item.media_type)"
                size="small"
                variant="flat"
              >
                {{ item.media_type }}
              </v-chip>
            </template>
            <template v-slot:item.score="{ item }">
              <v-progress-linear
                :model-value="item.score * 100"
                :color="getScoreColor(item.score)"
                height="20"
                rounded
              >
                <template v-slot:default>
                  <span class="text-caption">{{ (item.score * 100).toFixed(0) }}%</span>
                </template>
              </v-progress-linear>
            </template>
            <template v-slot:item.size_bytes="{ item }">
              {{ formatFileSize(item.size_bytes) }}
            </template>
            <template v-slot:item.modified_at="{ item }">
              {{ formatDate(item.modified_at) }}
            </template>
            <template v-slot:item.result="{ item }">
              <v-chip
                v-if="item.result"
                :color="getResultColor(item.result)"
                size="small"
                variant="flat"
              >
                {{ item.result }}
              </v-chip>
              <span v-else class="text-medium-emphasis">-</span>
            </template>
          </v-data-table>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { inboxApi } from '@/services/api'

// 状态
const loading = ref(false)
const processing = ref(false)
const errorMessage = ref<string | null>(null)
const successMessage = ref<string | null>(null)
const items = ref<Array<{
  path: string
  media_type: string
  score: number
  reason: string
  size_bytes: number
  modified_at: string
  result?: string
}>>([])

// 表格列定义
const headers = [
  { title: '文件路径', key: 'path', sortable: true },
  { title: '媒体类型', key: 'media_type', sortable: true },
  { title: '置信度', key: 'score', sortable: true },
  { title: '判断原因', key: 'reason', sortable: false },
  { title: '文件大小', key: 'size_bytes', sortable: true },
  { title: '修改时间', key: 'modified_at', sortable: true },
  { title: '处理结果', key: 'result', sortable: false }
]

// 加载预览
const loadPreview = async () => {
  loading.value = true
  errorMessage.value = null
  successMessage.value = null

  try {
    const response = await inboxApi.preview()
    
    // 处理响应（根据实际响应格式调整）
    if (response.data) {
      if (response.data.items) {
        items.value = response.data.items
      } else if (Array.isArray(response.data)) {
        items.value = response.data
      }
    }
    
    successMessage.value = `扫描完成，发现 ${items.value.length} 个项目`
  } catch (err: any) {
    console.error('加载预览失败:', err)
    errorMessage.value = err.response?.data?.error_message || 
                        err.response?.data?.message || 
                        err.message || 
                        '加载预览失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 运行一次处理
const runOnce = async () => {
  processing.value = true
  errorMessage.value = null
  successMessage.value = null

  try {
    const response = await inboxApi.runOnce()
    
    // 处理响应
    if (response.data) {
      if (response.data.items) {
        items.value = response.data.items
      } else if (Array.isArray(response.data)) {
        items.value = response.data
      }
    }
    
    // 统计处理结果
    const handled = items.value.filter(item => item.result?.startsWith('handled:')).length
    const skipped = items.value.filter(item => item.result?.startsWith('skipped:')).length
    const failed = items.value.filter(item => item.result?.startsWith('failed:')).length
    
    successMessage.value = `处理完成：成功 ${handled}，跳过 ${skipped}，失败 ${failed}`
  } catch (err: any) {
    console.error('执行处理失败:', err)
    errorMessage.value = err.response?.data?.error_message || 
                        err.response?.data?.message || 
                        err.message || 
                        '执行处理失败，请稍后重试'
  } finally {
    processing.value = false
  }
}

// 工具函数
const truncatePath = (path: string, maxLength: number = 50) => {
  if (path.length <= maxLength) return path
  return '...' + path.slice(-maxLength)
}

const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return `${(bytes / Math.pow(k, i)).toFixed(2)} ${sizes[i]}`
}

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

const getMediaTypeColor = (mediaType: string): string => {
  const colors: Record<string, string> = {
    movie: 'red',
    tv: 'blue',
    anime: 'purple',
    ebook: 'green',
    audiobook: 'orange',
    novel_txt: 'teal',
    comic: 'pink',
    music: 'indigo',
    unknown: 'grey'
  }
  return colors[mediaType] || 'grey'
}

const getScoreColor = (score: number): string => {
  if (score >= 0.8) return 'success'
  if (score >= 0.5) return 'warning'
  return 'error'
}

const getResultColor = (result: string): string => {
  if (result.startsWith('handled:')) return 'success'
  if (result.startsWith('skipped:')) return 'info'
  if (result.startsWith('failed:')) return 'error'
  return 'grey'
}

// 页面加载时自动刷新
onMounted(() => {
  loadPreview()
})
</script>

<style scoped>
.inbox-preview-page {
  padding: 16px;
}
</style>

