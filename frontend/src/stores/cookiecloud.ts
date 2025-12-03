/**
 * CookieCloud 状态管理
 * 使用 Pinia 管理 CookieCloud 配置、同步状态等
 */

import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'
import CookieCloudApi from '@/api/cookiecloud'
import type {
  CookieCloudSettings,
  CookieCloudSettingsUpdate,
  CookieCloudSyncResult,
  CookieCloudTestResult,
  CookieCloudStatus,
  CookieCloudSyncHistory,
  CookieCloudSyncStatus
} from '@/types/cookiecloud'

export const useCookieCloudStore = defineStore('cookiecloud', () => {
  // === 状态定义 ===
  
  // CookieCloud设置
  const settings = ref<CookieCloudSettings | null>(null)
  const settingsLoading = ref(false)
  const settingsError = ref<string | null>(null)
  
  // 同步状态
  const syncResult = ref<CookieCloudSyncResult | null>(null)
  const syncLoading = ref(false)
  const syncError = ref<string | null>(null)
  
  // 连接测试
  const testResult = ref<CookieCloudTestResult | null>(null)
  const testLoading = ref(false)
  const testError = ref<string | null>(null)
  
  // 状态概览
  const status = ref<CookieCloudStatus | null>(null)
  const statusLoading = ref(false)
  const statusError = ref<string | null>(null)
  
  // 同步历史
  const syncHistory = ref<CookieCloudSyncHistory[]>([])
  const historyLoading = ref(false)
  const historyError = ref<string | null>(null)
  
  // 编辑中的设置（用于表单）
  const editingSettings = reactive<CookieCloudSettingsUpdate>({
    enabled: false,
    host: '',
    uuid: '',
    password: '',
    sync_interval_minutes: 60,
    safe_host_whitelist: []
  })

  // === 计算属性 ===
  
  // 是否已配置
  const isConfigured = computed(() => {
    return settings.value?.enabled && 
           settings.value?.host && 
           settings.value?.uuid && 
           settings.value?.password
  })

  // 上次同步状态
  const lastSyncStatus = computed((): CookieCloudSyncStatus => {
    if (!settings.value?.last_status) return 'NEVER'
    return settings.value.last_status as CookieCloudSyncStatus
  })

  // 是否正在同步
  const isSyncing = computed(() => syncLoading.value)

  // 同步状态文本
  const syncStatusText = computed(() => {
    const status = lastSyncStatus.value
    switch (status) {
      case 'SUCCESS': return '同步成功'
      case 'ERROR': return '同步失败'
      case 'PARTIAL': return '部分成功'
      case 'RUNNING': return '正在同步'
      case 'NEVER': return '从未同步'
      default: return '未知状态'
    }
  })

  // 同步状态颜色
  const syncStatusColor = computed(() => {
    const status = lastSyncStatus.value
    switch (status) {
      case 'SUCCESS': return 'success'
      case 'ERROR': return 'error'
      case 'PARTIAL': return 'warning'
      case 'RUNNING': return 'info'
      case 'NEVER': return 'grey'
      default: return 'grey'
    }
  })

  // === 方法 ===
  
  // 获取CookieCloud设置
  const fetchSettings = async () => {
    try {
      settingsLoading.value = true
      settingsError.value = null
      
      const data = await CookieCloudApi.getSettings()
      settings.value = data
      
      // 更新编辑中的设置
      Object.assign(editingSettings, {
        enabled: data.enabled,
        host: data.host || '',
        uuid: data.uuid || '',
        password: data.password ? '***' : '',
        sync_interval_minutes: data.sync_interval_minutes,
        safe_host_whitelist: data.safe_host_whitelist || []
      })
      
    } catch (error: any) {
      console.error('获取CookieCloud设置失败:', error)
      settingsError.value = error.response?.data?.message || error.message || '获取设置失败'
      throw error
    } finally {
      settingsLoading.value = false
    }
  }

  // 更新CookieCloud设置
  const updateSettings = async () => {
    try {
      settingsLoading.value = true
      settingsError.value = null
      
      // 验证设置
      const isValid = await CookieCloudApi.validateSettings(editingSettings)
      if (!isValid) {
        throw new Error('设置验证失败，请检查配置')
      }
      
      // 准备提交数据
      const submitData = CookieCloudApi.prepareSettingsForSubmit(editingSettings)
      
      const data = await CookieCloudApi.updateSettings(submitData)
      settings.value = data
      
      // 更新编辑中的设置
      Object.assign(editingSettings, {
        enabled: data.enabled,
        host: data.host || '',
        uuid: data.uuid || '',
        password: data.password ? '***' : '',
        sync_interval_minutes: data.sync_interval_minutes,
        safe_host_whitelist: data.safe_host_whitelist || []
      })
      
    } catch (error: any) {
      console.error('更新CookieCloud设置失败:', error)
      settingsError.value = error.response?.data?.message || error.message || '更新设置失败'
      throw error
    } finally {
      settingsLoading.value = false
    }
  }

  // 触发同步
  const triggerSync = async (options?: { batch_size?: number; site_timeout?: number }) => {
    try {
      syncLoading.value = true
      syncError.value = null
      
      const data = await CookieCloudApi.triggerSync(options)
      syncResult.value = data
      
      // 刷新设置和状态
      await Promise.all([
        fetchSettings(),
        fetchStatus()
      ])
      
    } catch (error: any) {
      console.error('触发CookieCloud同步失败:', error)
      syncError.value = error.response?.data?.message || error.message || '触发同步失败'
      throw error
    } finally {
      syncLoading.value = false
    }
  }

  // 立即同步
  const triggerSyncImmediate = async (options?: { batch_size?: number; site_timeout?: number }) => {
    try {
      syncLoading.value = true
      syncError.value = null
      
      const data = await CookieCloudApi.triggerSyncImmediate(options)
      syncResult.value = data
      
      // 刷新设置和状态
      await Promise.all([
        fetchSettings(),
        fetchStatus()
      ])
      
    } catch (error: any) {
      console.error('立即同步CookieCloud失败:', error)
      syncError.value = error.response?.data?.message || error.message || '立即同步失败'
      throw error
    } finally {
      syncLoading.value = false
    }
  }

  // 测试连接
  const testConnection = async () => {
    try {
      testLoading.value = true
      testError.value = null
      
      const data = await CookieCloudApi.testConnection()
      testResult.value = data
      
    } catch (error: any) {
      console.error('测试CookieCloud连接失败:', error)
      testError.value = error.response?.data?.message || error.message || '测试连接失败'
      throw error
    } finally {
      testLoading.value = false
    }
  }

  // 获取状态概览
  const fetchStatus = async () => {
    try {
      statusLoading.value = true
      statusError.value = null
      
      const data = await CookieCloudApi.getStatus()
      status.value = data
      
    } catch (error: any) {
      console.error('获取CookieCloud状态失败:', error)
      statusError.value = error.response?.data?.message || error.message || '获取状态失败'
      throw error
    } finally {
      statusLoading.value = false
    }
  }

  // 获取同步历史
  const fetchSyncHistory = async (params?: { page?: number; size?: number }) => {
    try {
      historyLoading.value = true
      historyError.value = null
      
      const data = await CookieCloudApi.getSyncHistory(params)
      syncHistory.value = data.items
      
    } catch (error: any) {
      console.error('获取CookieCloud同步历史失败:', error)
      historyError.value = error.response?.data?.message || error.message || '获取同步历史失败'
      throw error
    } finally {
      historyLoading.value = false
    }
  }

  // 重置编辑设置
  const resetEditingSettings = () => {
    if (settings.value) {
      Object.assign(editingSettings, {
        enabled: settings.value.enabled,
        host: settings.value.host || '',
        uuid: settings.value.uuid || '',
        password: settings.value.password ? '***' : '',
        sync_interval_minutes: settings.value.sync_interval_minutes,
        safe_host_whitelist: settings.value.safe_host_whitelist || []
      })
    }
  }

  // 清除错误状态
  const clearErrors = () => {
    settingsError.value = null
    syncError.value = null
    testError.value = null
    statusError.value = null
    historyError.value = null
  }

  return {
    // 状态
    settings,
    settingsLoading,
    settingsError,
    syncResult,
    syncLoading,
    syncError,
    testResult,
    testLoading,
    testError,
    status,
    statusLoading,
    statusError,
    syncHistory,
    historyLoading,
    historyError,
    editingSettings,
    
    // 计算属性
    isConfigured,
    lastSyncStatus,
    isSyncing,
    syncStatusText,
    syncStatusColor,
    
    // 方法
    fetchSettings,
    updateSettings,
    triggerSync,
    triggerSyncImmediate,
    testConnection,
    fetchStatus,
    fetchSyncHistory,
    resetEditingSettings,
    clearErrors
  }
})
