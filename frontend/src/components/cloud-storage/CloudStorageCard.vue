<template>
  <v-card>
    <v-card-title>
      <div class="d-flex align-center">
        <v-icon
          :icon="providerIcon"
          :color="providerColor"
          size="24"
          class="mr-2"
        ></v-icon>
        <span>{{ storage.name }}</span>
      </div>
      <v-spacer></v-spacer>
      <v-chip
        :color="storage.enabled ? 'success' : 'error'"
        size="small"
        variant="tonal"
      >
        {{ storage.enabled ? '已启用' : '已禁用' }}
      </v-chip>
    </v-card-title>
    
    <v-card-text>
      <div class="text-body-2 mb-2">
        <strong>提供商:</strong> {{ providerName }}
      </div>
      
      <div v-if="storage.user_name" class="text-body-2 mb-2">
        <strong>用户名:</strong> {{ storage.user_name }}
      </div>
      
      <div v-if="storage.rclone_remote_name" class="text-body-2 mb-2">
        <strong>远程名称:</strong> {{ storage.rclone_remote_name }}
      </div>
      
      <!-- 存储使用情况 -->
      <div v-if="usage" class="mt-4">
        <div class="text-body-2 mb-2">
          <strong>存储使用情况</strong>
        </div>
        <v-progress-linear
          :model-value="usage.percentage"
          :color="getUsageColor(usage.percentage)"
          height="20"
          rounded
        >
          <template v-slot:default>
            <span class="text-white text-caption">
              {{ formatBytes(usage.used) }} / {{ formatBytes(usage.total) }}
              ({{ usage.percentage.toFixed(1) }}%)
            </span>
          </template>
        </v-progress-linear>
      </div>
    </v-card-text>
    
    <v-card-actions>
      <v-btn
        v-if="storage.provider === '115' && !storage.user_id"
        color="primary"
        variant="text"
        size="small"
        @click="$emit('authenticate', storage)"
      >
        登录
      </v-btn>
      <v-btn
        v-else-if="storage.provider === '115' && storage.user_id"
        color="success"
        variant="text"
        size="small"
        disabled
      >
        已登录
      </v-btn>
      <v-btn
        color="primary"
        variant="text"
        size="small"
        @click="emit('viewFiles', storage)"
      >
        查看文件
      </v-btn>
      <v-spacer></v-spacer>
      <v-btn
        icon="mdi-pencil"
        size="small"
        variant="text"
        @click="$emit('edit', storage)"
      ></v-btn>
      <v-btn
        icon="mdi-delete"
        size="small"
        variant="text"
        color="error"
        @click="handleDelete"
      ></v-btn>
    </v-card-actions>
  </v-card>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'

const props = defineProps<{
  storage: any
}>()

const emit = defineEmits<{
  refresh: []
  authenticate: [storage: any]
  viewFiles: [storage: any]
  edit: [storage: any]
}>()
const usage = ref<any>(null)

// 提供商图标和颜色
const providerIcon = computed(() => {
  switch (props.storage.provider) {
    case '115':
      return 'mdi-cloud'
    case 'rclone':
      return 'mdi-server-network'
    case 'openlist':
      return 'mdi-open-in-app'
    default:
      return 'mdi-cloud'
  }
})

const providerColor = computed(() => {
  switch (props.storage.provider) {
    case '115':
      return 'blue'
    case 'rclone':
      return 'green'
    case 'openlist':
      return 'orange'
    default:
      return 'grey'
  }
})

const providerName = computed(() => {
  switch (props.storage.provider) {
    case '115':
      return '115网盘'
    case 'rclone':
      return 'RClone'
    case 'openlist':
      return 'OpenList'
    default:
      return '未知'
  }
})

// 获取存储使用情况
const loadUsage = async () => {
  try {
    const response = await api.get(`/cloud-storage/${props.storage.id}/usage`)
    usage.value = response.data
  } catch (error) {
    console.error('获取存储使用情况失败:', error)
  }
}

// 格式化字节
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 获取使用率颜色
const getUsageColor = (percentage: number): string => {
  if (percentage < 50) return 'success'
  if (percentage < 80) return 'warning'
  return 'error'
}

// 处理删除
const handleDelete = async () => {
  if (!confirm('确定要删除这个云存储配置吗？')) {
    return
  }
  
  try {
    await api.delete(`/cloud-storage/${props.storage.id}`)
    emit('refresh')
  } catch (error) {
    console.error('删除云存储配置失败:', error)
    alert('删除失败')
  }
}

onMounted(() => {
  loadUsage()
})
</script>

<style scoped>
</style>

