/**
 * 仪表盘状态管理
 */

import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

interface SystemStats {
  cpu_usage: number
  memory_usage: number
  memory_total_gb: number
  memory_used_gb: number
  disk_usage: number
  disk_total_gb: number
  disk_used_gb: number
  disk_free_gb: number
  network_sent: number
  network_recv: number
}

interface MediaStats {
  total_movies: number
  total_tv_shows: number
  total_anime: number
  total_episodes: number
  total_size_gb: number
  by_quality: Record<string, number>
}

interface DownloadStats {
  active: number
  paused: number
  completed: number
  failed: number
  total_speed_mbps: number
  total_size_gb: number
  downloaded_gb: number
}

interface TTSStats {
  pending_jobs: number
  running_jobs: number
  completed_last_24h: number
}

interface PluginStats {
  total_plugins: number
  active_plugins: number
  quarantined_plugins: number
}

interface ReadingStats {
  active_novels: number
  active_audiobooks: number
  active_manga: number
}

interface RecentEvent {
  type: string
  title: string
  time: string | null
  message: string
  media_type?: string
  ebook_id?: number
  plugin_name?: string
}

interface DashboardData {
  system_stats: SystemStats
  media_stats: MediaStats
  download_stats: DownloadStats
  active_downloads: number
  active_subscriptions: number
  // 新增字段
  tts_stats: TTSStats
  plugin_stats: PluginStats
  reading_stats: ReadingStats
  recent_events: RecentEvent[]
}

export const useDashboardStore = defineStore('dashboard', () => {
  const loading = ref(false)
  const dashboardData = ref<DashboardData | null>(null)
  const systemStats = ref<SystemStats | null>(null)
  const mediaStats = ref<MediaStats | null>(null)
  const downloadStats = ref<DownloadStats | null>(null)
  
  // 更新系统统计（用于WebSocket实时更新）
  const updateSystemStats = (data: SystemStats) => {
    systemStats.value = data
    // 更新兼容格式
    if (stats.value) {
      stats.value.system = {
        cpu: data.cpu_usage || 0,
        memory: data.memory_usage || 0,
        disk: data.disk_usage || 0
      }
    }
  }
  
  // 兼容旧版本的stats格式
  const stats = ref({
    media: { total: 0 },
    downloads: { active: 0, totalSpeed: 0 },
    storage: { used: 0 },
    system: { cpu: 0, memory: 0, disk: 0 }
  })
  
  const downloadSpeedData = ref<any[]>([])
  
  // 更新仪表盘数据（用于WebSocket实时更新）
  const updateDashboardData = (data: DashboardData) => {
    dashboardData.value = data
    
    // 更新兼容格式
    if (data) {
      stats.value = {
        media: {
          total: (data.media_stats?.total_movies || 0) +
                 (data.media_stats?.total_tv_shows || 0) +
                 (data.media_stats?.total_anime || 0)
        },
        downloads: {
          active: data.download_stats?.active || 0,
          totalSpeed: (data.download_stats?.total_speed_mbps || 0) * 1024 * 1024 // 转换为字节/秒
        },
        storage: {
          used: data.system_stats?.disk_usage || 0
        },
        system: {
          cpu: data.system_stats?.cpu_usage || 0,
          memory: data.system_stats?.memory_usage || 0,
          disk: data.system_stats?.disk_usage || 0
        }
      }
    }
  }

  // 获取综合仪表盘数据
  const fetchDashboardData = async () => {
    loading.value = true
    try {
      const response = await api.get('/dashboard/')
      // 统一响应格式：response.data 已经是 data 字段的内容
      const data = response.data
      updateDashboardData(data)
      
      return data
    } catch (error) {
      console.error('Fetch dashboard data failed:', error)
      throw error
    } finally {
      loading.value = false
    }
  }
  
  // 获取系统统计
  const fetchSystemStats = async () => {
    try {
      const response = await api.get('/dashboard/system-stats')
      systemStats.value = response.data
      return response.data
    } catch (error) {
      console.error('Fetch system stats failed:', error)
      throw error
    }
  }
  
  // 获取媒体统计
  const fetchMediaStats = async () => {
    try {
      const response = await api.get('/dashboard/media-stats')
      mediaStats.value = response.data
      return response.data
    } catch (error) {
      console.error('Fetch media stats failed:', error)
      throw error
    }
  }
  
  // 获取下载统计
  const fetchDownloadStats = async () => {
    try {
      const response = await api.get('/dashboard/download-stats')
      downloadStats.value = response.data
      return response.data
    } catch (error) {
      console.error('Fetch download stats failed:', error)
      throw error
    }
  }
  
  return {
    loading,
    dashboardData,
    systemStats,
    mediaStats,
    downloadStats,
    stats,
    downloadSpeedData,
    fetchDashboardData,
    fetchSystemStats,
    fetchMediaStats,
    fetchDownloadStats,
    updateDashboardData,
    updateSystemStats
  }
})

