<template>
  <v-dialog
    :model-value="modelValue"
    max-width="500"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card>
      <v-card-title>
        115网盘登录
      </v-card-title>
      
      <v-card-text>
        <div v-if="qrUrl" class="text-center">
          <v-alert type="info" variant="tonal" class="mb-4">
            请使用115网盘App扫描二维码登录
          </v-alert>
          
          <!-- 二维码显示 -->
          <div class="mb-4">
            <img
              :src="qrImageUrl"
              alt="二维码"
              style="max-width: 100%; height: auto;"
            />
          </div>
          
          <!-- 状态提示 -->
          <div v-if="status === 0" class="text-body-2 text-warning">
            等待扫描...
          </div>
          <div v-else-if="status === 1" class="text-body-2 text-info">
            已扫描，等待确认...
          </div>
          <div v-else-if="status === 2" class="text-body-2 text-success">
            登录成功！
          </div>
          <div v-else-if="status === -1" class="text-body-2 text-error">
            登录失败或已过期
          </div>
        </div>
        
        <div v-else class="text-center">
          <v-progress-circular
            indeterminate
            color="primary"
          ></v-progress-circular>
          <div class="mt-4 text-body-2">
            正在生成二维码...
          </div>
        </div>
      </v-card-text>
      
      <v-card-actions>
        <v-spacer></v-spacer>
        <v-btn
          v-if="qrUrl"
          color="primary"
          :loading="checking"
          @click="checkStatus"
        >
          检查状态
        </v-btn>
        <v-btn
          variant="text"
          @click="$emit('update:modelValue', false)"
        >
          关闭
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import api from '@/services/api'

const props = defineProps<{
  modelValue: boolean
  storageId: number | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  authenticated: []
}>()
const qrUrl = ref('')
const qrImageUrl = ref('')
const status = ref<number | null>(null)
const checking = ref(false)
let statusCheckInterval: number | null = null

// 生成二维码
const generateQRCode = async () => {
  if (!props.storageId) {
    return
  }
  
  try {
    const response = await api.post(`/cloud-storage/${props.storageId}/qr-code`)
    qrUrl.value = response.data.qr_url
    // 使用qrcode库生成二维码图片URL
    // 这里简化处理，实际应该使用qrcode库生成图片
    qrImageUrl.value = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(qrUrl.value)}`
    status.value = 0
  } catch (error) {
    console.error('生成二维码失败:', error)
    alert('生成二维码失败')
  }
}

// 检查登录状态
const checkStatus = async () => {
  if (!props.storageId) {
    return
  }
  
  try {
    checking.value = true
    const response = await api.get(`/cloud-storage/${props.storageId}/qr-status`)
    status.value = response.data.status
    
    if (response.data.status === 2) {
      // 登录成功
      clearInterval(statusCheckInterval!)
      statusCheckInterval = null
      emit('authenticated')
      emit('update:modelValue', false)
    } else if (response.data.status === -1) {
      // 登录失败
      clearInterval(statusCheckInterval!)
      statusCheckInterval = null
    }
  } catch (error) {
    console.error('检查登录状态失败:', error)
  } finally {
    checking.value = false
  }
}

// 开始自动检查状态
const startStatusCheck = () => {
  if (statusCheckInterval) {
    return
  }
  
  statusCheckInterval = window.setInterval(() => {
    if (status.value !== null && status.value !== 2 && status.value !== -1) {
      checkStatus()
    }
  }, 2000) // 每2秒检查一次
}

// 停止自动检查
const stopStatusCheck = () => {
  if (statusCheckInterval) {
    clearInterval(statusCheckInterval)
    statusCheckInterval = null
  }
}

// 监听对话框显示
watch(() => props.modelValue, (visible) => {
  if (visible && props.storageId) {
    generateQRCode()
    startStatusCheck()
  } else {
    stopStatusCheck()
    qrUrl.value = ''
    qrImageUrl.value = ''
    status.value = null
  }
})

onUnmounted(() => {
  stopStatusCheck()
})
</script>

<style scoped>
</style>

