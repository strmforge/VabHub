<template>
  <div class="multimodal-monitoring-page">
    <PageHeader
      title="多模态分析性能监控"
      subtitle="实时性能指标、告警和优化管理"
    >
      <template v-slot:actions>
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

    <!-- 标签页 -->
    <v-tabs v-model="activeTab" class="mb-4">
      <v-tab value="metrics">性能指标</v-tab>
      <v-tab value="alerts">告警管理</v-tab>
      <v-tab value="optimization">优化管理</v-tab>
      <v-tab value="history">历史数据</v-tab>
    </v-tabs>

    <v-window v-model="activeTab">
      <!-- 性能指标标签页 -->
      <v-window-item value="metrics">
        <PerformanceMetricsTab
          :loading="loading"
          :metrics="metrics"
          :summary="summary"
          :cache-stats="cacheStats"
          @refresh="refreshMetrics"
        />
      </v-window-item>

      <!-- 告警管理标签页 -->
      <v-window-item value="alerts">
        <AlertsManagementTab
          :loading="alertsLoading"
          :alerts="alerts"
          @refresh="refreshAlerts"
          @resolve="handleResolveAlert"
          @check="handleCheckAlerts"
        />
      </v-window-item>

      <!-- 优化管理标签页 -->
      <v-window-item value="optimization">
        <OptimizationManagementTab
          :loading="optimizationLoading"
          :config="optimizationConfig"
          :history="optimizationHistory"
          @refresh="refreshOptimization"
          @optimize="handleOptimize"
          @update-config="handleUpdateConfig"
        />
      </v-window-item>

      <!-- 历史数据标签页 -->
      <v-window-item value="history">
        <HistoryDataTab
          :loading="historyLoading"
          :statistics="historyStatistics"
          @refresh="refreshHistory"
          @cleanup="handleCleanupHistory"
        />
      </v-window-item>
    </v-window>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useToast } from 'vue-toastification'
import PageHeader from '@/components/common/PageHeader.vue'
import PerformanceMetricsTab from '@/components/multimodal/PerformanceMetricsTab.vue'
import AlertsManagementTab from '@/components/multimodal/AlertsManagementTab.vue'
import OptimizationManagementTab from '@/components/multimodal/OptimizationManagementTab.vue'
import HistoryDataTab from '@/components/multimodal/HistoryDataTab.vue'
import {
  getPerformanceSummary,
  getCacheStats,
  getAlerts,
  checkAlerts,
  resolveAlert,
  getOptimizationConfig,
  getOptimizationHistory,
  getHistoryStatistics,
  cleanupHistory,
  optimizeAll,
  updateOptimizationConfig
} from '@/services/multimodalMetrics'

const toast = useToast()

// 状态
const activeTab = ref('metrics')
const loading = ref(false)
const alertsLoading = ref(false)
const optimizationLoading = ref(false)
const historyLoading = ref(false)

const metrics = ref<any>(null)
const summary = ref<any>(null)
const cacheStats = ref<any>(null)
const alerts = ref<any[]>([])
const optimizationConfig = ref<any>(null)
const optimizationHistory = ref<any[]>([])
const historyStatistics = ref<any>(null)

// 刷新性能指标
const refreshMetrics = async () => {
  loading.value = true
  try {
    const [summaryRes, cacheStatsRes] = await Promise.all([
      getPerformanceSummary(),
      getCacheStats()
    ])
    summary.value = summaryRes.data
    cacheStats.value = cacheStatsRes.data
    metrics.value = summaryRes.data?.operations || {}
  } catch (error: any) {
    toast.error(`获取性能指标失败: ${error.message}`)
  } finally {
    loading.value = false
  }
}

// 刷新告警
const refreshAlerts = async () => {
  alertsLoading.value = true
  try {
    const response = await getAlerts({ limit: 100 })
    alerts.value = response.data || []
  } catch (error: any) {
    toast.error(`获取告警列表失败: ${error.message}`)
  } finally {
    alertsLoading.value = false
  }
}

// 刷新优化
const refreshOptimization = async () => {
  optimizationLoading.value = true
  try {
    const [configRes, historyRes] = await Promise.all([
      getOptimizationConfig(),
      getOptimizationHistory({ limit: 100 })
    ])
    optimizationConfig.value = configRes.data
    optimizationHistory.value = historyRes.data || []
  } catch (error: any) {
    toast.error(`获取优化信息失败: ${error.message}`)
  } finally {
    optimizationLoading.value = false
  }
}

// 刷新历史数据
const refreshHistory = async () => {
  historyLoading.value = true
  try {
    const response = await getHistoryStatistics({})
    historyStatistics.value = response.data || {}
  } catch (error: any) {
    toast.error(`获取历史数据失败: ${error.message}`)
  } finally {
    historyLoading.value = false
  }
}

// 刷新所有数据
const refreshData = async () => {
  await refreshMetrics()
  if (activeTab.value === 'alerts') {
    await refreshAlerts()
  } else if (activeTab.value === 'optimization') {
    await refreshOptimization()
  } else if (activeTab.value === 'history') {
    await refreshHistory()
  }
}

// 解决告警
const handleResolveAlert = async (alertId: number) => {
  try {
    await resolveAlert(alertId, 'user')
    toast.success('告警已解决')
    await refreshAlerts()
  } catch (error: any) {
    toast.error(`解决告警失败: ${error.message}`)
  }
}

// 检查告警
const handleCheckAlerts = async (operation?: string) => {
  try {
    const response = await checkAlerts({ operation, time_window: 300 })
    const newAlerts = response.data || []
    if (newAlerts.length > 0) {
      toast.warning(`发现${newAlerts.length}个新告警`)
    } else {
      toast.success('未发现新告警')
    }
    await refreshAlerts()
  } catch (error: any) {
    toast.error(`检查告警失败: ${error.message}`)
  }
}

// 执行优化
const handleOptimize = async (type: 'all' | 'cache-ttl' | 'concurrency', operation?: string) => {
  try {
    if (type === 'all') {
      await optimizeAll()
    }
    toast.success('优化完成')
    await refreshOptimization()
    await refreshMetrics()
  } catch (error: any) {
    toast.error(`优化失败: ${error.message}`)
  }
}

// 更新配置
const handleUpdateConfig = async (config: any) => {
  try {
    await updateOptimizationConfig(config)
    toast.success('配置已更新')
    await refreshOptimization()
  } catch (error: any) {
    toast.error(`更新配置失败: ${error.message}`)
  }
}

// 清理历史数据
const handleCleanupHistory = async (days: number) => {
  try {
    const response = await cleanupHistory(days)
    const cleanedCount = response.data?.cleaned_count || 0
    toast.success(`清理了${cleanedCount}条历史数据`)
    await refreshHistory()
  } catch (error: any) {
    toast.error(`清理历史数据失败: ${error.message}`)
  }
}

// 监听标签页切换
watch(activeTab, (newTab) => {
  if (newTab === 'alerts' && alerts.value.length === 0) {
    refreshAlerts()
  } else if (newTab === 'optimization' && !optimizationConfig.value) {
    refreshOptimization()
  } else if (newTab === 'history' && !historyStatistics.value) {
    refreshHistory()
  }
})

// 初始化
onMounted(() => {
  refreshMetrics()
})
</script>

<style scoped>
.multimodal-monitoring-page {
  padding: 24px;
}
</style>

