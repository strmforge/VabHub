<template>
  <div class="transfer-history-page">
    <PageHeader
      title="媒体整理"
      subtitle="查看文件转移历史记录"
    />
    
    <!-- 搜索栏 -->
    <v-card class="mb-4">
      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="8">
            <v-text-field
              v-model="searchTitle"
              label="搜索转移记录"
              variant="outlined"
              density="compact"
              prepend-inner-icon="mdi-magnify"
              clearable
              @keyup.enter="loadHistory"
              @click:clear="loadHistory"
            />
          </v-col>
          
          <v-col cols="12" md="4">
            <v-select
              v-model="statusFilter"
              :items="statusOptions"
              label="状态过滤"
              variant="outlined"
              density="compact"
              clearable
              @update:model-value="loadHistory"
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>
    
    <!-- 转移历史表格 -->
    <v-card>
      <v-data-table
        :headers="headers"
        :items="histories"
        :loading="loading"
        :items-per-page="itemsPerPage"
        :page="page"
        :items-length="total"
        @update:page="handlePageChange"
        @update:items-per-page="handleItemsPerPageChange"
        class="transfer-table"
      >
        <template v-slot:item.title="{ item }">
          <div class="d-flex align-center">
            <v-avatar
              v-if="item.image"
              size="40"
              class="me-2"
            >
              <v-img :src="item.image" :alt="item.title" />
            </v-avatar>
            <div>
              <div class="font-weight-medium">{{ item.title || '未知' }}</div>
              <div v-if="item.seasons || item.episodes" class="text-caption text-medium-emphasis">
                <span v-if="item.seasons">{{ item.seasons }}</span>
                <span v-if="item.episodes">{{ item.episodes }}</span>
              </div>
            </div>
          </div>
        </template>
        
        <template v-slot:item.path="{ item }">
          <div class="path-cell">
            <div class="text-body-2">
              <span class="text-medium-emphasis">{{ item.src_storage }}</span>
              <span class="mx-1">/</span>
              <span class="text-truncate" :title="item.src">{{ truncatePath(item.src) }}</span>
            </div>
            <div class="text-body-2 mt-1">
              <v-icon size="small" class="me-1">mdi-arrow-right</v-icon>
              <span class="text-medium-emphasis">{{ item.dest_storage }}</span>
              <span class="mx-1">/</span>
              <span class="text-truncate" :title="item.dest">{{ truncatePath(item.dest) }}</span>
            </div>
          </div>
        </template>
        
        <template v-slot:item.mode="{ item }">
          <v-chip
            :color="getModeColor(item.mode)"
            size="small"
            variant="flat"
          >
            {{ getModeText(item.mode) }}
          </v-chip>
        </template>
        
        <template v-slot:item.file_size="{ item }">
          {{ formatBytes(item.file_size || 0) }}
        </template>
        
        <template v-slot:item.date="{ item }">
          {{ item.date || formatDateTime(item.created_at) }}
        </template>
        
        <template v-slot:item.status="{ item }">
          <v-chip
            :color="item.status ? 'success' : 'error'"
            size="small"
            variant="flat"
          >
            <v-icon start size="small">
              {{ item.status ? 'mdi-check-circle' : 'mdi-alert-circle' }}
            </v-icon>
            {{ item.status ? '成功' : '失败' }}
          </v-chip>
          <div v-if="!item.status && item.errmsg" class="text-caption text-error mt-1">
            {{ item.errmsg }}
          </div>
        </template>
        
        <template v-slot:item.actions="{ item }">
          <v-menu>
            <template v-slot:activator="{ props }">
              <v-btn
                v-bind="props"
                icon="mdi-dots-vertical"
                variant="text"
                size="small"
              />
            </template>
            <v-list>
              <v-list-item @click="viewDetails(item)">
                <v-list-item-title>
                  <v-icon class="me-2">mdi-information</v-icon>
                  查看详情
                </v-list-item-title>
              </v-list-item>
              <v-list-item
                v-if="!item.status"
                @click="openManualTransferDialog(item)"
                class="text-warning"
              >
                <v-list-item-title>
                  <v-icon class="me-2">mdi-folder-move</v-icon>
                  手动整理
                </v-list-item-title>
              </v-list-item>
              <v-list-item
                v-if="item.status"
                @click="copyPath(item.dest)"
              >
                <v-list-item-title>
                  <v-icon class="me-2">mdi-content-copy</v-icon>
                  复制目标路径
                </v-list-item-title>
              </v-list-item>
              <v-divider />
              <v-list-item
                @click="deleteHistory(item)"
                class="text-error"
              >
                <v-list-item-title>
                  <v-icon class="me-2">mdi-delete</v-icon>
                  删除记录
                </v-list-item-title>
              </v-list-item>
            </v-list>
          </v-menu>
        </template>
      </v-data-table>
    </v-card>
    
    <!-- 详情对话框 -->
    <v-dialog v-model="showDetailsDialog" max-width="800">
      <v-card v-if="selectedHistory">
        <v-card-title>转移详情</v-card-title>
        <v-card-text>
          <v-row>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis mb-1">标题</div>
              <div class="text-body-1 font-weight-medium">{{ selectedHistory.title || '未知' }}</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis mb-1">类型</div>
              <div class="text-body-1">{{ selectedHistory.type || '-' }}</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis mb-1">分类</div>
              <div class="text-body-1">{{ selectedHistory.category || '-' }}</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis mb-1">年份</div>
              <div class="text-body-1">{{ selectedHistory.year || '-' }}</div>
            </v-col>
            <v-col cols="12">
              <div class="text-caption text-medium-emphasis mb-1">源路径</div>
              <div class="text-body-2 font-family-monospace">{{ selectedHistory.src }}</div>
            </v-col>
            <v-col cols="12">
              <div class="text-caption text-medium-emphasis mb-1">目标路径</div>
              <div class="text-body-2 font-family-monospace">{{ selectedHistory.dest }}</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis mb-1">转移方式</div>
              <div class="text-body-1">{{ getModeText(selectedHistory.mode) }}</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis mb-1">文件大小</div>
              <div class="text-body-1">{{ formatBytes(selectedHistory.file_size || 0) }}</div>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis mb-1">状态</div>
              <v-chip
                :color="selectedHistory.status ? 'success' : 'error'"
                size="small"
              >
                {{ selectedHistory.status ? '成功' : '失败' }}
              </v-chip>
            </v-col>
            <v-col cols="12" md="6">
              <div class="text-caption text-medium-emphasis mb-1">时间</div>
              <div class="text-body-1">{{ selectedHistory.date || formatDateTime(selectedHistory.created_at) }}</div>
            </v-col>
            <v-col cols="12" v-if="!selectedHistory.status && selectedHistory.errmsg">
              <div class="text-caption text-medium-emphasis mb-1">错误信息</div>
              <div class="text-body-2 text-error">{{ selectedHistory.errmsg }}</div>
            </v-col>
          </v-row>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showDetailsDialog = false">关闭</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 手动整理对话框 -->
    <ManualTransferDialog
      v-if="showManualTransferDialog"
      :config="manualTransferConfig"
      @close="closeManualTransferDialog"
      @complete="onManualTransferComplete"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/common/PageHeader.vue'
import ManualTransferDialog from '@/components/media/ManualTransferDialog.vue'
import api from '@/services/api'

const toast = useToast()

// 数据
const histories = ref<any[]>([])
const loading = ref(false)
const searchTitle = ref('')
const statusFilter = ref<string | null>(null)
const page = ref(1)
const itemsPerPage = ref(50)
const total = ref(0)

// 对话框
const showDetailsDialog = ref(false)
const selectedHistory = ref<any>(null)

// 状态选项
const statusOptions = [
  { title: '成功', value: 'success' },
  { title: '失败', value: 'failed' }
]

// 表格列
const headers = [
  { title: '标题', key: 'title', sortable: false, width: '200px' },
  { title: '路径', key: 'path', sortable: false },
  { title: '转移方式', key: 'mode', sortable: false, width: '120px' },
  { title: '大小', key: 'file_size', sortable: false, width: '120px' },
  { title: '时间', key: 'date', sortable: false, width: '180px' },
  { title: '状态', key: 'status', sortable: false, width: '120px' },
  { title: '操作', key: 'actions', sortable: false, width: '80px', align: 'end' as const }
]

// 加载历史记录
const loadHistory = async () => {
  loading.value = true
  try {
    const params: any = {
      page: page.value,
      count: itemsPerPage.value
    }
    
    if (searchTitle.value) {
      params.title = searchTitle.value
    }
    
    if (statusFilter.value) {
      params.status_filter = statusFilter.value
    }
    
    const response = await api.get('/transfer-history/', { params })
    
    histories.value = response.data.list || []
    total.value = response.data.total || 0
  } catch (error: any) {
    toast.error(error.message || '加载转移历史失败')
  } finally {
    loading.value = false
  }
}

// 分页变化
const handlePageChange = (newPage: number) => {
  page.value = newPage
  loadHistory()
}

const handleItemsPerPageChange = (newItemsPerPage: number) => {
  itemsPerPage.value = newItemsPerPage
  page.value = 1
  loadHistory()
}

// 获取转移方式文本
const getModeText = (mode: string): string => {
  const modeMap: Record<string, string> = {
    'move': '移动',
    'copy': '复制',
    'link': '硬链接',
    'softlink': '软链接'
  }
  return modeMap[mode] || mode
}

// 获取转移方式颜色
const getModeColor = (mode: string): string => {
  const colorMap: Record<string, string> = {
    'move': 'primary',
    'copy': 'info',
    'link': 'success',
    'softlink': 'warning'
  }
  return colorMap[mode] || 'default'
}

// 截断路径
const truncatePath = (path: string, maxLength: number = 50): string => {
  if (path.length <= maxLength) return path
  return '...' + path.slice(-maxLength)
}

// 格式化字节
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 格式化日期时间
const formatDateTime = (dateStr: string): string => {
  if (!dateStr) return '-'
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

// 查看详情
const viewDetails = (item: any) => {
  selectedHistory.value = item
  showDetailsDialog.value = true
}

// 复制路径
const copyPath = async (path: string) => {
  try {
    await navigator.clipboard.writeText(path)
    toast.success('路径已复制到剪贴板')
  } catch (error) {
    toast.error('复制失败')
  }
}

// 删除历史记录
const deleteHistory = async (item: any) => {
  if (!confirm('确定要删除这条转移历史记录吗？')) {
    return
  }
  
  try {
    await api.delete(`/transfer-history/${item.id}`)
    toast.success('删除成功')
    loadHistory()
  } catch (error: any) {
    toast.error(error.message || '删除失败')
  }
}

// 手动整理相关
const showManualTransferDialog = ref(false)
const manualTransferConfig = ref<any>(null)

// 打开手动整理对话框
const openManualTransferDialog = async (item: any) => {
  try {
    const response = await api.get(`/transfer-history/${item.id}/manual-config`)
    manualTransferConfig.value = response.data  // axios interceptor already unwrapped
    showManualTransferDialog.value = true
  } catch (error: any) {
    toast.error(error.message || '获取手动整理配置失败')
  }
}

// 关闭手动整理对话框
const closeManualTransferDialog = () => {
  showManualTransferDialog.value = false
  manualTransferConfig.value = null
}

// 手动整理完成回调
const onManualTransferComplete = (success: boolean) => {
  closeManualTransferDialog()
  if (success) {
    toast.success('手动整理完成')
    loadHistory() // 刷新列表
  }
}

// 初始化
onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.transfer-history-page {
  padding: 24px;
}

.transfer-table {
  width: 100%;
}

.path-cell {
  max-width: 500px;
}

.font-family-monospace {
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  word-break: break-all;
}
</style>

