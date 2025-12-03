/**
 * 多模态分析性能监控API服务
 */

import api from './api'

// 性能指标相关
export const getMetrics = async (operation?: string) => {
  const params = operation ? { operation } : {}
  return api.get('/multimodal/metrics/metrics', { params })
}

export const getPerformanceSummary = async () => {
  return api.get('/multimodal/metrics/summary')
}

export const getCacheStats = async () => {
  return api.get('/multimodal/metrics/cache')
}

export const getTimeSeries = async (operation: string, minutes: number = 60) => {
  return api.get('/multimodal/metrics/timeseries', {
    params: { operation, minutes }
  })
}

export const resetMetrics = async () => {
  return api.post('/multimodal/metrics/reset')
}

// 历史数据相关
export const getHistoryMetrics = async (params: {
  operation?: string
  start_time?: string
  end_time?: string
  limit?: number
}) => {
  return api.get('/multimodal/history/metrics', { params })
}

export const getHistoryStatistics = async (params: {
  operation?: string
  start_time?: string
  end_time?: string
}) => {
  return api.get('/multimodal/history/statistics', { params })
}

// 告警相关
export const getAlerts = async (params: {
  operation?: string
  alert_type?: string
  resolved?: boolean
  limit?: number
}) => {
  return api.get('/multimodal/history/alerts', { params })
}

export const checkAlerts = async (params: {
  operation?: string
  time_window?: number
}) => {
  return api.post('/multimodal/history/alerts/check', null, { params })
}

export const resolveAlert = async (alertId: number, resolvedBy: string = 'system') => {
  return api.post(`/multimodal/history/alerts/${alertId}/resolve`, null, {
    params: { resolved_by: resolvedBy }
  })
}

export const cleanupHistory = async (days: number = 30) => {
  return api.post('/multimodal/history/cleanup', null, {
    params: { days }
  })
}

// 优化相关
export const optimizeAll = async () => {
  return api.post('/multimodal/auto-optimization/optimize/all')
}

export const optimizeCacheTTL = async (operation: string) => {
  return api.post('/multimodal/auto-optimization/optimize/cache-ttl', null, {
    params: { operation }
  })
}

export const optimizeConcurrency = async (operation: string) => {
  return api.post('/multimodal/auto-optimization/optimize/concurrency', null, {
    params: { operation }
  })
}

export const getOptimizationConfig = async () => {
  return api.get('/multimodal/auto-optimization/config')
}

export const updateOptimizationConfig = async (config: {
  cache_ttl?: Record<string, any>
  concurrency?: Record<string, any>
}) => {
  return api.post('/multimodal/auto-optimization/config', config)
}

export const getOptimizationHistory = async (params: {
  operation?: string
  optimization_type?: string
  limit?: number
}) => {
  return api.get('/multimodal/auto-optimization/optimization/history', { params })
}

// 缓存优化相关
export const analyzeCachePerformance = async () => {
  return api.get('/multimodal/optimization/cache/performance')
}

export const optimizeCacheTTLManual = async (operation: string, targetHitRate: number = 0.8) => {
  return api.get('/multimodal/optimization/cache/optimize-ttl', {
    params: { operation, target_hit_rate: targetHitRate }
  })
}

export const warmupCache = async (filePaths: string[], operation: string = 'video_analysis') => {
  return api.post('/multimodal/optimization/cache/warmup', {
    file_paths: filePaths,
    operation
  })
}

// 并发优化相关
export const analyzeConcurrencyPerformance = async (operation: string) => {
  return api.get('/multimodal/optimization/concurrency/performance', {
    params: { operation }
  })
}

export const optimizeConcurrencyManual = async (
  operation: string,
  targetAvgDuration: number = 1.0
) => {
  return api.get('/multimodal/optimization/concurrency/optimize', {
    params: { operation, target_avg_duration: targetAvgDuration }
  })
}

export const monitorConcurrency = async (operation: string, duration: number = 60) => {
  return api.get('/multimodal/optimization/concurrency/monitor', {
    params: { operation, duration }
  })
}

export const getOptimalConcurrency = async (operation: string) => {
  return api.get('/multimodal/optimization/concurrency/optimal', {
    params: { operation }
  })
}

