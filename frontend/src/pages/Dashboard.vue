<template>
  <div class="dashboard-page">
    <!-- 页面头部 -->
    <PageHeader
      title="仪表盘"
      subtitle="系统概览和关键指标"
    >
      <template v-slot:actions>
        <v-btn
          v-if="!editMode"
          color="primary"
          prepend-icon="mdi-pencil"
          @click="enterEditMode"
        >
          编辑布局
        </v-btn>
        <v-btn
          color="primary"
          prepend-icon="mdi-refresh"
          @click="refreshData"
          :loading="loading"
        >
          刷新
        </v-btn>
      </template>
    </PageHeader>

    <!-- 可拖拽仪表盘布局 -->
    <DraggableDashboard
      v-if="useDraggableLayout"
      :edit-mode="editMode"
      :layout-id="currentLayoutId"
      @layout-saved="onLayoutSaved"
      @edit-mode-changed="onEditModeChanged"
    />

    <!-- 传统固定布局（备用） -->
    <div v-else>
      <!-- 关键指标卡片 -->
      <v-row class="mb-4">
        <v-col cols="12" sm="6" md="3">
          <StatCard
            title="媒体资源"
            :value="computedStats.media.total"
            icon="mdi-movie"
            color="primary"
          />
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <StatCard
            title="活跃下载"
            :value="computedStats.downloads.active"
            icon="mdi-download"
            color="success"
            :subtitle="`总速度: ${formatSpeed(computedStats.downloads.totalSpeed)}`"
          />
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <StatCard
            title="存储使用"
            :value="`${computedStats.storage.used.toFixed(1)}%`"
            icon="mdi-harddisk"
            color="warning"
            :progress="computedStats.storage.used"
          />
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <StatCard
            title="系统负载"
            :value="`${computedStats.system.cpu.toFixed(1)}%`"
            icon="mdi-chip"
            color="info"
            :subtitle="`内存: ${computedStats.system.memory.toFixed(1)}%`"
          />
        </v-col>
      </v-row>

      <!-- 图表区域 -->
      <v-row>
        <!-- 下载速度图表 -->
        <v-col cols="12" md="8">
          <v-card>
            <v-card-title>下载速度趋势</v-card-title>
            <v-card-text>
              <DownloadSpeedChart :data="downloadSpeedData" />
            </v-card-text>
          </v-card>
        </v-col>
        
        <!-- 系统资源监控 -->
        <v-col cols="12" md="4">
          <v-card>
            <v-card-title>系统资源</v-card-title>
            <v-card-text>
              <SystemResourceMonitor 
                :stats="dashboardData?.system_stats || { cpu: 0, memory: 0, disk: 0 }" 
              />
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- 快速操作和最近活动 -->
      <v-row class="mt-4">
        <v-col cols="12" md="6">
          <QuickActionsPanel />
        </v-col>
        <v-col cols="12" md="6">
          <RecentActivityTimeline />
        </v-col>
      </v-row>
    </div>

    <!-- VabHub特色功能展示 -->
    <v-row class="mt-4">
      <v-col cols="12">
        <v-card>
          <v-card-title>
            <v-icon class="mr-2">mdi-star</v-icon>
            VabHub 特色功能
          </v-card-title>
          <v-card-text>
            <v-row>
              <v-col cols="12" sm="6" md="3">
                <FeatureCard
                  icon="mdi-music"
                  title="音乐管理"
                  description="多平台音乐订阅和管理"
                  color="purple"
                  :to="{ name: 'MusicSubscriptions' }"
                />
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <FeatureCard
                  icon="mdi-lightbulb-on"
                  title="AI推荐"
                  description="智能个性化推荐"
                  color="orange"
                  :to="{ name: 'Recommendations' }"
                />
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <FeatureCard
                  icon="mdi-shield-alert"
                  title="HNR检测"
                  description="智能做种风险管理"
                  color="red"
                  :to="{ name: 'HNRMonitoring' }"
                />
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <FeatureCard
                  icon="mdi-robot"
                  title="智能助手"
                  description="自然语言交互"
                  color="blue"
                  :to="{ name: 'Assistant' }"
                />
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useDashboardStore } from '@/stores/dashboard'
import { useWebSocket } from '@/composables/useWebSocket'
import PageHeader from '@/components/common/PageHeader.vue'
import StatCard from '@/components/common/StatCard.vue'
import DownloadSpeedChart from '@/components/dashboard/DownloadSpeedChart.vue'
import SystemResourceMonitor from '@/components/dashboard/SystemResourceMonitor.vue'
import QuickActionsPanel from '@/components/dashboard/QuickActionsPanel.vue'
import RecentActivityTimeline from '@/components/dashboard/RecentActivityTimeline.vue'
import FeatureCard from '@/components/common/FeatureCard.vue'
import DraggableDashboard from '@/components/dashboard/DraggableDashboard.vue'

// 临时使用ApexCharts（需要安装vue3-apexcharts）
// import VueApexCharts from 'vue3-apexcharts'

const dashboardStore = useDashboardStore()
const loading = computed(() => dashboardStore.loading)
const dashboardData = computed(() => dashboardStore.dashboardData)
const stats = computed(() => dashboardStore.stats)
const downloadSpeedData = ref([])

// 拖拽布局相关
const useDraggableLayout = ref(true) // 默认使用拖拽布局
const editMode = ref(false)
const currentLayoutId = ref<number | undefined>(undefined)

const refreshData = async () => {
  try {
    await dashboardStore.fetchDashboardData()
  } catch (error) {
    console.error('Failed to fetch dashboard data:', error)
  }
}

// WebSocket实时更新
const { isConnected, subscribe } = useWebSocket({
  topics: ['dashboard', 'system'],
  onMessage: (message) => {
    if (message.type === 'dashboard_update') {
      console.log('[Dashboard] 收到仪表盘实时更新:', message.data)
      dashboardStore.updateDashboardData(message.data)
    } else if (message.type === 'system_update') {
      console.log('[Dashboard] 收到系统资源实时更新:', message.data)
      // 更新系统统计
      if (message.data) {
        dashboardStore.updateSystemStats(message.data)
      }
    }
  },
  onConnect: () => {
    console.log('[Dashboard] WebSocket已连接')
  },
  onDisconnect: () => {
    console.log('[Dashboard] WebSocket已断开')
  },
  onError: (error) => {
    console.error('[Dashboard] WebSocket错误:', error)
  }
})

const formatSpeed = (bytes: number) => {
  if (!bytes || bytes === 0) return '0 B/s'
  if (bytes < 1024) return `${bytes} B/s`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(2)} KB/s`
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB/s`
}

// 计算统计数据
const computedStats = computed(() => {
  if (!dashboardData.value) {
    return {
      media: { total: 0 },
      downloads: { active: 0, totalSpeed: 0 },
      storage: { used: 0 },
      system: { cpu: 0, memory: 0, disk: 0 }
    }
  }
  
  const sys = dashboardData.value.system_stats
  const media = dashboardData.value.media_stats
  const download = dashboardData.value.download_stats
  
  return {
    media: {
      total: (media?.total_movies || 0) + (media?.total_tv_shows || 0) + (media?.total_anime || 0)
    },
    downloads: {
      active: download?.active || 0,
      totalSpeed: (download?.total_speed_mbps || 0) * 1024 * 1024 // 转换为字节/秒
    },
    storage: {
      used: sys?.disk_usage || 0
    },
    system: {
      cpu: sys?.cpu_usage || 0,
      memory: sys?.memory_usage || 0,
      disk: sys?.disk_usage || 0
    }
  }
})

// 进入编辑模式
const enterEditMode = () => {
  editMode.value = true
}

// 编辑模式变化
const onEditModeChanged = (mode: boolean) => {
  editMode.value = mode
}

// 布局保存
const onLayoutSaved = (layoutId: number) => {
  currentLayoutId.value = layoutId
}

onMounted(() => {
  refreshData()
  // 每30秒自动刷新
  const interval = setInterval(() => {
    refreshData()
  }, 30000)
  
  onUnmounted(() => {
    clearInterval(interval)
  })
})
</script>

<style lang="scss" scoped>
.dashboard-page {
  min-height: 100vh;
}
</style>

