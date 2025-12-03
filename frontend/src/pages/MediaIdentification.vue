<template>
  <div class="media-identification-page">
    <PageHeader
      title="媒体识别"
      subtitle="智能识别媒体文件信息"
    >
      <template v-slot:actions>
        <v-btn
          color="primary"
          prepend-icon="mdi-file-upload"
          @click="showUploadDialog = true"
        >
          上传文件
        </v-btn>
        <v-btn
          color="primary"
          prepend-icon="mdi-folder-multiple"
          @click="showBatchDialog = true"
        >
          批量识别
        </v-btn>
      </template>
    </PageHeader>

    <!-- 文件选择区域 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-text>
        <v-file-input
          v-model="selectedFiles"
          label="选择媒体文件"
          prepend-icon="mdi-file"
          variant="outlined"
          multiple
          accept="video/*,audio/*"
          @change="handleFilesSelected"
        />
      </v-card-text>
    </v-card>

    <!-- 识别结果 -->
    <div v-if="loading" class="text-center py-12">
      <v-progress-circular indeterminate color="primary" size="64" />
      <div class="mt-4 text-body-1 text-medium-emphasis">识别中...</div>
    </div>

    <div v-else-if="results.length === 0" class="text-center py-12">
      <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-file-question</v-icon>
      <div class="text-h6 text-medium-emphasis mb-2">暂无识别结果</div>
      <div class="text-body-2 text-medium-emphasis">
        请选择媒体文件进行识别
      </div>
    </div>

    <v-row v-else>
      <v-col
        v-for="(result, index) in results"
        :key="index"
        cols="12"
        md="6"
      >
        <v-card variant="outlined">
          <v-card-title class="d-flex align-center justify-space-between">
            <span class="text-body-1">{{ result.file_path }}</span>
            <v-chip
              :color="result.success ? 'success' : 'error'"
              size="small"
              variant="flat"
            >
              {{ result.success ? '识别成功' : '识别失败' }}
            </v-chip>
          </v-card-title>

          <v-card-text v-if="result.success">
            <v-row>
              <v-col cols="12" sm="6">
                <div class="mb-2">
                  <strong>标题：</strong> {{ result.title || '未知' }}
                </div>
                <div class="mb-2" v-if="result.year">
                  <strong>年份：</strong> {{ result.year }}
                </div>
                <div class="mb-2" v-if="result.season !== undefined">
                  <strong>季数：</strong> {{ result.season }}
                </div>
                <div class="mb-2" v-if="result.episode !== undefined">
                  <strong>集数：</strong> {{ result.episode }}
                </div>
                <div class="mb-2">
                  <strong>类型：</strong> {{ result.type || '未知' }}
                </div>
                <div class="mb-2">
                  <strong>置信度：</strong> {{ (result.confidence * 100).toFixed(1) }}%
                </div>
                <div class="mb-2" v-if="result.source">
                  <strong>识别来源：</strong> {{ result.source }}
                </div>
                <div class="mb-2" v-if="result.file_size">
                  <strong>文件大小：</strong> {{ formatFileSize(result.file_size) }}
                </div>
              </v-col>
              <v-col cols="12" sm="6">
                <v-progress-linear
                  :model-value="result.confidence * 100"
                  :color="getConfidenceColor(result.confidence)"
                  height="8"
                  rounded
                  class="mb-2"
                />
                <v-chip
                  :color="getConfidenceColor(result.confidence)"
                  size="small"
                  variant="flat"
                >
                  {{ getConfidenceLabel(result.confidence) }}
                </v-chip>
              </v-col>
            </v-row>
          </v-card-text>

          <v-card-text v-else>
            <v-alert type="error" variant="tonal">
              {{ result.error || '识别失败' }}
            </v-alert>
          </v-card-text>

          <v-card-actions>
            <v-spacer />
            <v-btn
              size="small"
              variant="text"
              @click="handleRetry(result.file_path)"
            >
              重新识别
            </v-btn>
            <v-btn
              v-if="result.success"
              size="small"
              color="primary"
              @click="handleAddSubscription(result)"
            >
              添加到订阅
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-col>
    </v-row>

    <!-- 上传对话框 -->
    <v-dialog v-model="showUploadDialog" max-width="500">
      <v-card>
        <v-card-title>上传文件识别</v-card-title>
        <v-card-text>
          <v-file-input
            v-model="uploadFiles"
            label="选择文件"
            multiple
            accept="video/*,audio/*"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showUploadDialog = false">取消</v-btn>
          <v-btn color="primary" @click="handleUpload">识别</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- 批量识别对话框 -->
    <v-dialog v-model="showBatchDialog" max-width="600">
      <v-card>
        <v-card-title>批量识别</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="batchPath"
            label="文件夹路径"
            prepend-icon="mdi-folder"
            variant="outlined"
            hint="输入包含媒体文件的文件夹路径"
            persistent-hint
          />
          <v-checkbox
            v-model="recursive"
            label="递归扫描子文件夹"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showBatchDialog = false">取消</v-btn>
          <v-btn color="primary" @click="handleBatchIdentify">开始识别</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'

const loading = ref(false)
const showUploadDialog = ref(false)
const showBatchDialog = ref(false)
const selectedFiles = ref<File[]>([])
const uploadFiles = ref<File[]>([])
const batchPath = ref('')
const recursive = ref(true)
const results = ref<any[]>([])

const handleFilesSelected = async (files: File[] | null) => {
  if (!files || files.length === 0) return

  loading.value = true
  try {
    // 如果只有一个文件，使用单文件上传API
    if (files.length === 1) {
      const file = files[0]
      const formData = new FormData()
      formData.append('file', file)
      
      const response = await api.post('/media-identification/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 300000 // 5分钟超时，用于大文件上传
      })
      
      results.value = [response.data]
    } else {
      // 多个文件使用批量上传API
      const formData = new FormData()
      Array.from(files).forEach(file => {
        formData.append('files', file)
      })
      
      const response = await api.post('/media-identification/upload/batch', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        timeout: 600000 // 10分钟超时，用于批量上传
      })
      
      results.value = response.data.results || []
    }
  } catch (error: any) {
    console.error('识别失败:', error)
    alert('识别失败: ' + (error.response?.data?.detail || error.message))
    results.value = []
  } finally {
    loading.value = false
  }
}

const handleUpload = async () => {
  if (!uploadFiles.value || uploadFiles.value.length === 0) return

  showUploadDialog.value = false
  loading.value = true
  
  try {
    // 使用批量上传API
    const formData = new FormData()
    Array.from(uploadFiles.value).forEach(file => {
      formData.append('files', file)
    })
    
    const response = await api.post('/media-identification/upload/batch', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      },
      timeout: 600000 // 10分钟超时，用于批量上传
    })
    
    results.value = response.data.results || []
    uploadFiles.value = []
  } catch (error: any) {
    console.error('上传失败:', error)
    alert('上传失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const handleBatchIdentify = async () => {
  if (!batchPath.value) return

  loading.value = true
  showBatchDialog.value = false
  try {
    // TODO: 实现批量识别（需要后端支持文件夹扫描）
    console.log('批量识别:', batchPath.value, recursive.value)
    // 这里需要后端API支持
  } catch (error: any) {
    console.error('批量识别失败:', error)
  } finally {
    loading.value = false
  }
}

const handleRetry = async (filePath: string) => {
  try {
    const response = await api.post('/media-identification/identify', {
      file_path: filePath
    })
    
    // 更新结果
    const index = results.value.findIndex(r => r.file_path === filePath)
    if (index >= 0) {
      results.value[index] = response.data
    }
  } catch (error: any) {
    console.error('重新识别失败:', error)
  }
}

const handleAddSubscription = (result: any) => {
  // TODO: 打开订阅创建对话框
  console.log('添加到订阅:', result)
}

const getConfidenceColor = (confidence: number) => {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.6) return 'primary'
  if (confidence >= 0.4) return 'warning'
  return 'error'
}

const getConfidenceLabel = (confidence: number) => {
  if (confidence >= 0.8) return '高置信度'
  if (confidence >= 0.6) return '中置信度'
  if (confidence >= 0.4) return '低置信度'
  return '不可靠'
}

const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}
</script>

<style scoped>
.media-identification-page {
  padding: 24px;
}
</style>

