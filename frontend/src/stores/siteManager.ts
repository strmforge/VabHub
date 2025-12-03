/**
 * 站点管理状态管理 (SITE-MANAGER-1)
 * 使用Pinia管理站点数据、过滤、排序等状态
 */

import { defineStore } from 'pinia'
import { ref, reactive, computed } from 'vue'
import { api, type ApiResponse } from '@/utils/api'

import type {
  SiteBrief, SiteDetail, SiteUpdatePayload, SiteAccessConfigPayload,
  SiteListFilter, SiteHealthResult, SiteImportItem, SiteExportItem,
  ImportResult, BatchHealthCheckResult
} from '@/types/siteManager'
import { HealthStatus, CheckType } from '@/types/siteManager'

// Helper function to convert string to HealthStatus enum
const stringToHealthStatus = (status: string | undefined): HealthStatus => {
  if (!status) return HealthStatus.UNKNOWN
  switch (status) {
    case 'OK': return HealthStatus.OK
    case 'WARN': return HealthStatus.WARN
    case 'ERROR': return HealthStatus.ERROR
    default: return HealthStatus.UNKNOWN
  }
}

export const useSiteManagerStore = defineStore('siteManager', () => {
  // === 状态定义 ===
  
  // 站点列表
  const sites = ref<SiteBrief[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)
  
  // 当前选中的站点详情
  const currentSite = ref<SiteDetail | null>(null)
  const detailLoading = ref(false)
  
  // 过滤和搜索状态
  const filter = reactive<SiteListFilter>({
    enabled: null,
    category: null,
    health_status: null,
    keyword: '',
    tags: [],
    priority_min: null,
    priority_max: null
  })
  
  // 分类列表
  const categories = ref<Array<{key: string, name: string, icon: string}>>([])
  
  // 统计摘要
  const stats = ref({
    total_sites: 0,
    enabled_sites: 0,
    disabled_sites: 0,
    health_stats: {} as Record<string, number>,
    category_stats: {} as Record<string, number>
  })
  
  // === 计算属性 ===
  
  const filteredSites = computed(() => {
    let result = [...sites.value]
    
    // 启用状态过滤
    if (filter.enabled !== null) {
      result = result.filter(site => site.enabled === filter.enabled)
    }
    
    // 分类过滤
    if (filter.category) {
      result = result.filter(site => site.category === filter.category)
    }
    
    // 健康状态过滤
    if (filter.health_status) {
      result = result.filter(site => site.stats?.health_status === filter.health_status)
    }
    
    // 关键词搜索
    if (filter.keyword) {
      const keyword = filter.keyword.toLowerCase()
      result = result.filter(site => 
        site.name.toLowerCase().includes(keyword) ||
        site.domain?.toLowerCase().includes(keyword) ||
        site.key?.toLowerCase().includes(keyword)
      )
    }
    
    // 标签过滤
    if (filter.tags && filter.tags.length > 0) {
      result = result.filter(site => {
        if (!site.tags) return false
        const siteTags = typeof site.tags === 'string' 
          ? site.tags.split(',').map((t: string) => t.trim())
          : site.tags
        return filter.tags!.some((tag: string) => siteTags.includes(tag))
      })
    }
    
    // 优先级范围过滤
    if (filter.priority_min !== null) {
      result = result.filter(site => site.priority >= filter.priority_min!)
    }
    
    if (filter.priority_max !== null) {
      result = result.filter(site => site.priority <= filter.priority_max!)
    }
    
    return result
  })
  
  const enabledSites = computed(() => 
    filteredSites.value.filter(site => site.enabled)
  )
  
  const disabledSites = computed(() => 
    filteredSites.value.filter(site => !site.enabled)
  )
  
  const healthySites = computed(() => 
    filteredSites.value.filter(site => site.stats?.health_status === HealthStatus.OK)
  )
  
  const unhealthySites = computed(() => 
    filteredSites.value.filter(site => 
      site.stats?.health_status && site.stats.health_status !== HealthStatus.OK
    )
  )
  
  // === API调用方法 ===
  
  /**
   * 获取站点列表
   */
  const fetchSites = async () => {
    loading.value = true
    error.value = null
    
    try {
      const response: ApiResponse<SiteBrief[]> = await api.get('/api/sites', {
        params: filter
      })
      
      if (response.data.success) {
        // Convert health_status strings to enum values
        sites.value = response.data.data.map(site => ({
          ...site,
          stats: site.stats ? {
            ...site.stats,
            health_status: stringToHealthStatus(site.stats.health_status)
          } : undefined
        }))
      } else {
        throw new Error(response.data.message || '获取站点列表失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '未知错误'
      console.error('获取站点列表失败:', err)
    } finally {
      loading.value = false
    }
  }
  
  /**
   * 获取站点详情
   */
  const fetchSiteDetail = async (siteId: number) => {
    detailLoading.value = true
    error.value = null
    
    try {
      const response: ApiResponse<SiteDetail> = await api.get(`/api/sites/${siteId}`)
      
      if (response.data.success) {
        // Convert health_status strings to enum values
        const siteData = response.data.data
        currentSite.value = {
          ...siteData,
          stats: siteData.stats ? {
            ...siteData.stats,
            health_status: stringToHealthStatus(siteData.stats.health_status)
          } : undefined
        }
      } else {
        throw new Error(response.data.message || '获取站点详情失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '未知错误'
      console.error('获取站点详情失败:', err)
    } finally {
      detailLoading.value = false
    }
  }
  
  /**
   * 更新站点基本信息
   */
  const updateSite = async (siteId: number, payload: SiteUpdatePayload) => {
    try {
      const response: ApiResponse<SiteBrief> = await api.put(`/api/sites/${siteId}`, payload)
      
      if (response.data.success) {
        // Convert health_status strings to enum values
        const updatedSite = {
          ...response.data.data,
          stats: response.data.data.stats ? {
            ...response.data.data.stats,
            health_status: stringToHealthStatus(response.data.data.stats.health_status)
          } : undefined
        }
        
        // 更新本地站点列表
        const index = sites.value.findIndex((site: SiteBrief) => site.id === siteId)
        if (index !== -1) {
          Object.assign(sites.value[index], updatedSite)
        }
        
        // 更新当前站点详情
        if (currentSite.value?.id === siteId) {
          currentSite.value = updatedSite as SiteDetail
        }
        
        return updatedSite
      } else {
        throw new Error(response.data.message || '更新站点失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '未知错误'
      console.error('更新站点失败:', err)
      throw err
    }
  }
  
  /**
   * 更新站点访问配置
   */
  const updateSiteAccessConfig = async (siteId: number, payload: SiteAccessConfigPayload) => {
    try {
      const response: ApiResponse<SiteDetail> = await api.put(`/api/sites/${siteId}/access-config`, payload)
      
      if (response.data.success) {
        // Convert health_status strings to enum values
        const updatedSite = {
          ...response.data.data,
          stats: response.data.data.stats ? {
            ...response.data.data.stats,
            health_status: stringToHealthStatus(response.data.data.stats.health_status)
          } : undefined
        }
        
        // 更新当前站点详情
        if (currentSite.value?.id === siteId) {
          currentSite.value = updatedSite
        }
        
        return updatedSite
      } else {
        throw new Error(response.data.message || '更新访问配置失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '未知错误'
      console.error('更新访问配置失败:', err)
      throw err
    }
  }
  
  /**
   * 删除站点
   */
  const deleteSite = async (siteId: number) => {
    try {
      const response: ApiResponse<boolean> = await api.delete(`/api/sites/${siteId}`)
      
      if (response.data.success) {
        // 从本地列表中移除
        const index = sites.value.findIndex((site: SiteBrief) => site.id === siteId)
        if (index !== -1) {
          sites.value.splice(index, 1)
        }
        
        // 清空当前站点详情
        if (currentSite.value?.id === siteId) {
          currentSite.value = null
        }
        
        return true
      } else {
        throw new Error(response.data.message || '删除站点失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '未知错误'
      console.error('删除站点失败:', err)
      throw err
    }
  }
  
  /**
   * 执行站点健康检查
   */
  const checkSiteHealth = async (siteId: number, checkType: CheckType = CheckType.BASIC): Promise<SiteHealthResult> => {
    try {
      const response: ApiResponse<SiteHealthResult> = await api.post(`/api/sites/${siteId}/health-check`, null, {
        params: { check_type: checkType }
      })
      
      if (response.data.success) {
        const result = {
          ...response.data.data,
          status: stringToHealthStatus(response.data.data.status)
        }
        
        // 更新本地站点统计
        const siteIndex = sites.value.findIndex(site => site.id === siteId)
        if (siteIndex !== -1 && sites.value[siteIndex].stats) {
          sites.value[siteIndex].stats!.health_status = result.status
          sites.value[siteIndex].stats!.last_seen_at = result.status === HealthStatus.OK ? new Date().toISOString() : undefined
          sites.value[siteIndex].stats!.avg_response_time = result.response_time_ms
        }
        
        // 更新当前站点详情
        if (currentSite.value?.id === siteId && currentSite.value.stats) {
          currentSite.value.stats.health_status = result.status
          currentSite.value.stats.last_seen_at = result.status === HealthStatus.OK ? new Date().toISOString() : undefined
          currentSite.value.stats.avg_response_time = result.response_time_ms
        }
        
        return result
      } else {
        throw new Error(response.data.message || '健康检查失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '未知错误'
      console.error('健康检查失败:', err)
      throw err
    }
  }
  
  /**
   * 批量健康检查
   */
  const batchHealthCheck = async (siteIds: number[], checkType: CheckType = CheckType.BASIC): Promise<BatchHealthCheckResult> => {
    try {
      const response: ApiResponse<BatchHealthCheckResult> = await api.post('/api/sites/batch-health-check', siteIds, {
        params: { check_type: checkType }
      })
      
      if (response.data.success) {
        const result = {
          ...response.data.data,
          results: response.data.data.results.map(healthResult => ({
            ...healthResult,
            status: stringToHealthStatus(healthResult.status)
          }))
        }
        
        // 批量更新本地站点统计
        result.results.forEach((healthResult: SiteHealthResult) => {
          const siteIndex = sites.value.findIndex((site: SiteBrief) => site.id === healthResult.site_id)
          if (siteIndex !== -1 && sites.value[siteIndex].stats) {
            sites.value[siteIndex].stats!.health_status = healthResult.status
            sites.value[siteIndex].stats!.last_seen_at = healthResult.status === HealthStatus.OK ? new Date().toISOString() : undefined
            sites.value[siteIndex].stats!.avg_response_time = healthResult.response_time_ms
          }
        })
        
        return result
      } else {
        throw new Error(response.data.message || '批量健康检查失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '未知错误'
      console.error('批量健康检查失败:', err)
      throw err
    }
  }
  
  /**
   * 导入站点配置
   */
  const importSites = async (items: SiteImportItem[]): Promise<ImportResult> => {
    try {
      const response: ApiResponse<ImportResult> = await api.post('/api/sites/import', { items })
      
      if (response.data.success) {
        // 刷新站点列表
        await fetchSites()
        return response.data.data
      } else {
        throw new Error(response.data.message || '导入站点失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '未知错误'
      console.error('导入站点失败:', err)
      throw err
    }
  }
  
  /**
   * 导出站点配置
   */
  const exportSites = async (siteIds?: number[]): Promise<SiteExportItem[]> => {
    try {
      const params = siteIds ? { site_ids: siteIds.join(',') } : {}
      const response: ApiResponse<SiteExportItem[]> = await api.get('/api/sites/export', { params })
      
      if (response.data.success) {
        return response.data.data
      } else {
        throw new Error(response.data.message || '导出站点失败')
      }
    } catch (err) {
      error.value = err instanceof Error ? err.message : '未知错误'
      console.error('导出站点失败:', err)
      throw err
    }
  }
  
  /**
   * 获取站点分类列表
   */
  const fetchCategories = async () => {
    try {
      const response: ApiResponse<Array<{key: string, name: string, icon: string}>> = await api.get('/api/sites/categories/list')
      
      if (response.data.success) {
        categories.value = response.data.data
      } else {
        throw new Error(response.data.message || '获取分类列表失败')
      }
    } catch (err) {
      console.error('获取分类列表失败:', err)
    }
  }
  
  /**
   * 获取统计摘要
   */
  const fetchStats = async () => {
    try {
      const response: ApiResponse<{
        total_sites: number
        enabled_sites: number
        disabled_sites: number
        health_stats: Record<string, number>
        category_stats: Record<string, number>
      }> = await api.get('/api/sites/stats/summary')
      
      if (response.data.success) {
        stats.value = response.data.data
      } else {
        throw new Error(response.data.message || '获取统计摘要失败')
      }
    } catch (err) {
      console.error('获取统计摘要失败:', err)
    }
  }
  
  // === 过滤和搜索方法 ===
  
  /**
   * 设置过滤器
   */
  const setFilter = (newFilter: Partial<SiteListFilter>) => {
    Object.assign(filter, newFilter)
  }
  
  /**
   * 重置过滤器
   */
  const resetFilter = () => {
    Object.assign(filter, {
      enabled: null,
      category: null,
      health_status: null,
      keyword: '',
      tags: [],
      priority_min: null,
      priority_max: null
    })
  }
  
  /**
   * 切换站点启用状态
   */
  const toggleSiteEnabled = async (siteId: number) => {
    const site = sites.value.find((s: SiteBrief) => s.id === siteId)
    if (!site) return
    
    const newEnabled = !site.enabled
    await updateSite(siteId, { enabled: newEnabled })
  }
  
  /**
   * 调整站点优先级
   */
  const adjustSitePriority = async (siteId: number, delta: number) => {
    const site = sites.value.find((s: SiteBrief) => s.id === siteId)
    if (!site) return
    
    const newPriority = Math.max(0, site.priority + delta)
    await updateSite(siteId, { priority: newPriority })
  }
  
  // === 初始化方法 ===
  
  /**
   * 初始化站点管理器
   */
  const initialize = async () => {
    await Promise.all([
      fetchSites(),
      fetchCategories(),
      fetchStats()
    ])
  }
  
  return {
    // 状态
    sites,
    loading,
    error,
    currentSite,
    detailLoading,
    filter,
    categories,
    stats,
    
    // 计算属性
    filteredSites,
    enabledSites,
    disabledSites,
    healthySites,
    unhealthySites,
    
    // 方法
    fetchSites,
    fetchSiteDetail,
    updateSite,
    updateSiteAccessConfig,
    deleteSite,
    checkSiteHealth,
    batchHealthCheck,
    importSites,
    exportSites,
    fetchCategories,
    fetchStats,
    setFilter,
    resetFilter,
    toggleSiteEnabled,
    adjustSitePriority,
    initialize
  }
})
