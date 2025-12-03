<template>
  <div class="file-browser-page">
    <PageHeader
      title="文件管理"
      subtitle="浏览、管理本地和云存储文件"
    />
    
    <!-- 主布局：左侧目录树 + 右侧文件列表 -->
    <v-row class="file-browser-layout" no-gutters>
      <!-- 左侧目录树导航（桌面端显示） -->
      <v-col v-if="showTree" cols="12" md="3" class="file-navigator-col">
        <FileNavigator
          :storage="selectedStorage"
          :current-path="currentPath"
          @navigate="handleNavigate"
        />
      </v-col>
      
      <!-- 右侧主内容区 -->
      <v-col :cols="showTree ? 12 : 12" :md="showTree ? 9 : 12">
        <!-- 工具栏 -->
        <v-card class="mb-4">
          <v-card-text class="pa-2">
            <v-row align="center" no-gutters>
              <!-- 存储选择 -->
              <v-col cols="auto" class="me-2">
                <v-menu>
                  <template v-slot:activator="{ props }">
                    <v-btn
                      v-bind="props"
                      variant="text"
                      density="compact"
                      prepend-icon="mdi-folder-network"
                    >
                      {{ getStorageName(selectedStorage) }}
                      <v-icon end>mdi-chevron-down</v-icon>
                    </v-btn>
                  </template>
                  <v-list>
                    <v-list-item
                      v-for="storage in storageOptions"
                      :key="storage.value"
                      :active="selectedStorage === storage.value"
                      @click="handleStorageChange(storage.value)"
                    >
                      <template v-slot:prepend>
                        <v-icon :icon="getStorageIcon(storage.value)" />
                      </template>
                      <v-list-item-title>{{ storage.title }}</v-list-item-title>
                    </v-list-item>
                  </v-list>
                </v-menu>
              </v-col>
              
              <!-- 路径导航 -->
              <v-col cols="auto" class="me-2">
                <v-btn
                  variant="text"
                  density="compact"
                  :disabled="currentPath === '/'"
                  @click="navigateUp"
                >
                  <v-icon start>mdi-arrow-up</v-icon>
                  上一级
                </v-btn>
              </v-col>
              
              <!-- 路径面包屑 -->
              <v-col cols="auto" class="flex-grow-1">
                <v-breadcrumbs
                  :items="pathBreadcrumbs"
                  class="pa-0"
                  density="compact"
                >
                  <template v-slot:divider>
                    <v-icon size="small">mdi-chevron-right</v-icon>
                  </template>
                  <template v-slot:item="{ item }">
                    <v-btn
                      variant="text"
                      density="compact"
                      :disabled="item.disabled"
                      @click="navigateToBreadcrumb(item)"
                    >
                      {{ item.title }}
                    </v-btn>
                  </template>
                </v-breadcrumbs>
              </v-col>
              
              <!-- 工具栏按钮 -->
              <v-col cols="auto" class="d-flex align-center">
                <v-btn
                  icon="mdi-sort"
                  variant="text"
                  density="compact"
                  @click="toggleSort"
                >
                  <v-icon>{{ sortIcon }}</v-icon>
                </v-btn>
                
                <v-btn
                  icon="mdi-refresh"
                  variant="text"
                  density="compact"
                  :loading="loading"
                  @click="refreshFiles"
                />
                
                <v-btn
                  icon="mdi-folder-plus"
                  variant="text"
                  density="compact"
                  @click="showCreateFolderDialog = true"
                />
                
                <v-btn
                  icon="mdi-view-list"
                  variant="text"
                  density="compact"
                  :active="viewMode === 'list'"
                  @click="viewMode = 'list'"
                />
                
                <v-btn
                  icon="mdi-view-grid"
                  variant="text"
                  density="compact"
                  :active="viewMode === 'grid'"
                  @click="viewMode = 'grid'"
                />
                
                <v-btn
                  icon="mdi-file-tree"
                  variant="text"
                  density="compact"
                  :active="showTree"
                  @click="showTree = !showTree"
                  class="d-md-none"
                />
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
    
        <!-- 搜索栏 -->
        <v-card class="mb-4">
          <v-card-text class="pa-2">
            <v-text-field
              v-model="searchQuery"
              label="搜索文件..."
              variant="outlined"
              density="compact"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
              @keyup.enter="handleSearch"
              @click:clear="handleSearch"
            />
          </v-card-text>
        </v-card>
        
        <!-- 统计信息 -->
        <v-row class="mb-4">
          <v-col cols="12" sm="6" md="3">
            <v-card variant="elevated" color="primary" class="stat-card">
              <v-card-text class="pa-4 text-center">
                <v-icon size="32" class="mb-2">mdi-file-multiple</v-icon>
                <div class="stat-number">{{ stats.total }}</div>
                <div class="stat-label">总文件数</div>
              </v-card-text>
            </v-card>
          </v-col>
          
          <v-col cols="12" sm="6" md="3">
            <v-card variant="elevated" color="success" class="stat-card">
              <v-card-text class="pa-4 text-center">
                <v-icon size="32" class="mb-2">mdi-folder</v-icon>
                <div class="stat-number">{{ stats.dirs }}</div>
                <div class="stat-label">目录数</div>
              </v-card-text>
            </v-card>
          </v-col>
          
          <v-col cols="12" sm="6" md="3">
            <v-card variant="elevated" color="info" class="stat-card">
              <v-card-text class="pa-4 text-center">
                <v-icon size="32" class="mb-2">mdi-movie</v-icon>
                <div class="stat-number">{{ stats.mediaFiles }}</div>
                <div class="stat-label">媒体文件</div>
              </v-card-text>
            </v-card>
          </v-col>
          
          <v-col cols="12" sm="6" md="3">
            <v-card variant="elevated" color="warning" class="stat-card">
              <v-card-text class="pa-4 text-center">
                <v-icon size="32" class="mb-2">mdi-harddisk</v-icon>
                <div class="stat-number">{{ formatBytes(storageUsage?.used || 0) }}</div>
                <div class="stat-label">已使用空间</div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
        
        <!-- 批量操作工具栏 -->
        <v-card v-if="selectedFiles.length > 0" class="mb-4" color="primary" variant="flat">
          <v-card-text class="pa-2">
            <v-row align="center" no-gutters>
              <v-col cols="auto" class="me-2">
                <v-chip color="white" variant="flat">
                  <v-icon start>mdi-checkbox-multiple-marked</v-icon>
                  已选择 {{ selectedFiles.length }} 项
                </v-chip>
              </v-col>
              <v-col cols="auto" class="me-2">
                <v-btn
                  variant="text"
                  density="compact"
                  prepend-icon="mdi-text-recognition"
                  @click="handleBatchRecognize"
                >
                  批量识别
                </v-btn>
              </v-col>
              <v-col cols="auto" class="me-2">
                <v-btn
                  variant="text"
                  density="compact"
                  prepend-icon="mdi-auto-fix"
                  @click="handleBatchScrape"
                >
                  批量刮削
                </v-btn>
              </v-col>
              <v-col cols="auto" class="me-2">
                <v-btn
                  variant="text"
                  density="compact"
                  prepend-icon="mdi-folder-arrow-right"
                  @click="handleBatchTransfer"
                >
                  批量整理
                </v-btn>
              </v-col>
              <v-col cols="auto" class="me-2">
                <v-btn
                  variant="text"
                  density="compact"
                  prepend-icon="mdi-delete"
                  @click="handleBatchDelete"
                >
                  批量删除
                </v-btn>
              </v-col>
              <v-spacer />
              <v-col cols="auto">
                <v-btn
                  icon="mdi-close"
                  variant="text"
                  density="compact"
                  @click="selectedFiles = []"
                />
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
        
        <!-- 文件详情/图片预览 -->
        <v-card v-if="selectedFile && selectedFile.type === 'file' && !isDirectory" class="mb-4">
          <v-card-text>
            <div v-if="isImageFile(selectedFile)" class="text-center">
              <v-img
                :src="getImageUrl(selectedFile)"
                max-width="100%"
                max-height="600px"
                contain
                class="mb-4"
              />
            </div>
            <div v-else class="text-center">
              <v-icon size="64" :icon="getFileIcon(selectedFile.extension)" class="mb-2" />
              <div class="text-h6 mt-2">{{ selectedFile.name }}</div>
              <div class="text-body-2 text-medium-emphasis mt-2">
                <div>大小: {{ formatBytes(selectedFile.size) }}</div>
                <div v-if="selectedFile.modify_time">
                  修改时间: {{ formatTime(selectedFile.modify_time) }}
                </div>
              </div>
              <v-btn
                v-if="selectedStorage === 'local'"
                color="primary"
                prepend-icon="mdi-download"
                class="mt-4"
                @click="handleDownload(selectedFile)"
              >
                下载文件
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
        
        <!-- 文件列表 -->
        <FileList
          :files="filteredFiles"
          :loading="loading"
          :view-mode="viewMode"
          :selected-files="selectedFiles"
          @select="handleFileSelect"
          @navigate="handleNavigate"
          @action="handleFileAction"
        />
      </v-col>
    </v-row>
    
    <!-- 创建文件夹对话框 -->
    <v-dialog v-model="showCreateFolderDialog" max-width="500">
      <v-card>
        <v-card-title>新建文件夹</v-card-title>
        <v-card-text>
          <v-text-field
            v-model="newFolderName"
            label="文件夹名称"
            variant="outlined"
            autofocus
            @keyup.enter="handleCreateFolder"
          />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="showCreateFolderDialog = false">取消</v-btn>
          <v-btn color="primary" @click="handleCreateFolder">创建</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
    
    <!-- 文件操作对话框 -->
    <FileOperationDialog
      v-model="showOperationDialog"
      :file="selectedFile"
      :operation="currentOperation"
      @success="handleOperationSuccess"
    />
    
    <!-- 媒体识别结果对话框 -->
    <MediaInfoDialog
      v-model="showMediaInfoDialog"
      :media-info="mediaInfo"
    />
    
    <!-- 进度对话框 -->
    <v-dialog v-model="showProgressDialog" persistent max-width="500">
      <v-card>
        <v-card-title>{{ progressTitle }}</v-card-title>
        <v-card-text>
          <v-progress-linear
            :model-value="progressValue"
            :indeterminate="progressIndeterminate"
            color="primary"
            class="mb-4"
          />
          <div class="text-body-2">{{ progressText }}</div>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useToast } from '@/composables/useToast'
import { useDisplay } from 'vuetify'
import PageHeader from '@/components/common/PageHeader.vue'
import FileList from '@/components/file-browser/FileList.vue'
import FileNavigator from '@/components/file-browser/FileNavigator.vue'
import FileOperationDialog from '@/components/file-browser/FileOperationDialog.vue'
import MediaInfoDialog from '@/components/file-browser/MediaInfoDialog.vue'
import api from '@/services/api'

const toast = useToast()
const display = useDisplay()

// 存储和路径
const selectedStorage = ref('local')
const currentPath = ref('/')
const pathStack = ref<any[]>([]) // 路径堆栈
const showTree = ref(display.mdAndUp.value) // 默认桌面端显示目录树
const searchQuery = ref('')
const sortMode = ref<'name' | 'time' | 'size'>('name')

const storageOptions = [
  { title: '本地存储', value: 'local' },
  { title: '115网盘', value: '115' },
  { title: 'RClone', value: 'rclone' },
  { title: 'OpenList', value: 'openlist' }
]

// 文件列表
const files = ref<any[]>([])
const loading = ref(false)
const viewMode = ref<'list' | 'grid'>('list')
const selectedFiles = ref<string[]>([])

// 统计信息
const stats = ref({
  total: 0,
  dirs: 0,
  files: 0,
  mediaFiles: 0
})

const storageUsage = ref<any>(null)

// 对话框
const showCreateFolderDialog = ref(false)
const newFolderName = ref('')
const showOperationDialog = ref(false)
const selectedFile = ref<any>(null)
const currentOperation = ref<string | null>(null)
const showMediaInfoDialog = ref(false)
const mediaInfo = ref<any>(null)
const showProgressDialog = ref(false)
const progressTitle = ref('')
const progressText = ref('')
const progressValue = ref(0)
const progressIndeterminate = ref(false)

// 路径面包屑
const pathBreadcrumbs = computed(() => {
  if (!currentPath.value || currentPath.value === '/') {
    return [{ title: getStorageName(selectedStorage.value), disabled: false, path: '/' }]
  }
  
  const parts = currentPath.value.split('/').filter(p => p)
  const breadcrumbs = [{ title: getStorageName(selectedStorage.value), disabled: false, path: '/' }]
  
  let path = ''
  parts.forEach((part, index) => {
    path += '/' + part
    breadcrumbs.push({
      title: part,
      disabled: index === parts.length - 1,
      path: path
    })
  })
  
  return breadcrumbs
})

// 过滤后的文件列表
const filteredFiles = computed(() => {
  let result = [...files.value]
  
  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(file => 
      file.name.toLowerCase().includes(query) ||
      file.path.toLowerCase().includes(query)
    )
  }
  
  // 排序
  result.sort((a, b) => {
    if (sortMode.value === 'name') {
      // 目录优先，然后按名称排序
      if (a.type !== b.type) {
        return a.type === 'dir' ? -1 : 1
      }
      return a.name.localeCompare(b.name, 'zh-CN')
    } else if (sortMode.value === 'time') {
      return (b.modify_time || 0) - (a.modify_time || 0)
    } else if (sortMode.value === 'size') {
      if (a.type !== b.type) {
        return a.type === 'dir' ? -1 : 1
      }
      return (b.size || 0) - (a.size || 0)
    }
    return 0
  })
  
  return result
})

// 排序图标
const sortIcon = computed(() => {
  const icons: Record<string, string> = {
    'name': 'mdi-sort-alphabetical-ascending',
    'time': 'mdi-sort-clock-ascending-outline',
    'size': 'mdi-sort-numeric-ascending'
  }
  return icons[sortMode.value] || 'mdi-sort'
})

// 获取存储名称
const getStorageName = (storage: string): string => {
  const option = storageOptions.find(s => s.value === storage)
  return option?.title || storage
}

// 获取存储图标
const getStorageIcon = (storage: string): string => {
  const icons: Record<string, string> = {
    'local': 'mdi-folder',
    '115': 'mdi-cloud',
    'rclone': 'mdi-desktop-classic',
    'openlist': 'mdi-desktop-classic'
  }
  return icons[storage] || 'mdi-folder'
}

// 加载文件列表
const loadFiles = async () => {
  loading.value = true
  try {
    const response = await api.get('/file-browser/list', {
      params: {
        storage: selectedStorage.value,
        path: currentPath.value,
        recursion: false,
        sort: sortMode.value
      }
    })
    
    files.value = response.data.items || []
    stats.value = {
      total: response.data.total || 0,
      dirs: response.data.dirs_count || 0,
      files: response.data.files_count || 0,
      mediaFiles: response.data.media_files_count || 0
    }
  } catch (error: any) {
    toast.error(error.message || '加载文件列表失败')
  } finally {
    loading.value = false
  }
}

// 加载存储使用情况
const loadStorageUsage = async () => {
  try {
    const response = await api.get('/file-browser/storage/usage', {
      params: {
        storage: selectedStorage.value
      }
    })
    storageUsage.value = response.data
  } catch (error) {
    // 静默失败
  }
}

// 刷新文件
const refreshFiles = () => {
  loadFiles()
  loadStorageUsage()
}

// 存储切换
const handleStorageChange = (storage?: string) => {
  if (storage) {
    selectedStorage.value = storage
  }
  currentPath.value = '/'
  pathStack.value = []
  selectedFiles.value = []
  refreshFiles()
}

// 导航到路径
const navigateToPath = () => {
  refreshFiles()
}

// 导航到上一级
const navigateUp = () => {
  if (currentPath.value === '/') return
  
  const parts = currentPath.value.split('/').filter(p => p)
  if (parts.length > 0) {
    parts.pop()
    const newPath = parts.length > 0 ? '/' + parts.join('/') : '/'
    navigateToPathItem({
      storage: selectedStorage.value,
      type: 'dir',
      path: newPath,
      name: parts.length > 0 ? parts[parts.length - 1] : '/'
    })
  }
}

// 导航到面包屑项
const navigateToBreadcrumb = (item: any) => {
  if (item.disabled) return
  navigateToPathItem({
    storage: selectedStorage.value,
    type: 'dir',
    path: item.path,
    name: item.title
  })
}

// 导航到路径项
const navigateToPathItem = (item: any) => {
  currentPath.value = item.path || '/'
  
  // 更新路径堆栈
  if (item.path === '/') {
    pathStack.value = []
  } else {
    const parts = item.path.split('/').filter(p => p)
    pathStack.value = []
    let path = ''
    parts.forEach((part: string) => {
      path += '/' + part
      pathStack.value.push({
        storage: selectedStorage.value,
        type: 'dir',
        path: path,
        name: part
      })
    })
  }
  
  refreshFiles()
}

// 切换排序
const toggleSort = () => {
  const modes: ('name' | 'time' | 'size')[] = ['name', 'time', 'size']
  const currentIndex = modes.indexOf(sortMode.value)
  sortMode.value = modes[(currentIndex + 1) % modes.length]
}

// 搜索
const handleSearch = () => {
  // 搜索功能已通过computed实现，这里可以添加其他逻辑
}

// 文件选择
const handleFileSelect = (fileIds: string[]) => {
  selectedFiles.value = fileIds
}

// 导航（点击目录）
const handleNavigate = (file: any) => {
  if (file.type === 'dir') {
    selectedFile.value = null
    navigateToPathItem(file)
  } else {
    // 点击文件时显示详情
    selectedFile.value = file
  }
}

// 判断是否为图片文件
const isImageFile = (file: any): boolean => {
  if (!file || file.type !== 'file') return false
  const imageExts = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg', '.ico']
  return imageExts.some(ext => file.name.toLowerCase().endsWith(ext))
}

// 获取图片URL
const getImageUrl = (file: any): string => {
  if (selectedStorage.value === 'local') {
    return `/api/file-browser/image?storage=${selectedStorage.value}&path=${encodeURIComponent(file.path)}`
  }
  return file.thumbnail || file.url || ''
}

// 获取文件图标
const getFileIcon = (extension: string | null): string => {
  if (!extension) return 'mdi-file-outline'
  // 这里可以复用FileList中的图标映射逻辑
  return 'mdi-file-outline'
}

// 判断当前是否为目录视图
const isDirectory = computed(() => {
  return currentPath.value !== '/' || files.value.some(f => f.type === 'dir')
})

// 文件操作
const handleFileAction = async (action: string, file: any) => {
  selectedFile.value = file
  currentOperation.value = action
  
  switch (action) {
    case 'recognize':
      await handleRecognize(file)
      break
    case 'scrape':
      await handleScrape(file)
      break
    case 'rename':
      showOperationDialog.value = true
      break
    case 'transfer':
      showOperationDialog.value = true
      break
    case 'download':
      await handleDownload(file)
      break
    case 'delete':
      await handleDelete(file)
      break
    default:
      showOperationDialog.value = true
  }
}

// 下载文件
const handleDownload = async (file: any) => {
  if (selectedStorage.value !== 'local') {
    toast.warning('目前只支持本地文件下载')
    return
  }
  
  try {
    const response = await api.post('/file-browser/download', {
      storage: selectedStorage.value,
      path: file.path,
      confirm: true
    }, {
      responseType: 'blob'
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', file.name)
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    
    toast.success('文件下载成功')
  } catch (error: any) {
    toast.error(error.message || '下载文件失败')
  }
}

// 识别文件
const handleRecognize = async (file: any) => {
  if (file.type !== 'file' || !file.is_media) {
    toast.warning('只能识别媒体文件')
    return
  }
  
  if (selectedStorage.value !== 'local') {
    toast.warning('目前只支持本地文件识别')
    return
  }
  
  showProgressDialog.value = true
  progressTitle.value = '识别媒体文件'
  progressText.value = `正在识别: ${file.name}`
  progressIndeterminate.value = true
  
  try {
    const response = await api.get('/file-browser/recognize', {
      params: {
        storage: selectedStorage.value,
        path: file.path
      }
    })
    
    mediaInfo.value = response.data
    showMediaInfoDialog.value = true
  } catch (error: any) {
    toast.error(error.message || '识别文件失败')
  } finally {
    showProgressDialog.value = false
  }
}

// 刮削文件
const handleScrape = async (file: any) => {
  if (file.type !== 'file' || !file.is_media) {
    toast.warning('只能刮削媒体文件')
    return
  }
  
  if (selectedStorage.value !== 'local') {
    toast.warning('目前只支持本地文件刮削')
    return
  }
  
  showProgressDialog.value = true
  progressTitle.value = '刮削媒体信息'
  progressText.value = `正在刮削: ${file.name}`
  progressIndeterminate.value = true
  
  try {
    await api.post('/file-browser/scrape', {
      storage: selectedStorage.value,
      path: file.path,
      overwrite: true
    })
    
    toast.success('刮削成功')
  } catch (error: any) {
    toast.error(error.message || '刮削失败')
  } finally {
    showProgressDialog.value = false
  }
}

// 删除文件
const handleDelete = async (file: any) => {
  if (!confirm(`确定要删除 "${file.name}" 吗？此操作不可恢复。`)) {
    return
  }
  
  try {
    await api.delete('/file-browser/delete', {
      data: {
        storage: selectedStorage.value,
        path: file.path,
        confirm: true
      }
    })
    
    toast.success('删除成功')
    refreshFiles()
  } catch (error: any) {
    toast.error(error.message || '删除失败')
  }
}

// 创建文件夹
const handleCreateFolder = async () => {
  if (!newFolderName.value.trim()) {
    toast.warning('请输入文件夹名称')
    return
  }
  
  try {
    await api.post('/file-browser/folder', {
      storage: selectedStorage.value,
      path: currentPath.value,
      name: newFolderName.value
    })
    
    toast.success('创建成功')
    showCreateFolderDialog.value = false
    newFolderName.value = ''
    refreshFiles()
  } catch (error: any) {
    toast.error(error.message || '创建失败')
  }
}

// 批量操作
const handleBatchRecognize = async () => {
  const mediaFiles = files.value.filter(f => 
    selectedFiles.value.includes(f.fileid) && f.type === 'file' && f.is_media
  )
  
  if (mediaFiles.length === 0) {
    toast.warning('请选择媒体文件')
    return
  }
  
  showProgressDialog.value = true
  progressTitle.value = '批量识别'
  progressIndeterminate.value = false
  
  let successCount = 0
  for (let i = 0; i < mediaFiles.length; i++) {
    const file = mediaFiles[i]
    progressText.value = `正在识别 ${i + 1}/${mediaFiles.length}: ${file.name}`
    progressValue.value = ((i + 1) / mediaFiles.length) * 100
    
    try {
      await handleRecognize(file)
      successCount++
    } catch (error) {
      // 继续处理下一个
    }
  }
  
  showProgressDialog.value = false
  toast.success(`批量识别完成: ${successCount}/${mediaFiles.length}`)
}

const handleBatchScrape = async () => {
  const mediaFiles = files.value.filter(f => 
    selectedFiles.value.includes(f.fileid) && f.type === 'file' && f.is_media
  )
  
  if (mediaFiles.length === 0) {
    toast.warning('请选择媒体文件')
    return
  }
  
  showProgressDialog.value = true
  progressTitle.value = '批量刮削'
  progressIndeterminate.value = false
  
  let successCount = 0
  for (let i = 0; i < mediaFiles.length; i++) {
    const file = mediaFiles[i]
    progressText.value = `正在刮削 ${i + 1}/${mediaFiles.length}: ${file.name}`
    progressValue.value = ((i + 1) / mediaFiles.length) * 100
    
    try {
      await handleScrape(file)
      successCount++
    } catch (error) {
      // 继续处理下一个
    }
  }
  
  showProgressDialog.value = false
  toast.success(`批量刮削完成: ${successCount}/${mediaFiles.length}`)
}

const handleBatchTransfer = () => {
  if (selectedFiles.value.length === 0) {
    toast.warning('请选择要整理的文件')
    return
  }
  
  showOperationDialog.value = true
  currentOperation.value = 'transfer'
}

const handleBatchDelete = async () => {
  if (selectedFiles.value.length === 0) {
    toast.warning('请选择要删除的文件')
    return
  }
  
  if (!confirm(`确定要删除选中的 ${selectedFiles.value.length} 个文件/目录吗？此操作不可恢复。`)) {
    return
  }
  
  showProgressDialog.value = true
  progressTitle.value = '批量删除'
  progressIndeterminate.value = false
  
  const selectedItems = files.value.filter(f => selectedFiles.value.includes(f.fileid))
  let successCount = 0
  
  for (let i = 0; i < selectedItems.length; i++) {
    const file = selectedItems[i]
    progressText.value = `正在删除 ${i + 1}/${selectedItems.length}: ${file.name}`
    progressValue.value = ((i + 1) / selectedItems.length) * 100
    
    try {
      await handleDelete(file)
      successCount++
    } catch (error) {
      // 继续处理下一个
    }
  }
  
  showProgressDialog.value = false
  selectedFiles.value = []
  toast.success(`批量删除完成: ${successCount}/${selectedItems.length}`)
  refreshFiles()
}

// 操作成功回调
const handleOperationSuccess = () => {
  showOperationDialog.value = false
  selectedFile.value = null
  currentOperation.value = null
  refreshFiles()
}

// 格式化字节
const formatBytes = (bytes: number): string => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i]
}

// 监听路径变化
watch(() => currentPath.value, () => {
  refreshFiles()
})

// 监听存储变化
watch(() => selectedStorage.value, () => {
  handleStorageChange()
})

// 监听显示模式变化（响应式）
watch(() => display.mdAndUp.value, (isDesktop) => {
  if (isDesktop) {
    showTree.value = true
  } else {
    showTree.value = false
  }
})

// 初始化
onMounted(() => {
  refreshFiles()
})
</script>

<style scoped>
.file-browser-page {
  padding: 24px;
}

.file-browser-layout {
  min-height: calc(100vh - 200px);
}

.file-navigator-col {
  border-right: 1px solid rgba(var(--v-border-color), 0.12);
}

.stat-card {
  height: 100%;
}

.stat-number {
  font-size: 24px;
  font-weight: bold;
  margin: 8px 0;
}

.stat-label {
  font-size: 14px;
  color: rgba(0, 0, 0, 0.6);
}
</style>

