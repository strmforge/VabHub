<template>
  <v-container fluid>
    <!-- 页面标题 -->
    <v-row>
      <v-col cols="12">
        <div class="d-flex align-center mb-4">
          <v-icon size="32" color="primary" class="mr-3">mdi-harddisk</v-icon>
          <h1 class="text-h4">存储监控</h1>
          <v-spacer></v-spacer>
          <v-btn
            color="primary"
            prepend-icon="mdi-plus"
            @click="openCreateDialog"
          >
            添加存储目录
          </v-btn>
        </div>
      </v-col>
    </v-row>

    <!-- 统计卡片 -->
    <v-row v-if="statistics">
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon size="40" color="primary" class="mr-3">mdi-folder-multiple</v-icon>
              <div>
                <div class="text-caption text-medium-emphasis">总目录数</div>
                <div class="text-h5">{{ statistics.total_directories }}</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon size="40" color="success" class="mr-3">mdi-check-circle</v-icon>
              <div>
                <div class="text-caption text-medium-emphasis">启用目录</div>
                <div class="text-h5">{{ statistics.enabled_directories }}</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon size="40" color="warning" class="mr-3">mdi-alert</v-icon>
              <div>
                <div class="text-caption text-medium-emphasis">未解决预警</div>
                <div class="text-h5">{{ statistics.unresolved_alerts }}</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" sm="6" md="3">
        <v-card>
          <v-card-text>
            <div class="d-flex align-center">
              <v-icon size="40" color="info" class="mr-3">mdi-chart-pie</v-icon>
              <div>
                <div class="text-caption text-medium-emphasis">总使用率</div>
                <div class="text-h5">{{ statistics.total_usage_percent.toFixed(1) }}%</div>
              </div>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 标签页 -->
    <v-row>
      <v-col cols="12">
        <v-card>
          <v-tabs v-model="activeTab" bg-color="surface">
            <v-tab value="directories">
              <v-icon start>mdi-folder-multiple</v-icon>
              存储目录
            </v-tab>
            <v-tab value="usage">
              <v-icon start>mdi-chart-line</v-icon>
              使用情况
            </v-tab>
            <v-tab value="trends">
              <v-icon start>mdi-chart-timeline-variant</v-icon>
              使用趋势
            </v-tab>
            <v-tab value="alerts">
              <v-icon start>mdi-alert</v-icon>
              预警列表
              <v-badge
                v-if="statistics && statistics.unresolved_alerts > 0"
                :content="statistics.unresolved_alerts"
                color="error"
                inline
                class="ml-2"
              />
            </v-tab>
          </v-tabs>

          <v-card-text>
            <!-- 存储目录标签页 -->
            <v-window v-model="activeTab">
              <v-window-item value="directories">
                <StorageDirectoriesTab
                  :directories="directories"
                  :loading="loading"
                  @refresh="loadData"
                  @edit="openEditDialog"
                  @delete="handleDelete"
                />
              </v-window-item>

              <!-- 使用情况标签页 -->
              <v-window-item value="usage">
                <StorageUsageTab
                  :usage-list="usageList"
                  :loading="loading"
                  @refresh="loadUsage"
                />
              </v-window-item>

              <!-- 使用趋势标签页 -->
              <v-window-item value="trends">
                <StorageTrendsTab
                  :directories="directories"
                  :loading="loading"
                  @refresh="loadData"
                />
              </v-window-item>

              <!-- 预警列表标签页 -->
              <v-window-item value="alerts">
                <StorageAlertsTab
                  :alerts="alerts"
                  :loading="loading"
                  @refresh="loadAlerts"
                  @resolve="handleResolveAlert"
                />
              </v-window-item>
            </v-window>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- 创建/编辑对话框 -->
    <StorageDirectoryDialog
      v-model="dialogVisible"
      :directory="selectedDirectory"
      @saved="handleSaved"
    />
  </v-container>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { storageMonitorApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import StorageDirectoriesTab from '@/components/storage-monitor/StorageDirectoriesTab.vue'
import StorageUsageTab from '@/components/storage-monitor/StorageUsageTab.vue'
import StorageTrendsTab from '@/components/storage-monitor/StorageTrendsTab.vue'
import StorageAlertsTab from '@/components/storage-monitor/StorageAlertsTab.vue'
import StorageDirectoryDialog from '@/components/storage-monitor/StorageDirectoryDialog.vue'

const { showToast } = useToast()

const activeTab = ref('directories')
const directories = ref<any[]>([])
const usageList = ref<any[]>([])
const alerts = ref<any[]>([])
const statistics = ref<any>(null)
const loading = ref(false)
const dialogVisible = ref(false)
const selectedDirectory = ref<any>(null)

// 加载数据
const loadData = async () => {
  try {
    loading.value = true
    await Promise.all([
      loadDirectories(),
      loadStatistics()
    ])
  } catch (error: any) {
    showToast('加载数据失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    loading.value = false
  }
}

// 加载存储目录列表
const loadDirectories = async () => {
  try {
    const response = await storageMonitorApi.getDirectories()
    directories.value = response.data || []
  } catch (error: any) {
    console.error('加载存储目录列表失败:', error)
    showToast('加载存储目录列表失败: ' + (error.message || '未知错误'), 'error')
  }
}

// 加载使用情况
const loadUsage = async () => {
  try {
    loading.value = true
    const response = await storageMonitorApi.getAllDirectoriesUsage()
    usageList.value = response.data || []
  } catch (error: any) {
    console.error('加载使用情况失败:', error)
    showToast('加载使用情况失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    loading.value = false
  }
}

// 加载预警列表
const loadAlerts = async () => {
  try {
    loading.value = true
    const response = await storageMonitorApi.getAlerts({ resolved: false })
    alerts.value = response.data || []
  } catch (error: any) {
    console.error('加载预警列表失败:', error)
    showToast('加载预警列表失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    loading.value = false
  }
}

// 加载统计信息
const loadStatistics = async () => {
  try {
    const response = await storageMonitorApi.getStatistics()
    statistics.value = response.data
  } catch (error: any) {
    console.error('加载统计信息失败:', error)
  }
}

// 打开创建对话框
const openCreateDialog = () => {
  selectedDirectory.value = null
  dialogVisible.value = true
}

// 打开编辑对话框
const openEditDialog = (directory: any) => {
  selectedDirectory.value = directory
  dialogVisible.value = true
}

// 处理保存
const handleSaved = () => {
  dialogVisible.value = false
  selectedDirectory.value = null
  loadData()
  if (activeTab.value === 'usage') {
    loadUsage()
  }
}

// 处理删除
const handleDelete = async (id: number) => {
  if (!confirm('确定要删除这个存储目录吗？')) {
    return
  }
  
  try {
    await storageMonitorApi.deleteDirectory(id)
    showToast('删除成功', 'success')
    loadData()
  } catch (error: any) {
    showToast('删除失败: ' + (error.message || '未知错误'), 'error')
  }
}

// 处理解决预警
const handleResolveAlert = async (id: number) => {
  try {
    await storageMonitorApi.resolveAlert(id)
    showToast('预警已解决', 'success')
    loadAlerts()
    loadStatistics()
  } catch (error: any) {
    showToast('解决预警失败: ' + (error.message || '未知错误'), 'error')
  }
}

// 监听标签页切换
const handleTabChange = () => {
  if (activeTab.value === 'usage') {
    loadUsage()
  } else if (activeTab.value === 'alerts') {
    loadAlerts()
  }
}

// 监听activeTab变化
watch(activeTab, handleTabChange)

onMounted(() => {
  loadData()
  // 如果默认标签页是使用情况，加载使用情况
  if (activeTab.value === 'usage') {
    loadUsage()
  } else if (activeTab.value === 'alerts') {
    loadAlerts()
  }
})
</script>

<script lang="ts">
export default {
  name: 'StorageMonitor'
}
</script>

<style scoped>
.v-card {
  border-radius: 12px;
}
</style>

