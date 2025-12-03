<template>
  <v-container fluid>
    <!-- 页面标题 -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center mb-4">
          <v-icon size="32" color="primary" class="mr-3">mdi-server</v-icon>
          <h1 class="text-h4">媒体服务器管理</h1>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            @click="openCreateDialog"
          >
            添加媒体服务器
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- 服务器列表 -->
    <v-row>
      <v-col
        v-for="server in servers"
        :key="server.id"
        cols="12"
        md="6"
        lg="4"
      >
        <MediaServerCard
          :server="server"
          @refresh="loadServers"
          @edit="openEditDialog"
          @delete="handleDelete"
          @check="handleCheckConnection"
          @sync="handleSync"
          @view-details="viewServerDetails"
        />
      </v-col>
    </v-row>

    <!-- 空状态 -->
    <v-alert
      v-if="!loading && servers.length === 0"
      type="info"
      variant="tonal"
      class="mt-4"
    >
      还没有配置媒体服务器，点击"添加媒体服务器"按钮开始配置。
    </v-alert>

    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-8">
      <v-progress-circular indeterminate color="primary"></v-progress-circular>
      <div class="mt-4 text-body-2 text-medium-emphasis">加载中...</div>
    </div>

    <!-- 创建/编辑对话框 -->
    <MediaServerDialog
      v-model="dialogVisible"
      :server="selectedServer"
      @saved="handleSaved"
    />

    <!-- 服务器详情对话框 -->
    <MediaServerDetailDialog
      v-model="detailDialogVisible"
      :server-id="selectedServerId"
      @refresh="loadServers"
    />
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { mediaServerApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import MediaServerCard from '@/components/media-server/MediaServerCard.vue'
import MediaServerDialog from '@/components/media-server/MediaServerDialog.vue'
import MediaServerDetailDialog from '@/components/media-server/MediaServerDetailDialog.vue'

const { showToast } = useToast()

const servers = ref<any[]>([])
const loading = ref(false)
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const selectedServer = ref<any>(null)
const selectedServerId = ref<number | null>(null)

// 加载服务器列表
const loadServers = async () => {
  try {
    loading.value = true
    const response = await mediaServerApi.getMediaServers()
    servers.value = response.data || []
  } catch (error: any) {
    console.error('加载媒体服务器列表失败:', error)
    showToast('加载媒体服务器列表失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    loading.value = false
  }
}

// 打开创建对话框
const openCreateDialog = () => {
  selectedServer.value = null
  dialogVisible.value = true
}

// 打开编辑对话框
const openEditDialog = (server: any) => {
  selectedServer.value = server
  dialogVisible.value = true
}

// 处理保存
const handleSaved = () => {
  dialogVisible.value = false
  selectedServer.value = null
  loadServers()
}

// 处理删除
const handleDelete = async (id: number) => {
  if (!confirm('确定要删除这个媒体服务器吗？')) {
    return
  }

  try {
    await mediaServerApi.deleteMediaServer(id)
    showToast('删除成功', 'success')
    loadServers()
  } catch (error: any) {
    showToast('删除失败: ' + (error.message || '未知错误'), 'error')
  }
}

// 检查连接
const handleCheckConnection = async (id: number) => {
  try {
    await mediaServerApi.checkConnection(id)
    showToast('连接检查成功', 'success')
    loadServers()
  } catch (error: any) {
    showToast('连接检查失败: ' + (error.message || '未知错误'), 'error')
  }
}

// 同步
const handleSync = async (id: number, type: 'libraries' | 'metadata') => {
  try {
    if (type === 'libraries') {
      await mediaServerApi.syncLibraries(id)
      showToast('媒体库同步已启动', 'success')
    } else {
      await mediaServerApi.syncMetadata(id)
      showToast('元数据同步已启动', 'success')
    }
    loadServers()
  } catch (error: any) {
    showToast('同步失败: ' + (error.message || '未知错误'), 'error')
  }
}

// 查看详情
const viewServerDetails = (id: number) => {
  selectedServerId.value = id
  detailDialogVisible.value = true
}

onMounted(() => {
  loadServers()
})
</script>

<script lang="ts">
export default {
  name: 'MediaServers'
}
</script>

<style scoped>
.v-card {
  border-radius: 12px;
}
</style>

