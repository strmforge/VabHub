<template>
  <div class="directory-config-page">
    <PageHeader
      title="目录配置"
      subtitle="管理文件整理目录配置"
    >
      <template v-slot:actions>
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          @click="openCreateDialog"
        >
          创建目录配置
        </v-btn>
      </template>
    </PageHeader>

    <!-- 过滤和搜索 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-text>
        <v-row>
          <v-col cols="12" md="4">
            <v-select
              v-model="filters.monitor_type"
              :items="monitorTypeOptions"
              label="监控类型"
              clearable
              variant="outlined"
              density="compact"
              prepend-inner-icon="mdi-monitor"
              @update:model-value="loadDirectories"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-select
              v-model="filters.enabled"
              :items="enabledOptions"
              label="启用状态"
              clearable
              variant="outlined"
              density="compact"
              prepend-inner-icon="mdi-toggle-switch"
              @update:model-value="loadDirectories"
            />
          </v-col>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="searchQuery"
              label="搜索"
              variant="outlined"
              density="compact"
              prepend-inner-icon="mdi-magnify"
              clearable
              @update:model-value="handleSearch"
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 目录配置列表 -->
    <div v-if="loading" class="text-center py-12">
      <v-progress-circular indeterminate color="primary" size="64" />
      <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
    </div>

    <div v-else-if="filteredDirectories.length === 0" class="text-center py-12">
      <v-icon size="80" color="grey-darken-1" class="mb-4">mdi-folder-off</v-icon>
      <div class="text-h5 font-weight-medium mb-2">暂无目录配置</div>
      <div class="text-body-2 text-medium-emphasis">
        使用"创建目录配置"按钮添加您的第一个目录配置
      </div>
    </div>

    <v-row v-else>
      <v-col
        v-for="directory in filteredDirectories"
        :key="directory.id"
        cols="12"
        md="6"
        lg="4"
      >
        <DirectoryConfigCard
          :directory="directory"
          @edit="editDirectory"
          @delete="deleteDirectory"
          @toggle-enabled="toggleEnabled"
        />
      </v-col>
    </v-row>

    <!-- 创建/编辑对话框 -->
    <DirectoryConfigDialog
      v-model="showDialog"
      :directory="editingDirectory"
      @saved="handleSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/common/PageHeader.vue'
import DirectoryConfigCard from '@/components/directory/DirectoryConfigCard.vue'
import DirectoryConfigDialog from '@/components/directory/DirectoryConfigDialog.vue'

const toast = useToast()

// 状态
const loading = ref(false)
const directories = ref<any[]>([])
const showDialog = ref(false)
const editingDirectory = ref<any>(null)
const searchQuery = ref('')

// 过滤
const filters = ref({
  monitor_type: null as string | null,
  enabled: null as boolean | null
})

// 选项
const monitorTypeOptions = [
  { title: '下载器监控', value: 'downloader' },
  { title: '目录监控', value: 'directory' },
  { title: '不监控', value: null }
]

const enabledOptions = [
  { title: '启用', value: true },
  { title: '禁用', value: false }
]

// 计算属性
const filteredDirectories = computed(() => {
  let result = directories.value

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(dir => 
      dir.download_path?.toLowerCase().includes(query) ||
      dir.library_path?.toLowerCase().includes(query) ||
      dir.media_type?.toLowerCase().includes(query) ||
      dir.media_category?.toLowerCase().includes(query)
    )
  }

  return result
})

// 方法
const loadDirectories = async () => {
  try {
    loading.value = true
    const params: any = {}
    if (filters.value.monitor_type !== null) {
      params.monitor_type = filters.value.monitor_type
    }
    if (filters.value.enabled !== null) {
      params.enabled = filters.value.enabled
    }
    
    const response = await api.get('/directories', { params })
    if (response.data.success) {
      directories.value = response.data.data || []
    } else {
      toast.error(response.data.error_message || '加载目录配置失败')
    }
  } catch (error: any) {
    toast.error(error.response?.data?.error_message || '加载目录配置失败')
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  editingDirectory.value = null
  showDialog.value = true
}

const editDirectory = (directory: any) => {
  editingDirectory.value = directory
  showDialog.value = true
}

const deleteDirectory = async (directory: any) => {
  if (!confirm(`确定要删除目录配置 "${directory.download_path}" 吗？`)) {
    return
  }

  try {
    const response = await api.delete(`/directories/${directory.id}`)
    if (response.data.success) {
      toast.success('删除成功')
      loadDirectories()
    } else {
      toast.error(response.data.error_message || '删除失败')
    }
  } catch (error: any) {
    toast.error(error.response?.data?.error_message || '删除失败')
  }
}

const toggleEnabled = async (directory: any) => {
  try {
    const response = await api.put(`/directories/${directory.id}`, {
      ...directory,
      enabled: !directory.enabled
    })
    if (response.data.success) {
      toast.success(directory.enabled ? '已禁用' : '已启用')
      loadDirectories()
    } else {
      toast.error(response.data.error_message || '操作失败')
    }
  } catch (error: any) {
    toast.error(error.response?.data?.error_message || '操作失败')
  }
}

const handleSaved = () => {
  showDialog.value = false
  editingDirectory.value = null
  loadDirectories()
}

const handleSearch = () => {
  // 搜索已通过计算属性实现
}

// 生命周期
onMounted(() => {
  loadDirectories()
})
</script>

<style scoped>
.directory-config-page {
  padding: 24px;
}
</style>

