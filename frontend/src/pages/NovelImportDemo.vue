<template>
  <div class="novel-import-demo-page">
    <v-container>
      <!-- 标题区 -->
      <v-card class="mb-6">
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2" color="warning">mdi-code-tags</v-icon>
          <span>小说 TXT 导入（Dev）</span>
          <v-chip size="small" color="warning" class="ml-2">开发工具</v-chip>
        </v-card-title>
        <v-card-subtitle>
          此功能仅用于开发/演示，支持上传本地 TXT 文件并导入为电子书。
        </v-card-subtitle>
      </v-card>

      <!-- 表单区域 -->
      <v-card>
        <v-card-title>上传 TXT 小说</v-card-title>
        <v-divider />
        <v-card-text>
          <v-form ref="formRef" @submit.prevent="handleSubmit">
            <!-- 文件选择 -->
            <v-file-input
              v-model="file"
              label="选择 TXT 文件"
              accept=".txt"
              prepend-icon="mdi-file-document"
              show-size
              :rules="fileRules"
              :disabled="loading"
              class="mb-4"
            />

            <!-- 标题 -->
            <v-text-field
              v-model="title"
              label="书名（可选）"
              hint="如果不填写，将使用文件名作为书名"
              prepend-inner-icon="mdi-book-open-variant"
              variant="outlined"
              :disabled="loading"
              class="mb-4"
            />

            <!-- 作者 -->
            <v-text-field
              v-model="author"
              label="作者（可选）"
              prepend-inner-icon="mdi-account"
              variant="outlined"
              :disabled="loading"
              class="mb-4"
            />

            <!-- 简介 -->
            <v-textarea
              v-model="description"
              label="简介（可选）"
              prepend-inner-icon="mdi-text"
              variant="outlined"
              rows="3"
              :disabled="loading"
              class="mb-4"
            />

            <!-- 操作按钮 -->
            <div class="d-flex gap-2">
              <v-btn
                type="submit"
                color="primary"
                :loading="loading"
                :disabled="!file"
                prepend-icon="mdi-upload"
              >
                导入
              </v-btn>
              <v-btn
                variant="outlined"
                @click="handleReset"
                :disabled="loading"
              >
                重置
              </v-btn>
            </div>
          </v-form>
        </v-card-text>
      </v-card>

      <!-- 结果展示区域 -->
      <v-card v-if="result || errorMessage" class="mt-6">
        <v-card-title>
          <v-icon class="mr-2" :color="result ? 'success' : 'error'">
            {{ result ? 'mdi-check-circle' : 'mdi-alert-circle' }}
          </v-icon>
          {{ result ? '导入成功' : '导入失败' }}
        </v-card-title>
        <v-divider />
        <v-card-text>
          <!-- 成功结果 -->
          <div v-if="result">
            <v-alert type="success" class="mb-4">
              {{ result.message }}
            </v-alert>

            <v-list>
              <v-list-item>
                <v-list-item-title>电子书 ID</v-list-item-title>
                <v-list-item-subtitle>{{ result.ebook_id }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item>
                <v-list-item-title>文件路径</v-list-item-title>
                <v-list-item-subtitle class="text-wrap">{{ result.ebook_path }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>

            <div class="mt-4">
              <v-btn
                v-if="result.ebook_id"
                color="primary"
                prepend-icon="mdi-book-open-page-variant"
                @click="goToWorkDetail"
              >
                查看作品
              </v-btn>
            </div>
          </div>

          <!-- 错误信息 -->
          <v-alert v-if="errorMessage" type="error">
            {{ errorMessage }}
          </v-alert>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { novelApi } from '@/services/api'

const router = useRouter()

// 表单状态
const file = ref<File | null>(null)
const title = ref<string>('')
const author = ref<string>('')
const description = ref<string>('')

// UI 状态
const loading = ref(false)
const result = ref<{
  success: boolean
  ebook_path: string
  ebook_id: number | null
  message: string
} | null>(null)
const errorMessage = ref<string | null>(null)
const formRef = ref<any>(null)

// 文件校验规则
const fileRules = [
  (v: File | null) => {
    if (!v) return '请选择文件'
    if (!v.name.toLowerCase().endsWith('.txt')) {
      return '只支持 .txt 文件'
    }
    return true
  }
]

// 提交表单
const handleSubmit = async () => {
  if (!file.value) {
    errorMessage.value = '请选择文件'
    return
  }

  loading.value = true
  errorMessage.value = null
  result.value = null

  try {
    // 组装 FormData
    const formData = new FormData()
    formData.append('file', file.value)
    if (title.value) formData.append('title', title.value)
    if (author.value) formData.append('author', author.value)
    if (description.value) formData.append('description', description.value)

    // 调用 API
    const response = await novelApi.uploadTxtNovel(formData)
    
    // 处理响应（根据实际响应格式调整）
    const responseData = response.data as Record<string, unknown> | undefined
    if (responseData) {
      if (typeof responseData === 'object' && 'success' in responseData) {
        result.value = responseData as unknown as typeof result.value
      } else if (responseData.data) {
        result.value = responseData.data as unknown as typeof result.value
      } else {
        result.value = responseData as unknown as typeof result.value
      }
    }
  } catch (err: any) {
    console.error('导入失败:', err)
    errorMessage.value = err.response?.data?.error_message || 
                        err.response?.data?.message || 
                        err.message || 
                        '导入失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

// 重置表单
const handleReset = () => {
  file.value = null
  title.value = ''
  author.value = ''
  description.value = ''
  result.value = null
  errorMessage.value = null
  formRef.value?.reset()
}

// 跳转到作品详情页
const goToWorkDetail = () => {
  if (result.value?.ebook_id) {
    router.push(`/works/${result.value.ebook_id}`)
  }
}
</script>

<style scoped>
.novel-import-demo-page {
  padding: 16px;
}
</style>

