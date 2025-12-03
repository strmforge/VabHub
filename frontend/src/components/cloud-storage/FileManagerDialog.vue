<template>
  <v-dialog
    :model-value="modelValue"
    max-width="1200"
    fullscreen
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <v-card>
      <v-card-title>
        <span>文件管理</span>
        <v-spacer></v-spacer>
        <v-btn
          icon="mdi-close"
          variant="text"
          @click="$emit('update:modelValue', false)"
        ></v-btn>
      </v-card-title>
      
      <v-card-text>
        <v-row>
          <v-col cols="12">
            <!-- 路径导航 -->
            <v-breadcrumbs
              :items="pathItems"
              class="pa-0"
            >
              <template v-slot:divider>
                <v-icon>mdi-chevron-right</v-icon>
              </template>
            </v-breadcrumbs>
          </v-col>
        </v-row>
        
        <v-row>
          <v-col cols="12">
            <!-- 文件列表 -->
            <v-data-table
              :headers="headers"
              :items="files"
              :loading="loading"
              class="elevation-1"
            >
              <template v-slot:item.name="{ item }">
                <div class="d-flex align-center">
                  <v-icon
                    :icon="item.type === 'dir' ? 'mdi-folder' : 'mdi-file'"
                    :color="item.type === 'dir' ? 'amber' : 'grey'"
                    class="mr-2"
                  ></v-icon>
                  <span>{{ item.name }}</span>
                </div>
              </template>
              
              <template v-slot:item.size="{ item }">
                {{ formatBytes(item.size) }}
              </template>
              
              <template v-slot:item.actions="{ item }">
                <v-btn
                  v-if="item.type === 'dir'"
                  icon="mdi-folder-open"
                  size="small"
                  variant="text"
                  @click="enterFolder(item.path)"
                ></v-btn>
                <v-btn
                  v-if="item.type === 'file'"
                  icon="mdi-download"
                  size="small"
                  variant="text"
                  @click="downloadFile(item)"
                ></v-btn>
              </template>
            </v-data-table>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
  </v-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import api from '@/services/api'

const props = defineProps<{
  modelValue: boolean
  storageId: number | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()
const files = ref<any[]>([])
const currentPath = ref('/')
const loading = ref(false)

const headers = [
  { title: '名称', key: 'name' },
  { title: '大小', key: 'size' },
  { title: '修改时间', key: 'modified_at' },
  { title: '操作', key: 'actions', sortable: false }
]

// 路径导航项
const pathItems = computed(() => {
  const parts = currentPath.value.split('/').filter(p => p)
  const items = [
    { title: '根目录', disabled: false, href: '#' }
  ]
  
  let current = ''
  parts.forEach((part, index) => {
    current += '/' + part
    items.push({
      title: part,
      disabled: index === parts.length - 1,
      href: '#'
    })
  })
  
  return items
})

// 加载文件列表
const loadFiles = async () => {
  if (!props.storageId) {
    return
  }
  
  try {
    loading.value = true
    const response = await api.get(`/cloud-storage/${props.storageId}/files`, {
      params: {
        path: currentPath.value,
        recursive: false
      }
    })
    // 统一响应格式：response.data 已经是 data 字段的内容
    // 如果是分页响应，data 包含 {items, total, page, page_size, total_pages}
    // 如果是列表响应，data 是数组或对象
    if (response.data && response.data.items && Array.isArray(response.data.items)) {
      // 分页响应格式
      files.value = response.data.items
    } else if (response.data && response.data.files && Array.isArray(response.data.files)) {
      // 兼容旧格式（如果API返回 {files: [...]}）
      files.value = response.data.files
    } else if (Array.isArray(response.data)) {
      // 直接数组格式
      files.value = response.data
    } else {
      files.value = []
      console.warn('文件列表数据格式不正确:', response.data)
    }
  } catch (error) {
    console.error('加载文件列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 进入文件夹
const enterFolder = (path: string) => {
  currentPath.value = path
  loadFiles()
}

// 下载文件
const downloadFile = (file: any) => {
  // TODO: 实现文件下载
  console.log('下载文件:', file)
}

// 格式化字节
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 监听对话框显示
watch(() => props.modelValue, (visible) => {
  if (visible && props.storageId) {
    currentPath.value = '/'
    loadFiles()
  }
})

// 监听路径变化
watch(() => currentPath.value, () => {
  if (props.modelValue && props.storageId) {
    loadFiles()
  }
})
</script>

<style scoped>
</style>

