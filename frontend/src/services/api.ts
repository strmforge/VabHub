/**
 * API 客户端
 */

import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8001/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    // 处理统一响应格式
    if (response.data && typeof response.data === 'object') {
      // 检查是否是统一响应格式 {success, message, data, timestamp}
      if ('success' in response.data && 'data' in response.data) {
        // 如果是成功响应，自动提取data字段
        if (response.data.success) {
          // 创建一个新的响应对象，将data字段提取到顶层
          return {
            ...response,
            data: response.data.data
          }
        } else {
          // 如果是错误响应（success=false），转换为错误
          const error = new Error(response.data.error_message || response.data.message || '请求失败')
          ;(error as any).code = response.data.error_code
          ;(error as any).details = response.data.details
          const axiosError = Object.create(Error.prototype)
          Object.assign(axiosError, error, {
            response: {
              ...response,
              data: {
                error_code: response.data.error_code,
                error_message: response.data.error_message || response.data.message,
                details: response.data.details,
                timestamp: response.data.timestamp
              }
            },
            isAxiosError: true,
            config: response.config,
            request: response.request
          })
          return Promise.reject(axiosError)
        }
      }
      // 如果不是统一响应格式，直接返回（兼容旧格式或特殊端点）
      return response
    }
    return response
  },
  (error) => {
    // 处理错误响应
    if (error.response?.data) {
      const errorData = error.response.data
      
      // 检查是否是统一错误格式
      if (errorData.error_code && errorData.error_message) {
        error.message = errorData.error_message
        error.errorCode = errorData.error_code
        error.errorDetails = errorData.details
      } 
      // 检查是否是统一响应格式但success=false
      else if (errorData.success === false && errorData.error_message) {
        error.message = errorData.error_message
        error.errorCode = errorData.error_code
        error.errorDetails = errorData.details
      }
      // 兼容旧的错误格式
      else if (errorData.detail) {
        error.message = typeof errorData.detail === 'string' 
          ? errorData.detail 
          : errorData.detail.message || '请求失败'
      }
    }
    
    // 处理401未授权错误
    if (error.response?.status === 401) {
      const authStore = useAuthStore()
      authStore.logout()
      router.push('/login')
    }
    
    return Promise.reject(error)
  }
)

export default api

// RSS订阅API
export const rssApi = {
  // 获取RSS订阅列表
  getRSSSubscriptions: (params?: {
    enabled?: boolean
    page?: number
    page_size?: number
  }) => api.get('/rss', { params }),
  
  // 获取RSS订阅详情
  getRSSSubscription: (id: number) => api.get(`/rss/${id}`),
  
  // 创建RSS订阅
  createRSSSubscription: (data: {
    name: string
    url: string
    site_id?: number
    enabled?: boolean
    interval?: number
    filter_rules?: any
    download_rules?: any
    description?: string
  }) => api.post('/rss', data),
  
  // 更新RSS订阅
  updateRSSSubscription: (id: number, data: {
    name?: string
    url?: string
    site_id?: number
    enabled?: boolean
    interval?: number
    filter_rules?: any
    download_rules?: any
    description?: string
  }) => api.put(`/rss/${id}`, data),
  
  // 删除RSS订阅
  deleteRSSSubscription: (id: number) => api.delete(`/rss/${id}`),
  
  // 检查RSS订阅更新
  checkRSSUpdates: (id: number) => api.post(`/rss/${id}/check`),
  
  // 获取RSS项列表
  getRSSItems: (params?: {
    subscription_id?: number
    processed?: boolean
    downloaded?: boolean
    page?: number
    page_size?: number
  }) => api.get('/rss/items', { params }),
  
  // 获取RSS项详情
  getRSSItem: (id: number) => api.get(`/rss/items/${id}`),
  
  // 获取订阅的RSS项列表
  getSubscriptionRSSItems: (subscriptionId: number, params?: {
    processed?: boolean
    downloaded?: boolean
    page?: number
    page_size?: number
  }) => api.get(`/rss/${subscriptionId}/items`, { params }),
  
  // 获取订阅的RSS项统计
  getSubscriptionRSSItemsStats: (subscriptionId: number) => api.get(`/rss/${subscriptionId}/items/stats`)
}

// 媒体文件管理API
export const mediaRenamerApi = {
  // 识别媒体文件
  identifyMediaFile: (filePath: string) => api.post('/media-renamer/identify', null, {
    params: { file_path: filePath }
  }),
  
  // 批量识别媒体文件
  batchIdentifyMediaFiles: (filePaths: string[]) => api.post('/media-renamer/identify/batch', filePaths),
  
  // 整理单个媒体文件
  organizeFile: (data: {
    source_path: string
    target_base_dir: string
    rename_template?: string
    move_file?: boolean
    download_subtitle?: boolean
    subtitle_language?: string
    use_classification?: boolean
  }) => api.post('/media-renamer/organize', data),
  
  // 整理目录
  organizeDirectory: (data: {
    source_path: string
    target_base_dir: string
    rename_template?: string
    move_file?: boolean
    media_extensions?: string[]
    download_subtitle?: boolean
    subtitle_language?: string
    use_classification?: boolean
  }) => api.post('/media-renamer/organize/directory', data)
}

// 字幕管理API
export const subtitleApi = {
  // 下载字幕
  downloadSubtitle: (params: {
    media_file_path: string
    language?: string
    save_path?: string
    force_download?: boolean
  }) => api.post('/subtitle/download', null, { params }),
  
  // 搜索字幕
  searchSubtitles: (params: {
    media_file_path: string
    language?: string
  }) => api.get('/subtitle/search', { params }),
  
  // 获取字幕列表
  getSubtitles: (params?: {
    media_file_path?: string
    language?: string
    page?: number
    page_size?: number
  }) => api.get('/subtitle', { params }),
  
  // 获取字幕详情
  getSubtitle: (id: number) => api.get(`/subtitle/${id}`),
  
  // 删除字幕
  deleteSubtitle: (id: number) => api.delete(`/subtitle/${id}`)
}

// 重复文件检测API
export const duplicateDetectionApi = {
  // 检测重复文件
  detectDuplicates: (params: {
    directory: string
    extensions?: string[]
    use_hash?: boolean
  }) => api.post('/duplicate-detection/detect', null, { params }),
  
  // 比较重复文件质量
  compareDuplicates: (filePaths: string[]) => api.post('/duplicate-detection/compare', filePaths)
}

// 文件质量比较API
export const qualityComparisonApi = {
  // 比较文件质量
  compareQuality: (filePaths: string[]) => api.post('/quality-comparison/compare', filePaths),
  
  // 分析文件质量
  analyzeQuality: (filePath: string) => api.post('/quality-comparison/analyze', null, {
    params: { file_path: filePath }
  })
}

// 豆瓣API
export const doubanApi = {
  // 搜索豆瓣媒体
  searchDouban: (params: {
    query: string
    media_type?: string
    start?: number
    count?: number
  }) => api.get('/douban/search', { params }),
  
  // 获取豆瓣媒体详情
  getDoubanDetail: (subjectId: string, mediaType?: string) => api.get(`/douban/detail/${subjectId}`, {
    params: { media_type: mediaType || 'movie' }
  }),
  
  // 获取豆瓣评分
  getDoubanRating: (subjectId: string, mediaType?: string) => api.get(`/douban/rating/${subjectId}`, {
    params: { media_type: mediaType || 'movie' }
  }),
  
  // 获取豆瓣电影TOP250
  getDoubanTop250: (params?: {
    start?: number
    count?: number
  }) => api.get('/douban/top250', { params }),
  
  // 获取豆瓣热门电影
  getDoubanHotMovies: (params?: {
    start?: number
    count?: number
  }) => api.get('/douban/hot/movie', { params }),
  
  // 获取豆瓣热门电视剧
  getDoubanHotTV: (params?: {
    start?: number
    count?: number
  }) => api.get('/douban/hot/tv', { params })
}

// 存储监控API
export const storageMonitorApi = {
  // 获取存储目录列表
  getDirectories: (params?: {
    enabled?: boolean
  }) => api.get('/storage-monitor/directories', { params }),
  
  // 获取存储目录详情
  getDirectory: (id: number) => api.get(`/storage-monitor/directories/${id}`),
  
  // 创建存储目录
  createDirectory: (data: {
    name: string
    path: string
    enabled?: boolean
    alert_threshold?: number
    description?: string
  }) => api.post('/storage-monitor/directories', data),
  
  // 更新存储目录
  updateDirectory: (id: number, data: {
    name?: string
    enabled?: boolean
    alert_threshold?: number
    description?: string
  }) => api.put(`/storage-monitor/directories/${id}`, data),
  
  // 删除存储目录
  deleteDirectory: (id: number) => api.delete(`/storage-monitor/directories/${id}`),
  
  // 获取目录使用情况
  getDirectoryUsage: (id: number) => api.get(`/storage-monitor/directories/${id}/usage`),
  
  // 获取目录使用趋势
  getDirectoryTrends: (id: number, days?: number) => api.get(`/storage-monitor/directories/${id}/trends`, {
    params: { days: days || 7 }
  }),
  
  // 获取所有目录的使用情况
  getAllDirectoriesUsage: () => api.get('/storage-monitor/usage'),
  
  // 获取存储预警列表
  getAlerts: (params?: {
    directory_id?: number
    resolved?: boolean
    alert_type?: string
  }) => api.get('/storage-monitor/alerts', { params }),
  
  // 解决存储预警
  resolveAlert: (id: number) => api.post(`/storage-monitor/alerts/${id}/resolve`),
  
  // 获取存储监控统计信息
  getStatistics: () => api.get('/storage-monitor/statistics')
}

// 调度器API
export const schedulerApi = {
  // 获取任务列表
  getJobs: (params?: {
    status?: string
    enabled?: boolean
    task_type?: string
  }) => api.get('/scheduler/jobs', { params }),
  
  // 获取任务详情
  getJob: (jobId: string) => api.get(`/scheduler/jobs/${jobId}`),
  
  // 获取任务执行历史
  getJobExecutions: (jobId: string, params?: {
    page?: number
    page_size?: number
  }) => api.get(`/scheduler/jobs/${jobId}/executions`, { params }),
  
  // 获取统计信息
  getStatistics: () => api.get('/scheduler/statistics'),
  
  // 同步任务
  syncTasks: () => api.post('/scheduler/sync'),
  
  // 立即执行任务
  runJob: (jobId: string) => api.post(`/scheduler/jobs/${jobId}/run`),
  
  // 移除任务
  removeJob: (jobId: string) => api.delete(`/scheduler/jobs/${jobId}`)
}

// 媒体服务器API
export const mediaServerApi = {
  // 获取媒体服务器列表
  getMediaServers: (params?: {
    enabled?: boolean
    server_type?: string
  }) => api.get('/media-servers', { params }),
  
  // 获取媒体服务器详情
  getMediaServer: (serverId: number) => api.get(`/media-servers/${serverId}`),
  
  // 创建媒体服务器
  createMediaServer: (data: {
    name: string
    server_type: string
    url: string
    api_key?: string
    token?: string
    username?: string
    password?: string
    user_id?: string
    enabled?: boolean
    sync_enabled?: boolean
    sync_interval?: number
    sync_watched_status?: boolean
    sync_playback_status?: boolean
    sync_metadata?: boolean
  }) => api.post('/media-servers', data),
  
  // 更新媒体服务器
  updateMediaServer: (serverId: number, data: {
    name?: string
    url?: string
    api_key?: string
    token?: string
    username?: string
    password?: string
    user_id?: string
    enabled?: boolean
    sync_enabled?: boolean
    sync_interval?: number
    sync_watched_status?: boolean
    sync_playback_status?: boolean
    sync_metadata?: boolean
  }) => api.put(`/media-servers/${serverId}`, data),
  
  // 删除媒体服务器
  deleteMediaServer: (serverId: number) => api.delete(`/media-servers/${serverId}`),
  
  // 检查服务器连接
  checkConnection: (serverId: number) => api.post(`/media-servers/${serverId}/check`),
  
  // 同步媒体库
  syncLibraries: (serverId: number) => api.post(`/media-servers/${serverId}/sync/libraries`),
  
  // 同步元数据
  syncMetadata: (serverId: number) => api.post(`/media-servers/${serverId}/sync/metadata`),
  
  // 获取播放会话
  getPlaybackSessions: (serverId: number) => api.get(`/media-servers/${serverId}/playback-sessions`),
  
  // 获取同步历史
  getSyncHistory: (serverId: number, params?: {
    page?: number
    page_size?: number
  }) => api.get(`/media-servers/${serverId}/sync-history`, { params })
}

// 仪表盘布局API
export const dashboardLayoutApi = {
  // 获取布局
  getLayout: (layoutId?: number) => api.get('/dashboard/layout', {
    params: layoutId ? { layout_id: layoutId } : {}
  }),
  
  // 保存布局
  saveLayout: (data: {
    name: string
    breakpoint?: string
    cols?: number
    row_height?: number
    margin?: number[]
    layouts: Record<string, any>
    widgets: string[]
    is_default?: boolean
  }, layoutId?: number) => api.post('/dashboard/layout', data, {
    params: layoutId ? { layout_id: layoutId } : {}
  }),
  
  // 列出所有布局
  listLayouts: () => api.get('/dashboard/layouts'),
  
  // 删除布局
  deleteLayout: (layoutId: number) => api.delete(`/dashboard/layout/${layoutId}`),
  
  // 获取组件列表
  getWidgets: () => api.get('/dashboard/widgets')
}

// 媒体API
export const mediaApi = {
  // 搜索媒体
  searchMedia: (params: {
    query: string
    type?: 'movie' | 'tv'
  }) => api.get('/media/search', { params }),
  
  // 获取媒体详情
  getMediaDetails: (tmdbId: number, type: 'movie' | 'tv') => 
    api.get(`/media/details/${tmdbId}`, { params: { type } }),
  
  // 获取演职员表
  getMediaCredits: (tmdbId: number, type: 'movie' | 'tv') => 
    api.get(`/media/credits/${tmdbId}`, { params: { type } }),
  
  // 获取人物详情
  getPersonDetails: (personId: number) => 
    api.get(`/media/person/${personId}`),
  
  // 获取类似媒体
  getSimilarMedia: (tmdbId: number, type: 'movie' | 'tv') => 
    api.get(`/media/similar/${tmdbId}`, { params: { type } }),
  
  // 获取推荐媒体
  getRecommendedMedia: (tmdbId: number, type: 'movie' | 'tv') => 
    api.get(`/media/recommendations/${tmdbId}`, { params: { type } }),
  
  // 获取电视剧季信息
  getTVSeasons: (tmdbId: number) => 
    api.get(`/media/seasons/${tmdbId}`)
}

// Bangumi API
export const bangumiApi = {
  // 搜索动漫
  searchAnime: (params: {
    query: string
    limit?: number
  }) => api.get('/bangumi/search', { params }),
  
  // 获取动漫详情
  getAnimeDetail: (subjectId: number) => 
    api.get(`/bangumi/subject/${subjectId}`),
  
  // 获取每日放送
  getCalendar: () => api.get('/bangumi/calendar'),
  
  // 获取热门动漫
  getPopularAnime: (params?: {
    limit?: number
  }) => api.get('/bangumi/popular', { params })
}

// 下载器管理API
export const downloaderApi = {
  // 获取下载器实例列表
  getInstances: () => api.get('/dl/instances'),
  
  // 获取下载器统计信息
  getStats: (did: string) => api.get(`/dl/${did}/stats`),
  
  // 测试下载器连接
  testConnection: (did: string) => api.post(`/dl/${did}/test`)
}

// 网关签名API
export const gatewayApi = {
  // 对URL路径进行HMAC签名
  sign: (data: {
    path: string
    method?: string
  }) => api.post('/gateway/sign', data)
}

// 插件管理API
export const pluginsApi = {
  // 获取插件注册表
  getRegistry: () => api.get('/plugins/registry'),
  
  // 安装插件
  installPlugin: (pid: string) => api.post(`/plugins/${pid}/install`),
  
  // 获取插件列表
  getPlugins: () => api.get('/plugins/list'),
  
  // 获取插件状态
  getStatus: () => api.get('/plugins/status'),
  
  // 加载插件
  loadPlugin: (pluginName: string) => api.post('/plugins/load', { plugin_name: pluginName }),
  
  // 卸载插件
  unloadPlugin: (pluginName: string) => api.post(`/plugins/unload/${pluginName}`),
  
  // 重新加载插件
  reloadPlugin: (pluginName: string) => api.post(`/plugins/reload/${pluginName}`),
  
  // 启用热重载
  enableHotReload: () => api.post('/plugins/hot-reload/enable'),
  
  // 禁用热重载
  disableHotReload: () => api.post('/plugins/hot-reload/disable')
}

// 规则集管理API
export const rulesetApi = {
  // 获取规则集配置
  getRuleset: () => api.get('/ruleset'),
  
  // 更新规则集配置
  updateRuleset: (data: {
    rules: Record<string, any>
  }) => api.put('/ruleset', data)
}

// 刮削器管理API
export const scraperApi = {
  // 获取刮削器配置
  getConfig: () => api.get('/scraper/config'),
  
  // 更新刮削器配置
  updateConfig: (data: {
    tmdb_enabled?: boolean
    douban_enabled?: boolean
    tvdb_enabled?: boolean
    fanart_enabled?: boolean
    musicbrainz_enabled?: boolean
    acoustid_enabled?: boolean
    tmdb_api_key?: string
    douban_api_key?: string
    acoustid_api_key?: string
    cache_enabled?: boolean
    cache_ttl?: number
  }) => api.put('/scraper/config', data),
  
  // 测试刮削器连接
  testScraper: (scraperType: string, testQuery?: string) => 
    api.post('/scraper/test', null, {
      params: {
        scraper_type: scraperType,
        test_query: testQuery
      }
    })
}

// 密钥管理API
export const secretsApi = {
  // 获取密钥状态
  getStatus: () => api.get('/secrets/status')
}

// 下载管理API
export const downloadApi = {
  // 获取下载列表
  getDownloads: (params?: {
    status?: string
    vabhub_only?: boolean
    page?: number
    page_size?: number
  }) => api.get('/downloads', { params }),
  
  // 获取下载详情
  getDownload: (taskId: string) => api.get(`/downloads/${taskId}`),
  
  // 创建下载任务
  createDownload: (data: {
    title: string
    magnet_link?: string
    torrent_url?: string
    downloader?: string
    save_path?: string
    subscription_id?: number
    size_gb?: number
  }) => api.post('/downloads', data),
  
  // 暂停下载
  pauseDownload: (taskId: string) => api.post(`/downloads/${taskId}/pause`),
  
  // 恢复下载
  resumeDownload: (taskId: string) => api.post(`/downloads/${taskId}/resume`),
  
  // 删除下载
  deleteDownload: (taskId: string) => api.delete(`/downloads/${taskId}`),
  
  // 批量暂停
  batchPause: (taskIds: string[]) => api.post('/downloads/batch/pause', { task_ids: taskIds }),
  
  // 批量恢复
  batchResume: (taskIds: string[]) => api.post('/downloads/batch/resume', { task_ids: taskIds }),
  
  // 批量删除
  batchDelete: (taskIds: string[], deleteFiles?: boolean) => 
    api.post('/downloads/batch/delete', { task_ids: taskIds, delete_files: deleteFiles || false }),
  
  // 队列上移
  queueMoveUp: (taskId: string) => api.post(`/downloads/${taskId}/queue/up`),
  
  // 队列下移
  queueMoveDown: (taskId: string) => api.post(`/downloads/${taskId}/queue/down`),
  
  // 队列置顶
  queueMoveTop: (taskId: string) => api.post(`/downloads/${taskId}/queue/top`),
  
  // 设置全局速度限制
  setGlobalSpeedLimit: (downloader: string, data: {
    download_limit?: number
    upload_limit?: number
  }) => api.put(`/downloads/speed-limit/global?downloader=${downloader}`, data),
  
  // 获取全局速度限制
  getGlobalSpeedLimit: (downloader: string) => 
    api.get(`/downloads/speed-limit/global?downloader=${downloader}`),
  
  // 设置任务速度限制
  setTaskSpeedLimit: (taskId: string, data: {
    download_limit?: number
    upload_limit?: number
  }) => api.put(`/downloads/${taskId}/speed-limit`, data),
  
  // 批量设置任务速度限制
  batchSetSpeedLimit: (taskIds: string[], data: {
    download_limit?: number
    upload_limit?: number
  }) => api.post('/downloads/batch/speed-limit', { task_ids: taskIds, ...data }),
  
  // 批量队列操作
  batchQueueUp: (taskIds: string[]) => api.post('/downloads/batch/queue/up', { task_ids: taskIds }),
  batchQueueDown: (taskIds: string[]) => api.post('/downloads/batch/queue/down', { task_ids: taskIds }),
  batchQueueTop: (taskIds: string[]) => api.post('/downloads/batch/queue/top', { task_ids: taskIds })
}

export const systemApi = {
  getSelfCheck: () => api.get('/system/selfcheck')
}

// 小说导入 API（Dev 用）
export const novelApi = {
  uploadTxtNovel: (formData: FormData) => {
    return api.post<{
      success: boolean
      ebook_path: string
      ebook_id: number | null
      message: string
    }>('/dev/novel/upload-txt', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}

// 统一收件箱 API（Dev 用）
export const inboxApi = {
  preview: () => {
    return api.get<{
      items: Array<{
        path: string
        media_type: string
        score: number
        reason: string
        size_bytes: number
        modified_at: string
      }>
    }>('/dev/inbox/preview')
  },
  runOnce: () => {
    return api.post<{
      items: Array<{
        path: string
        media_type: string
        score: number
        reason: string
        size_bytes: number
        modified_at: string
        result: string
      }>
    }>('/dev/inbox/run-once')
  }
}

// 统一媒体库预览 API
export const libraryApi = {
  // 获取统一媒体库预览列表
  getPreview: (params?: {
    page?: number
    page_size?: number
    media_types?: string[]  // 例如: ['movie', 'ebook', 'audiobook']
  }) => {
    const queryParams: any = {}
    if (params?.page) queryParams.page = params.page
    if (params?.page_size) queryParams.page_size = params.page_size
    if (params?.media_types && params.media_types.length > 0) {
      queryParams.media_types = params.media_types.join(',')
    }
    return api.get('/library/preview', { params: queryParams })
  }
}

// 电子书 API
export const ebookApi = {
  // 获取电子书列表
  getEbooks: (params?: {
    keyword?: string
    author?: string
    series?: string
    page?: number
    page_size?: number
  }) => api.get('/ebooks', { params }),
  
  // 获取电子书详情
  getEbook: (ebookId: number) => api.get(`/ebooks/${ebookId}`),
  
  // 获取电子书统计
  getStats: () => api.get('/ebooks/stats/summary')
}

// 有声书 API
// 媒体库设置 API（只读）
export const adminSettingsApi = {
  getLibrarySettings: () => api.get<{
    inbox: {
      inbox_root: string
      enabled: boolean
      enabled_media_types: string[]
      detection_min_score: number
      scan_max_items: number
      last_run_at: string | null
      last_run_status: 'never' | 'success' | 'partial' | 'failed' | 'empty'
      last_run_summary: string | null
      pending_warning: string | null
    }
    library_roots: {
      movie: string
      tv: string
      anime: string
      short_drama?: string | null
      ebook: string
      comic?: string | null
      music?: string | null
    }
  }>('/admin/settings/library'),
  getTTSSettings: () => api.get<import('@/types/settings').TTSSettings>('/admin/settings/tts')
}

// 作品中心 API
export const workLinksApi = {
  // 获取指定 ebook 的所有关联
  listByEbook: (ebookId: number) => api.get<Array<{
    id: number
    ebook_id: number
    target_type: "video" | "comic" | "music"
    target_id: number
    relation: "include" | "exclude"
    created_at: string
    updated_at: string
  }>>(`/admin/work-links/by-ebook/${ebookId}`),
  
  // 创建或更新作品关联
  createOrUpdate: (payload: {
    ebook_id: number
    target_type: "video" | "comic" | "music"
    target_id: number
    relation: "include" | "exclude"
  }) => api.post<{
    id: number
    ebook_id: number
    target_type: "video" | "comic" | "music"
    target_id: number
    relation: "include" | "exclude"
    created_at: string
    updated_at: string
  }>("/admin/work-links", payload),
  
  // 删除作品关联
  delete: (linkId: number) => api.delete(`/admin/work-links/${linkId}`),
  
  // 通过组合键删除作品关联
  deleteByTarget: (params: {
    ebook_id: number
    target_type: "video" | "comic" | "music"
    target_id: number
  }) => api.delete("/admin/work-links/by-target", { params })
}

export const workApi = {
  // 获取作品详情（聚合电子书、有声书、漫画）
  getWorkDetail: (ebookId: number) => api.get<{
    ebook: {
      id: number
      title: string
      original_title?: string | null
      author?: string | null
      series?: string | null
      volume_index?: string | null
      language?: string | null
      publish_year?: number | null
      isbn?: string | null
      tags?: string | null
      description?: string | null
      cover_url?: string | null
      extra_metadata?: Record<string, any> | null
      created_at: string
      updated_at: string
    }
    ebook_files: Array<{
      id: number
      file_path: string
      format?: string | null
      file_size_mb?: number | null
      source_site_id?: string | null
      source_torrent_id?: string | null
      download_task_id?: number | null
      created_at: string
    }>
    audiobooks: Array<{
      id: number
      title?: string | null
      format?: string | null
      duration_seconds?: number | null
      bitrate_kbps?: number | null
      sample_rate_hz?: number | null
      channels?: number | null
      narrator?: string | null
      language?: string | null
      file_size_mb?: number | null
      source_site_id?: string | null
      download_task_id?: number | null
      created_at: string
    }>
    comics: Array<{
      id: number
      title: string
      series?: string | null
      volume_index?: number | null
      author?: string | null
      illustrator?: string | null
      language?: string | null
      region?: string | null
      publish_year?: number | null
      cover_url?: string | null
      tags?: string | null
    }>
    comic_files: Array<{
      id: number
      comic_id: number
      file_path: string
      file_size_mb?: number | null
      format?: string | null
      page_count?: number | null
      source_site_id?: string | null
      source_torrent_id?: string | null
      download_task_id?: number | null
      created_at: string
    }>
  }>(`/api/works/${ebookId}`)
}

export const audiobookApi = {
  // 获取有声书列表
  getAudiobooks: (params?: {
    keyword?: string
    author?: string
    narrator?: string
    page?: number
    page_size?: number
  }) => api.get('/audiobooks', { params }),
  
  // 获取有声书详情
  getAudiobook: (audiobookId: number) => api.get(`/audiobooks/${audiobookId}`),
  
  // 根据 EBook ID 获取该作品下的所有有声书文件
  getAudiobooksByEbook: (ebookId: number) => api.get(`/audiobooks/by-ebook/${ebookId}`),
  
  // 获取有声书统计
  getStats: () => api.get('/audiobooks/stats/summary')
}

// TTS 重新生成 Dev API
export const devTTSApi = {
  regenForWork: async (ebookId: number) => {
    const { data } = await api.post(`/dev/tts/regenerate-for-work/${ebookId}`)
    return data as {
      success: boolean
      status: string
      created_count: number
      skipped_count: number
      message?: string
    }
  },
  playgroundSynthesize: async (payload: import('@/types/tts').TTSPlaygroundRequest) => {
    const { data } = await api.post('/dev/tts/playground/synthesize', payload)
    return data as import('@/types/tts').TTSPlaygroundResponse
  }
}

// TTS Jobs Dev API
export const devTTSJobsApi = {
  list: async (params?: { status?: string; ebook_id?: number; limit?: number }) => {
    const { data } = await api.get<import('@/types/tts').TTSJob[]>('/dev/tts/jobs', { params })
    return data
  },
  get: async (jobId: number) => {
    const { data } = await api.get<import('@/types/tts').TTSJob>(`/dev/tts/jobs/${jobId}`)
    return data
  },
  enqueueForWork: async (ebookId: number) => {
    const { data } = await api.post<import('@/types/tts').TTSJob>(`/dev/tts/jobs/enqueue-for-work/${ebookId}`)
    return data
  },
  runNext: async () => {
    const { data } = await api.post<{
      success: boolean
      reason?: string
      message?: string
      job?: import('@/types/tts').TTSJob
    }>('/dev/tts/jobs/run-next')
    return data
  },
  runBatch: async (maxJobs?: number) => {
    const { data } = await api.post<{
      total_jobs: number
      run_jobs: number
      succeeded_jobs: number
      partial_jobs: number
      failed_jobs: number
      last_job_id?: number | null
      message: string
    }>('/dev/tts/jobs/run-batch', { max_jobs: maxJobs ?? null })
    return data
  }
}

// 电视墙智能打开 API
export const tvWallApi = {
  smartOpen: async (
    payload: import('@/types/playerWall').TvWallSmartOpenRequest
  ) => {
    const { data } = await api.post<import('@/types/playerWall').TvWallSmartOpenResponse>(
      '/api/tvwall/smart-open',
      payload
    )
    return data
  }
}

// TTS Work Profile API
export const devTTSWorkProfileApi = {
  getForWork: async (ebookId: number) => {
    const { data } = await api.get<import('@/types/tts').TTSWorkProfile | null>(`/dev/tts/work-profile/${ebookId}`)
    return data
  },
  upsert: async (payload: {
    ebook_id: number
    preset_id?: number | null
    provider?: string | null
    language?: string | null
    voice?: string | null
    speed?: number | null
    pitch?: number | null
    enabled?: boolean
    notes?: string | null
  }) => {
    const { data } = await api.post<import('@/types/tts').TTSWorkProfile>('/dev/tts/work-profile', payload)
    return data
  },
  delete: async (ebookId: number) => {
    const { data } = await api.delete<{ success: boolean; message: string }>(`/dev/tts/work-profile/${ebookId}`)
    return data
  }
}

// TTS Voice Presets API
export const devTTSVoicePresetsApi = {
  list: async () => {
    const { data } = await api.get<import('@/types/tts').TTSVoicePreset[]>('/dev/tts/voice-presets')
    return data
  },
  upsert: async (payload: Partial<import('@/types/tts').TTSVoicePreset> & { name: string }) => {
    const { data } = await api.post<import('@/types/tts').TTSVoicePreset>('/dev/tts/voice-presets', payload)
    return data
  },
  delete: async (id: number) => {
    const { data } = await api.delete<{ success: boolean; message: string; affected_profiles?: number }>(`/dev/tts/voice-presets/${id}`)
    return data
  }
}

// TTS Work Batch API
export const devTTSWorkBatchApi = {
  preview: async (filter: import('@/types/tts').TTSWorkBatchFilter) => {
    const { data } = await api.post<import('@/types/tts').TTSWorkBatchPreviewResponse>('/dev/tts/work-batch/preview', filter)
    return data
  },
  apply: async (req: import('@/types/tts').ApplyTTSWorkPresetRequest) => {
    const { data } = await api.post<import('@/types/tts').ApplyTTSWorkPresetResult>('/dev/tts/work-batch/apply', req)
    return data
  }
}

// 用户版 TTS Flow API
export const ttsUserApi = {
  enqueueForWork: async (ebookId: number) => {
    const { data } = await api.post<import('@/types/tts').UserTTSJobEnqueueResponse>(`/tts/jobs/enqueue-for-work/${ebookId}`)
    return data
  },
  getStatusByEbook: async (ebookId: number) => {
    const { data } = await api.get<import('@/types/tts').UserWorkTTSStatus>(`/tts/jobs/status/by-ebook/${ebookId}`)
    return data
  },
  getOverview: async (params?: { limit?: number; status?: string }) => {
    const { data } = await api.get<import('@/types/tts').UserTTSJobOverviewItem[]>('/tts/jobs/overview', { params })
    return data
  },
  // 批量 TTS API
  batchPreview: async (filter: import('@/types/tts').UserTTSBatchFilter) => {
    const { data } = await api.post<import('@/types/tts').UserTTSBatchPreviewResponse>('/tts/batch/preview', filter)
    return data
  },
  batchEnqueue: async (req: import('@/types/tts').UserTTSBatchEnqueueRequest) => {
    const { data } = await api.post<import('@/types/tts').UserTTSBatchEnqueueResult>('/tts/batch/enqueue', req)
    return data
  }
}

// TTS 存储管理 Dev API
export const devTTSStorageApi = {
  getOverview: async () => {
    const { data } = await api.get<import('@/types/tts').TTSStorageOverviewResponse>('/dev/tts/storage/overview')
    return data
  },
  getPolicy: async () => {
    const { data } = await api.get<import('@/types/tts').TTSStoragePolicy>('/dev/tts/storage/policy')
    return data
  },
  previewCleanup: async (payload: import('@/types/tts').TTSStorageCleanupPreviewRequest) => {
    const { data } = await api.post<import('@/types/tts').TTSStorageCleanupPreviewResponse>('/dev/tts/storage/preview', payload)
    return data
  },
  runCleanup: async (payload: import('@/types/tts').TTSStorageCleanupExecuteRequest) => {
    const { data } = await api.post<import('@/types/tts').TTSStorageCleanupExecuteResponse>('/dev/tts/storage/cleanup', payload)
    return data
  }
}

// 用户有声书播放 API
export const audiobookUserApi = {
  getWorkStatus: async (ebookId: number) => {
    const { data } = await api.get<import('@/types/tts').UserWorkAudiobookStatus>(`/user/audiobooks/progress/by-ebook/${ebookId}`)
    return data
  },
  updateWorkProgress: async (ebookId: number, payload: {
    audiobook_file_id: number
    position_seconds: number
    duration_seconds?: number | null
  }) => {
    const { data } = await api.post<import('@/types/tts').UserWorkAudiobookStatus>(`/user/audiobooks/progress/by-ebook/${ebookId}`, payload)
    return data
  },
  getFileStreamUrl: (fileId: number) => {
    return `/api/audiobooks/files/${fileId}/stream`
  }
}

// 小说中心聚合 API
export const novelCenterApi = {
  getList: async (params?: {
    page?: number
    page_size?: number
    keyword?: string
    author?: string
    series?: string
  }) => {
    const { data } = await api.get<import('@/types/novel').NovelCenterListResponse>('/novels/center/list', { params })
    return data
  }
}

// 小说 Inbox 管理 API
export const novelInboxApi = {
  getLogs: async (params?: {
    page?: number
    page_size?: number
    status?: string
    path_substring?: string
  }) => {
    const { data } = await api.get<import('@/types/audiobook').NovelInboxLogListResponse>('/api/dev/novels/inbox/import-logs', { params })
    return data
  },
  scan: async (payload: {
    max_files?: number
    generate_tts?: boolean
  }) => {
    const { data } = await api.post<import('@/types/audiobook').NovelInboxScanResult>('/api/dev/novels/inbox/scan', payload)
    return data
  }
}

// 有声书中心聚合 API
export const audiobookCenterApi = {
  getList: async (params?: {
    page?: number
    page_size?: number
    keyword?: string
    tts_status?: string
    progress_filter?: string
  }) => {
    const { data } = await api.get<import('@/types/audiobook').AudiobookCenterListResponse>('/audiobooks/center/list', { params })
    return data
  }
}

// 小说阅读器 API
export const novelReaderApi = {
  getChapters: async (ebookId: number) => {
    const { data } = await api.get<import('@/types/novel').NovelChapterSummary[]>(`/api/novels/${ebookId}/chapters`)
    return data
  },
  getChapterText: async (ebookId: number, chapterIndex: number) => {
    const { data } = await api.get<import('@/types/novel').NovelChapterTextResponse>(`/api/novels/${ebookId}/chapters/${chapterIndex}`)
    return data
  },
  getReadingProgress: async (ebookId: number) => {
    const { data } = await api.get<import('@/types/novel').UserNovelReadingProgress>(`/api/user/novels/reading-progress/by-ebook/${ebookId}`)
    return data
  },
  updateReadingProgress: async (ebookId: number, payload: {
    current_chapter_index: number
    chapter_offset: number
    is_finished?: boolean
  }) => {
    const { data } = await api.post<import('@/types/novel').UserNovelReadingProgress>(
      `/api/user/novels/reading-progress/by-ebook/${ebookId}`,
      payload
    )
    return data
  }
}

// 小说搜索 API
export const novelSearchApi = {
  searchInBook: async (ebookId: number, params: { q: string; max_hits?: number }) => {
    const { data } = await api.get<import('@/types/novel').NovelSearchHit[]>(`/api/novels/${ebookId}/search`, { params })
    return data
  }
}

// 用户通知 API
export const notificationApi = {
  // 获取分页通知列表 (使用 notifications_user.py)
  list: async (params?: {
    page?: number
    page_size?: number
    is_read?: boolean
    category?: string
    type?: string
    media_type?: string
  }) => {
    const { data } = await api.get<import('@/types/notify').UserNotificationListResponse>('/api/user/notifications', {
      params: {
        limit: params?.page_size || 20,
        offset: params?.page ? (params.page - 1) * (params.page_size || 20) : 0,
        is_read: params?.is_read,
        category: params?.category,
        type: params?.type,
        media_type: params?.media_type
      }
    })
    return data
  },
  
  // 获取最近通知列表 (使用 notifications_user.py)
  getRecent: async (limit = 20) => {
    const { data } = await api.get<import('@/types/notify').UserNotificationListResponse>('/api/user/notifications/recent', {
      params: { limit }
    })
    return data
  },
  
  // 获取未读数量 (使用 notifications_user.py)
  getUnreadCount: async () => {
    const { data } = await api.get<{ unread_count: number }>('/api/user/notifications/unread-count')
    return data
  },
  
  // 标记单条已读 (使用 notifications_user.py)
  markRead: async (id: number) => {
    const { data } = await api.post<{ success: boolean; updated: number }>('/api/user/notifications/mark-read', {
      ids: [id]
    })
    return data
  },

  // 批量标记已读 (新增功能)
  markReadBatch: async (ids: number[]) => {
    const { data } = await api.post<{ success: boolean; updated: number }>('/api/user/notifications/mark-read', {
      ids
    })
    return data
  },
  
  // 全部标记已读 (使用 notifications_user.py)
  markAllRead: async () => {
    const { data } = await api.post<{ success: boolean; updated: number }>('/api/user/notifications/mark-read')
    return data
  },

  // 按分类批量标记已读 (新增功能)
  markCategoryRead: async (category: string) => {
    const { data } = await api.post<{ success: boolean; updated: number }>('/api/user/notifications/mark-read', {
      category
    })
    return data
  },

  // 获取按分类统计的未读数量 (新增功能)
  getCategoryUnreadCount: async () => {
    const { data } = await api.get<{ unread_by_category: Record<string, number>; total_unread: number }>('/api/user/notifications/unread-count-by-category')
    return data
  },

  // 批量删除通知 (新增功能)
  deleteBatch: async (ids: number[]) => {
    const { data } = await api.delete<{ success: boolean; deleted: number }>('/api/user/notifications/batch', {
      data: { ids }
    })
    return data
  },

  // 按分类批量删除通知 (新增功能)
  deleteCategory: async (category: string) => {
    const { data } = await api.delete<{ success: boolean; deleted: number }>('/api/user/notifications/batch', {
      data: { category }
    })
    return data
  },

  // 删除单条通知 (更新)
  delete: async (id: number) => {
    const { data } = await api.delete<{ success: boolean; deleted: number }>(`/api/user/notifications/${id}`)
    return data
  },

  // 删除所有通知 (更新)
  deleteAll: async () => {
    const { data } = await api.delete<{ success: boolean; deleted: number }>('/api/user/notifications/')
    return data
  }
}

// 保留向后兼容的别名
export const userNotificationsApi = notificationApi

// 我的书架 API
export const myShelfApi = {
  getList: async (params?: {
    page?: number
    page_size?: number
    status?: string  // "active" | "finished" | "all"
    keyword?: string
  }) => {
    const { data } = await api.get<import('@/types/novel').MyShelfListResponse>('/user/my-shelf', { params })
    return data
  }
}

// 115 远程播放 API
export const remote115Api = {
  getPlayOptions: async (workId: number) => {
    const { data } = await api.get<import('@/types/remote115').Remote115VideoPlayOptions>(`/api/remote/115/videos/${workId}/play-options`)
    return data
  },
  updateProgress: async (workId: number, payload: { position: number; finished: boolean }) => {
    const { data } = await api.post(`/api/remote/115/videos/${workId}/progress`, payload)
    return data
  }
}

// 电视墙 API
export const playerWallApi = {
  getList: async (params: {
    page: number
    page_size: number
    keyword?: string
    has_115?: number
    media_type?: string
  }) => {
    const { data } = await api.get<{
      items: import('@/types/playerWall').PlayerWallItem[]
      total: number
      page: number
      page_size: number
      total_pages: number
    }>('/api/player/wall/list', { params })
    return data
  }
}

// 视频播放进度 API
export const videoProgressApi = {
  getProgress: async (workId: number) => {
    // @ts-ignore - videoProgress types are unrelated to notification center
    const { data } = await api.get<import('@/types/videoProgress').VideoProgressResponse>(`/api/video-progress/${workId}`)
    return data
  },
  
  updateProgress: async (workId: number, payload: {
    position_seconds: number
    duration_seconds?: number
    progress_percent: number
    is_finished: boolean
    source_type?: number
    last_play_url?: string
    tmdb_id?: number
  }) => {
    // @ts-ignore - videoProgress types are unrelated to notification center
    const { data } = await api.post<import('@/types/videoProgress').VideoProgressResponse>(`/api/video-progress/${workId}`, payload)
    return data
  },
  
  deleteProgress: async (workId: number) => {
    const { data } = await api.delete(`/api/video-progress/${workId}`)
    return data
  },
  
  listProgress: async (params?: {
    page?: number
    page_size?: number
    only_finished?: boolean
  }) => {
    // @ts-ignore - videoProgress types are unrelated to notification center
    const { data } = await api.get<import('@/types/videoProgress').VideoProgressListResponse>('/api/video-progress/', { params })
    return data
  }
}

// 漫画源管理 API
export const mangaSourceAdminApi = {
  list: async (params?: { keyword?: string; page?: number; page_size?: number }) => {
    const { data } = await api.get<{
      items: import('@/types/mangaSource').MangaSource[]
      total: number
      page: number
      page_size: number
      total_pages: number
    }>('/api/dev/manga/sources', { params })
    return data
  },
  create: async (payload: import('@/types/mangaSource').MangaSourceCreatePayload) => {
    const { data } = await api.post<import('@/types/mangaSource').MangaSource>('/api/dev/manga/sources', payload)
    return data
  },
  update: async (id: number, payload: import('@/types/mangaSource').MangaSourceUpdatePayload) => {
    const { data } = await api.put<import('@/types/mangaSource').MangaSource>(`/api/dev/manga/sources/${id}`, payload)
    return data
  },
  remove: async (id: number) => {
    const { data } = await api.delete(`/api/dev/manga/sources/${id}`)
    return data
  },
  ping: async (id: number) => {
    const { data } = await api.post<{ ok: boolean; message?: string }>(`/api/dev/manga/sources/${id}/ping`, {})
    return data
  }
}

// 远程漫画浏览 API
export const mangaRemoteApi = {
  listSources: async (params?: { only_enabled?: boolean }) => {
    const { data } = await api.get<import('@/types/mangaSource').RemoteMangaSourceInfo[]>('/api/manga/remote/sources', { params })
    return data
  },
  listLibraries: async (source_id: number) => {
    const { data } = await api.get<import('@/types/mangaSource').MangaLibraryInfo[]>(
      `/api/manga/remote/sources/${source_id}/libraries`
    )
    return data
  },
  search: async (params: {
    q: string
    source_id?: number
    page?: number
    page_size?: number
  }) => {
    const { data } = await api.get<import('@/types/mangaSource').RemoteMangaSearchResult>('/api/manga/remote/search', { params })
    return data
  },
  getSeriesDetail: async (source_id: number, remote_series_id: string) => {
    const { data } = await api.get<import('@/types/mangaSource').RemoteMangaSeries>(
      `/api/manga/remote/series/${source_id}/${encodeURIComponent(remote_series_id)}`
    )
    return data
  },
  getChapters: async (source_id: number, remote_series_id: string) => {
    const { data } = await api.get<import('@/types/mangaSource').RemoteMangaChapter[]>(
      `/api/manga/remote/series/${source_id}/${encodeURIComponent(remote_series_id)}/chapters`
    )
    return data
  },
  browseByLibrary: async (params: {
    source_id: number
    library_id: string
    page?: number
    page_size?: number
  }) => {
    const { source_id, library_id, page, page_size } = params
    const { data } = await api.get<import('@/types/mangaSource').RemoteMangaSearchResult>(
      `/api/manga/remote/sources/${source_id}/libraries/${encodeURIComponent(library_id)}/series`,
      { params: { page, page_size } }
    )
    return data
  },
  // 聚合搜索
  aggregatedSearch: async (params: {
    q: string
    sources?: string // 逗号分隔的源ID列表
    page?: number
    page_size?: number
    timeout_per_source?: number
  }) => {
    const { data } = await api.get<import('@/types/mangaSource').AggregatedSearchResult>('/api/manga/remote/aggregated-search', { params })
    return data
  },
  // 获取外部阅读URL
  getExternalUrl: async (source_id: number, remote_series_id: string) => {
    const { data } = await api.get<{ external_url: string }>(
      `/api/manga/remote/series/${source_id}/${encodeURIComponent(remote_series_id)}/external-url`
    )
    return data
  }
}

// 本地漫画库 API
export const mangaLocalApi = {
  listSeries: async (params?: {
    keyword?: string
    source_id?: number
    favorite?: boolean
    page?: number
    page_size?: number
  }) => {
    const { data } = await api.get<{
      items: import('@/types/mangaLocal').MangaSeriesLocal[]
      total: number
      page: number
      page_size: number
      total_pages: number
    }>('/api/manga/local/series', { params })
    return data
  },
  getSeriesDetail: async (series_id: number) => {
    const { data } = await api.get<{
      series: import('@/types/mangaLocal').MangaSeriesLocal
      chapters: import('@/types/mangaLocal').MangaChapterLocal[]
    }>(`/api/manga/local/series/${series_id}`)
    return data
  },
  importFromRemote: async (payload: {
    source_id: number
    remote_series_id: string
    mode: 'ALL' | 'LATEST_N' | 'SELECTED'
    latest_n?: number
    chapter_ids?: string[]
  }) => {
    const { data } = await api.post<{
      series: import('@/types/mangaLocal').MangaSeriesLocal
      chapters: import('@/types/mangaLocal').MangaChapterLocal[]
    }>('/api/manga/local/import', payload)
    return data
  },
  downloadChapter: async (chapter_id: number) => {
    const { data } = await api.post<import('@/types/mangaLocal').MangaChapterLocal>(
      `/api/manga/local/chapters/${chapter_id}/download`,
      {}
    )
    return data
  },
  downloadSeries: async (series_id: number, payload?: {
    mode?: 'ALL' | 'ONLY_PENDING' | 'LATEST_N'
    latest_n?: number
  }) => {
    const { data } = await api.post(`/api/manga/local/series/${series_id}/download`, payload ?? {})
    return data
  },
  getChapterPages: async (chapter_id: number) => {
    const { data } = await api.get<import('@/types/mangaLocal').LocalMangaPage[]>(
      `/api/manga/local/chapters/${chapter_id}/pages`
    )
    return data
  },
  syncSeries: async (series_id: number, payload?: { download_new?: boolean }) => {
    const { data } = await api.post<{
      series_id: number
      series_title: string
      new_chapters: number
      total_chapters: number
      last_sync_at: string | null
      status: string
    }>(
      `/api/manga/local/series/${series_id}/sync`,
      payload ?? {}
    )
    return data
  },
  getSeriesSyncStatus: async (series_id: number) => {
    const { data } = await api.get<{
      series_id: number
      series_title: string
      last_sync_at: string | null
      total_chapters: number
      downloaded_chapters: number
      new_chapter_count: number
      pending_chapters: number
      has_updates: boolean
    }>(`/api/manga/local/series/${series_id}/sync/status`)
    return data
  },
  syncSeriesRemote: async (series_id: number) => {
    const { data } = await api.post<{
      series_id: number
      source_id: number | null
      remote_series_id: string | null
      new_chapters_count: number
      had_error: boolean
      error_message: string | null
    }>(`/api/manga/local/series/${series_id}/sync_remote`)
    return data
  },
  syncFavorites: async (payload?: { download_new?: boolean; limit?: number }) => {
    const { data } = await api.post<{
      success: boolean
      processed_series: number
      total_new_chapters: number
      details: any[]
      message: string
    }>(
      '/api/manga/local/sync/favorites',
      payload ?? {}
    )
    return data
  },
  getFavoritesSyncOverview: async () => {
    const { data } = await api.get<{
      total_favorites: number
      series_with_updates: number
      total_new_chapters: number
      recent_sync_count: number
      last_sync_time: string | null
    }>('/api/manga/local/sync/favorites/overview')
    return data
  }
}

// 漫画阅读进度 API
export const mangaProgressApi = {
  getSeriesProgress: async (series_id: number) => {
    const { data } = await api.get<import('@/types/mangaLocal').MangaReadingProgress | null>(
      `/api/manga/local/progress/series/${series_id}`
    )
    return data
  },
  upsertSeriesProgress: async (payload: {
    series_id: number
    chapter_id?: number | null
    last_page_index: number
    total_pages?: number | null
    is_finished?: boolean
  }) => {
    const { series_id, ...data } = payload
    const { data: result } = await api.post<import('@/types/mangaLocal').MangaReadingProgress>(
      `/api/manga/local/progress/series/${series_id}`,
      { series_id, ...data }
    )
    return result
  },
  listHistory: async (params?: { limit?: number; offset?: number }) => {
    const { data } = await api.get<import('@/types/mangaLocal').MangaReadingHistoryItem[]>(
      '/api/manga/local/progress/history',
      { params }
    )
    return data
  }
}

// 阅读中心 API
export const readingHubApi = {
  listOngoing: async (params?: { limit_per_type?: number }) => {
    const { data } = await api.get<import('@/types/readingHub').ReadingOngoingItem[]>(
      '/api/reading/ongoing',
      { params }
    )
    return data
  },
  listHistory: async (params?: {
    limit?: number
    offset?: number
    media_type?: import('@/types/readingHub').ReadingMediaType
  }) => {
    const { data } = await api.get<import('@/types/readingHub').ReadingHistoryItem[]>(
      '/api/reading/history',
      { params }
    )
    return data
  },
  getStats: async () => {
    const { data } = await api.get<import('@/types/readingHub').ReadingStats>(
      '/api/reading/stats'
    )
    return data
  },
  getRecentActivity: async (params?: { limit?: number }) => {
    const { data } = await api.get<import('@/types/readingHub').ReadingActivityItem[]>(
      '/api/reading/recent_activity',
      { params }
    )
    return data
  }
}

// 阅读收藏 API
export const readingFavoriteApi = {
  addFavorite: async (payload: {
    media_type: import('@/types/readingHub').ReadingMediaType
    target_id: number
  }) => {
    const { data } = await api.post<import('@/types/readingFavorite').UserFavoriteMedia>(
      '/api/reading/favorites',
      payload
    )
    return data
  },

  removeFavorite: async (payload: {
    media_type: import('@/types/readingHub').ReadingMediaType
    target_id: number
  }) => {
    const { data } = await api.delete<import('@/types/readingFavorite').FavoriteOperationResponse>(
      '/api/reading/favorites',
      { 
        params: {
          media_type: payload.media_type,
          target_id: payload.target_id
        }
      }
    )
    return data
  },

  checkFavorite: async (params: {
    media_type: import('@/types/readingHub').ReadingMediaType
    target_id: number
  }) => {
    const { data } = await api.get<import('@/types/readingFavorite').FavoriteCheckResponse>(
      '/api/reading/favorites/exists',
      { params }
    )
    return data
  },

  listFavorites: async (params?: {
    media_type?: import('@/types/readingHub').ReadingMediaType
    limit?: number
    offset?: number
  }) => {
    const { data } = await api.get<import('@/types/readingFavorite').ReadingShelfItem[]>(
      '/api/reading/favorites',
      { params }
    )
    return data
  }
}

// 漫画追更 API
export const mangaFollowApi = {
  listFollowing: async (params?: { only_unread?: boolean; page?: number; page_size?: number }) => {
    const { data } = await api.get<{
      items: any[]
      total: number
      page: number
      page_size: number
    }>('/api/manga/follow', { params })
    return data
  },

  followSeries: async (seriesId: string) => {
    const { data } = await api.post(`/api/manga/follow/${seriesId}`)
    return data
  },

  unfollowSeries: async (seriesId: string) => {
    const { data } = await api.delete(`/api/manga/follow/${seriesId}`)
    return data
  },

  markSeriesRead: async (seriesId: string) => {
    const { data } = await api.post(`/api/manga/follow/${seriesId}/mark-read`)
    return data
  },

  // 关注外部源漫画系列（不下载章节）
  followRemoteSeries: async (payload: {
    source_id: number
    remote_series_id: string
  }) => {
    const { data } = await api.post('/api/manga/local/remote/follow', payload)
    return data
  }
}

// 音乐库 API
export const musicLibraryApi = {
  // 获取专辑列表
  listAlbums: async (params?: { keyword?: string; artist?: string; page?: number; page_size?: number }) => {
    const { data } = await api.get<{
      success: boolean
      data: import('@/types/music').MusicListResponse
    }>('/api/music/library/albums', { params })
    return data.data
  },

  // 获取专辑详情
  getAlbumDetail: async (albumId: number) => {
    const { data } = await api.get<{
      success: boolean
      data: import('@/types/music').MusicAlbumDetail
    }>(`/api/music/library/albums/${albumId}`)
    return data.data
  },

  // 获取艺术家列表
  listArtists: async (params?: { keyword?: string; page?: number; page_size?: number }) => {
    const { data } = await api.get<{
      success: boolean
      data: import('@/types/music').MusicArtistListResponse
    }>('/api/music/library/artists', { params })
    return data.data
  },

  // 获取曲目列表
  listTracks: async (params?: { keyword?: string; artist?: string; album?: string; page?: number; page_size?: number }) => {
    const { data } = await api.get<{
      success: boolean
      data: import('@/types/music').MusicTrackListResponse
    }>('/api/music/library/tracks', { params })
    return data.data
  },

  // 获取音乐库统计
  getStats: async () => {
    const { data } = await api.get<{
      success: boolean
      data: import('@/types/music').MusicStats
    }>('/api/music/library/stats')
    return data.data
  },

  // 获取音频流 URL
  getStreamUrl: (fileId: number) => {
    return `${api.defaults.baseURL}/api/music/library/stream/${fileId}`
  }
}

// 音乐榜单管理 API (Dev)
export const musicChartAdminApi = {
  // 获取榜单源列表
  listSources: async (params?: { keyword?: string; is_enabled?: boolean; page?: number; page_size?: number }) => {
    const { data } = await api.get<{
      success: boolean
      data: import('@/types/music').MusicChartSourceListResponse
    }>('/api/dev/music/charts/sources', { params })
    return data.data
  },

  // 获取榜单列表
  listCharts: async (params?: { source_id?: number; keyword?: string; is_enabled?: boolean; page?: number; page_size?: number }) => {
    const { data } = await api.get<{
      success: boolean
      data: import('@/types/music').MusicChartListResponse
    }>('/api/dev/music/charts/list', { params })
    return data.data
  },

  // 获取榜单详情
  getChartDetail: async (chartId: number, includeItems: boolean = true) => {
    const { data } = await api.get<{
      success: boolean
      data: import('@/types/music').MusicChartDetail
    }>(`/api/dev/music/charts/${chartId}`, { params: { include_items: includeItems } })
    return data.data
  },

  // 获取榜单条目
  getChartItems: async (chartId: number, params?: { keyword?: string; page?: number; page_size?: number }) => {
    const { data } = await api.get<{
      success: boolean
      data: import('@/types/music').MusicChartItemListResponse
    }>(`/api/dev/music/charts/${chartId}/items`, { params })
    return data.data
  },

  // 手动同步榜单
  syncChart: async (chartId: number) => {
    const { data } = await api.post<{
      success: boolean
      data: { new_count: number; updated_count: number }
      message: string
    }>(`/api/dev/music/charts/${chartId}/sync`)
    return data
  }
}

// 音乐订阅 API
export const musicSubscriptionApi = {
  // 获取我的订阅列表
  listSubscriptions: async (params?: { status?: string; page?: number; page_size?: number }) => {
    const { data } = await api.get<{
      success: boolean
      data: import('@/types/music').UserMusicSubscriptionListResponse
    }>('/api/music/subscriptions', { params })
    return data.data
  },

  // 创建订阅
  createSubscription: async (payload: import('@/types/music').UserMusicSubscriptionCreate) => {
    const { data } = await api.post<{
      success: boolean
      data: import('@/types/music').UserMusicSubscription
      message: string
    }>('/api/music/subscriptions', payload)
    return data
  },

  // 更新订阅
  updateSubscription: async (subscriptionId: number, payload: import('@/types/music').UserMusicSubscriptionUpdate) => {
    const { data } = await api.put<{
      success: boolean
      data: import('@/types/music').UserMusicSubscription
      message: string
    }>(`/api/music/subscriptions/${subscriptionId}`, payload)
    return data
  },

  // 删除订阅
  deleteSubscription: async (subscriptionId: number) => {
    const { data } = await api.delete<{
      success: boolean
      message: string
    }>(`/api/music/subscriptions/${subscriptionId}`)
    return data
  },

  // 暂停订阅
  pauseSubscription: async (subscriptionId: number) => {
    const { data } = await api.post<{
      success: boolean
      message: string
    }>(`/api/music/subscriptions/${subscriptionId}/pause`)
    return data
  },

  // 恢复订阅
  resumeSubscription: async (subscriptionId: number) => {
    const { data } = await api.post<{
      success: boolean
      message: string
    }>(`/api/music/subscriptions/${subscriptionId}/resume`)
    return data
  },

  // 手动运行一次
  runOnce: async (subscriptionId: number) => {
    const { data } = await api.post<{
      success: boolean
      data: import('@/types/music').SubscriptionRunResult
      message: string
    }>(`/api/music/subscriptions/${subscriptionId}/run_once`)
    return data
  },

  // 获取我的下载任务
  listDownloadJobs: async (params?: { status?: string; subscription_id?: number; page?: number; page_size?: number }) => {
    const { data } = await api.get<{
      success: boolean
      data: import('@/types/music').MusicDownloadJobListResponse
    }>('/api/music/subscriptions/jobs', { params })
    return data.data
  },

  // Phase 3: 重试失败的任务
  retryJob: async (jobId: number) => {
    const { data } = await api.post<{
      success: boolean
      message: string
    }>(`/api/music/subscriptions/jobs/${jobId}/retry`)
    return data
  },

  // Phase 3: 跳过任务
  skipJob: async (jobId: number) => {
    const { data } = await api.post<{
      success: boolean
      message: string
    }>(`/api/music/subscriptions/jobs/${jobId}/skip`)
    return data
  },

  // Phase 3: 获取订阅覆盖统计
  getCoverage: async (subscriptionId: number) => {
    const { data } = await api.get<{
      success: boolean
      data: import('@/types/music').SubscriptionCoverageStats
    }>(`/api/music/subscriptions/${subscriptionId}/coverage`)
    return data.data
  }
}

// 首页仪表盘 API
export const homeApi = {
  getDashboard: async () => {
    const { data } = await api.get<import('@/types/home').HomeDashboardResponse>(
      '/api/home/dashboard'
    )
    return data
  }
}

// 系统概览 Dashboard API
export const dashboardApi = {
  getDashboard: async () => {
    const { data } = await api.get<{ success: boolean; data: import('@/types/dashboard').DashboardData }>(
      '/api/dashboard/'
    )
    return data
  }
}

// 任务中心 API
export const taskCenterApi = {
  list: async (params?: {
    media_type?: string
    kind?: string
    status?: string
    page?: number
    page_size?: number
  }) => {
    const { data } = await api.get<import('@/types/taskCenter').TaskCenterListResponse>(
      '/api/task_center/tasks',
      { params }
    )
    return data
  }
}

// 全局搜索 API
export const globalSearchApi = {
  search: async (q: string, limitPerType?: number) => {
    const { data } = await api.get<import('@/types/globalSearch').GlobalSearchResponse>(
      '/api/search/global',
      { params: { q, limit_per_type: limitPerType } }
    )
    return data
  }
}

// 系统运维 API
export const adminApi = {
  getDashboard: async () => {
    const { data } = await api.get<import('@/types/admin').AdminDashboardResponse>(
      '/api/admin/dashboard'
    )
    return data
  },
  getRunners: async () => {
    const { data } = await api.get<import('@/types/admin').RunnerStatus[]>(
      '/api/admin/runners'
    )
    return data
  },
  getExternalSources: async () => {
    const { data } = await api.get<import('@/types/admin').ExternalSourceStatus[]>(
      '/api/admin/external_sources'
    )
    return data
  },
  getStorage: async () => {
    const { data } = await api.get<import('@/types/admin').StorageInfo[]>(
      '/api/admin/storage'
    )
    return data
  }
}

// Onboarding API
export const onboardingApi = {
  getStatus: async () => {
    const { data } = await api.get<import('@/types/onboarding').OnboardingStatus>(
      '/api/admin/onboarding/status'
    )
    return data
  },
  complete: async () => {
    const { data } = await api.post('/api/admin/onboarding/complete')
    return data
  },
  skip: async () => {
    const { data } = await api.post('/api/admin/onboarding/skip')
    return data
  }
}

// 配置管理 API
export const configAdminApi = {
  getSchema: async () => {
    const { data } = await api.get('/api/admin/config/schema')
    return data
  },
  validate: async (config: Record<string, unknown>) => {
    const { data } = await api.post('/api/admin/config/validate', config)
    return data
  },
  getEffective: async () => {
    const { data } = await api.get('/api/admin/config/effective')
    return data
  }
}

// 应用信息 API
export const appApi = {
  getVersion: async () => {
    const { data } = await api.get<import('@/types/app').AppVersionInfo>('/api/version')
    return data
  }
}

// 系统健康检查 API
export const systemHealthApi = {
  getSummary: async () => {
    const { data } = await api.get<import('@/types/systemHealth').SystemHealthSummary>('/api/admin/health/summary')
    return data
  },
  runOnce: async () => {
    const { data } = await api.post<import('@/types/systemHealth').SystemHealthSummary>('/api/admin/health/run_once', {})
    return data
  },
  getReport: async (format: 'json' | 'markdown' = 'json') => {
    const { data } = await api.get('/api/admin/health/report', { params: { format } })
    return data
  },
  getRunnerStats: async () => {
    const { data } = await api.get('/api/admin/health/runners')
    return data
  },
}

// Telegram 绑定 API
export const telegramBindingApi = {
  getStatus: async () => {
    const { data } = await api.get<{ is_bound: boolean; binding?: any }>('/api/notify/telegram/status')
    return data
  },
  generateCode: async () => {
    const { data } = await api.post<{ code: string; expires_in: number }>('/api/notify/telegram/binding_code')
    return data
  },
  unbind: async () => {
    await api.delete('/api/notify/telegram/unbind')
  },
}

// 用户通知渠道 API
export const userNotifyChannelApi = {
  list: async () => {
    const { data } = await api.get<import('@/types/userNotifyChannel').UserNotifyChannel[]>('/api/notify/channels')
    return data
  },
  get: async (id: number) => {
    const { data } = await api.get<import('@/types/userNotifyChannel').UserNotifyChannel>(`/api/notify/channels/${id}`)
    return data
  },
  create: async (payload: import('@/types/userNotifyChannel').UserNotifyChannelCreate) => {
    const { data } = await api.post<import('@/types/userNotifyChannel').UserNotifyChannel>('/api/notify/channels', payload)
    return data
  },
  update: async (id: number, payload: import('@/types/userNotifyChannel').UserNotifyChannelUpdate) => {
    const { data } = await api.put<import('@/types/userNotifyChannel').UserNotifyChannel>(`/api/notify/channels/${id}`, payload)
    return data
  },
  remove: async (id: number) => {
    await api.delete(`/api/notify/channels/${id}`)
  },
  test: async (id: number) => {
    const { data } = await api.post<import('@/types/userNotifyChannel').UserNotifyChannelTestResponse>(`/api/notify/channels/${id}/test`)
    return data
  },
}

// 告警渠道 API
export const alertChannelApi = {
  list: async () => {
    const { data } = await api.get<import('@/types/alertChannel').AlertChannel[]>('/api/admin/alert_channels')
    return data
  },
  get: async (id: number) => {
    const { data } = await api.get<import('@/types/alertChannel').AlertChannel>(`/api/admin/alert_channels/${id}`)
    return data
  },
  create: async (payload: import('@/types/alertChannel').AlertChannelCreate) => {
    const { data } = await api.post<import('@/types/alertChannel').AlertChannel>('/api/admin/alert_channels', payload)
    return data
  },
  update: async (id: number, payload: import('@/types/alertChannel').AlertChannelUpdate) => {
    const { data } = await api.put<import('@/types/alertChannel').AlertChannel>(`/api/admin/alert_channels/${id}`, payload)
    return data
  },
  remove: async (id: number) => {
    await api.delete(`/api/admin/alert_channels/${id}`)
  },
  test: async (id: number, message?: string) => {
    const { data } = await api.post(`/api/admin/alert_channels/${id}/test`, { message })
    return data
  },
}

// 通知偏好 API
export const notifyPreferenceApi = {
  getMatrix: async () => {
    const { data } = await api.get<import('@/types/notifyPreferences').UserNotifyPreferenceMatrix>('/api/notify/preferences/matrix')
    return data
  },
  upsertPreference: async (payload: import('@/types/notifyPreferences').UserNotifyPreferenceUpsert) => {
    const { data } = await api.put<import('@/types/notifyPreferences').UserNotifyPreference>('/api/notify/preferences', payload)
    return data
  },
  deletePreference: async (id: number) => {
    await api.delete(`/api/notify/preferences/${id}`)
  },
  getSnooze: async () => {
    const { data } = await api.get<import('@/types/notifyPreferences').UserNotifySnooze | null>('/api/notify/preferences/snooze')
    return data
  },
  updateSnooze: async (payload: import('@/types/notifyPreferences').UserNotifySnoozeUpdate) => {
    const { data } = await api.put<import('@/types/notifyPreferences').UserNotifySnooze>('/api/notify/preferences/snooze', payload)
    return data
  },
  quickSnooze: async (payload: import('@/types/notifyPreferences').SnoozeRequest) => {
    const { data } = await api.post<import('@/types/notifyPreferences').UserNotifySnooze>('/api/notify/preferences/snooze/quick', payload)
    return data
  },
  clearSnooze: async () => {
    await api.delete('/api/notify/preferences/snooze')
  },
  muteType: async (payload: import('@/types/notifyPreferences').MuteNotificationTypeRequest) => {
    const { data } = await api.post<{ success: boolean; preference_id: number }>('/api/notify/preferences/mute-type', payload)
    return data
  },
  unmuteType: async (payload: import('@/types/notifyPreferences').MuteNotificationTypeRequest) => {
    const { data } = await api.post<{ success: boolean }>('/api/notify/preferences/unmute-type', payload)
    return data
  },
}

// ============== 自检 API ==============
export const selfCheckApi = {
  run: async () => {
    const { data } = await api.post<import('@/types/selfCheck').SelfCheckRunResult>('/api/admin/self_check/run')
    return data
  },
  getSummary: async () => {
    const { data } = await api.get<{ message: string; groups: string[] }>('/api/admin/self_check/summary')
    return data
  },
}

// ============== 插件管理 API ==============
export const pluginAdminApi = {
  list: async () => {
    const { data } = await api.get<import('@/types/plugin').PluginInfo[]>('/api/dev/plugins')
    return data
  },
  scan: async () => {
    const { data } = await api.post<import('@/types/plugin').PluginScanResult>('/api/dev/plugins/scan', {})
    return data
  },
  updateStatus: async (id: number, status: 'ENABLED' | 'DISABLED') => {
    const { data } = await api.put<import('@/types/plugin').PluginInfo>(`/api/dev/plugins/${id}/status`, { status })
    return data
  },
  get: async (id: number) => {
    const { data } = await api.get<import('@/types/plugin').PluginInfo>(`/api/dev/plugins/${id}`)
    return data
  },
  listWorkflows: async () => {
    const { data } = await api.get<import('@/types/plugin').WorkflowExtensionInfo[]>('/api/dev/workflows')
    return data
  },
  runWorkflow: async (id: string, payload?: any) => {
    const { data } = await api.post<import('@/types/plugin').WorkflowRunResult>(
      `/api/dev/workflows/${encodeURIComponent(id)}/run`,
      { payload }
    )
    return data
  },
}

// ============== 插件配置 API（PLUGIN-UX-3） ==============
export const pluginConfigApi = {
  get: async (pluginId: string) => {
    const { data } = await api.get<{ success: boolean; data: import('@/types/plugin').PluginConfig }>(
      `/api/dev/plugins/${encodeURIComponent(pluginId)}/config`
    )
    return data.data
  },
  update: async (pluginId: string, config: Record<string, any>) => {
    const { data } = await api.put<{ success: boolean; data: import('@/types/plugin').PluginConfig }>(
      `/api/dev/plugins/${encodeURIComponent(pluginId)}/config`,
      { config }
    )
    return data.data
  },
}

// ============== 插件 Dashboard API（PLUGIN-UX-3） ==============
export const pluginDashboardApi = {
  get: async (pluginId: string) => {
    const { data } = await api.get<{ success: boolean; data: import('@/types/plugin').PluginDashboardSchema | null }>(
      `/api/plugin_panels/dashboard/${encodeURIComponent(pluginId)}`
    )
    return data.data
  },
}

// ============== 插件面板 API ==============
export const pluginPanelApi = {
  listByPlacement: async (placement: import('@/types/pluginPanels').PluginPanelPlacement) => {
    const { data } = await api.get<import('@/types/pluginPanels').PluginPanelWithPlugin[]>(
      '/api/plugin_panels',
      { params: { placement } }
    )
    return data
  },
  getPanelData: async (pluginId: string, panelId: string) => {
    const { data } = await api.get<import('@/types/pluginPanels').PluginPanelDataResponse>(
      `/api/plugin_panels/${encodeURIComponent(pluginId)}/${encodeURIComponent(panelId)}/data`
    )
    return data
  },
}

// ============== Plugin Hub API ==============
export const pluginHubApi = {
  /** 获取 Plugin Hub 配置（PLUGIN-HUB-3） */
  getConfig: async () => {
    const { data } = await api.get<import('@/types/pluginHub').PluginHubConfigResponse>(
      '/api/dev/plugin_hub/config'
    )
    return data
  },
  
  // ============== Hub 源管理（PLUGIN-HUB-4） ==============
  
  /** 获取 Hub 源列表 */
  getHubs: async () => {
    const { data } = await api.get<import('@/types/pluginHub').PluginHubSource[]>(
      '/api/dev/plugin_hub/hubs'
    )
    return data
  },
  
  /** 更新 Hub 源列表 */
  updateHubs: async (sources: import('@/types/pluginHub').PluginHubSource[]) => {
    const { data } = await api.put<import('@/types/pluginHub').PluginHubSource[]>(
      '/api/dev/plugin_hub/hubs',
      { sources }
    )
    return data
  },
  
  /** 获取 Plugin Hub 插件列表（多 Hub 聚合，PLUGIN-HUB-4） */
  list: async (params?: { 
    force_refresh?: boolean
    channel?: 'official' | 'community'
    include_community?: boolean
    hub_id?: string
    installed_only?: boolean
    not_installed_only?: boolean
  }) => {
    const { data } = await api.get<import('@/types/pluginHub').RemotePluginWithLocalStatus[]>(
      '/api/dev/plugin_hub',
      { params }
    )
    return data
  },
  
  /** 获取 Plugin Hub 索引（保留兼容） */
  getIndex: async (params?: { 
    force_refresh?: boolean
    channel?: 'official' | 'community'
    include_community?: boolean 
  }) => {
    const plugins = await pluginHubApi.list(params)
    // 返回兼容格式
    return {
      hub_name: 'Plugin Hub',
      hub_version: 1,
      plugins,
      fetched_at: null,
      cached: false,
    } as import('@/types/pluginHub').PluginHubIndexResponse
  },
  
  /** 获取单个插件详情 */
  getDetail: async (pluginId: string) => {
    const { data } = await api.get<import('@/types/pluginHub').RemotePluginWithLocalStatus>(
      `/api/dev/plugin_hub/${encodeURIComponent(pluginId)}`
    )
    return data
  },
  /** 获取插件 README */
  getReadme: async (pluginId: string) => {
    const { data } = await api.get<import('@/types/pluginHub').PluginReadmeResponse>(
      `/api/dev/plugin_hub/${encodeURIComponent(pluginId)}/readme`
    )
    return data
  },
  /** 获取安装指南 */
  getInstallGuide: async (pluginId: string) => {
    const { data } = await api.get<import('@/types/pluginHub').PluginInstallGuideResponse>(
      `/api/dev/plugin_hub/${encodeURIComponent(pluginId)}/install_guide`
    )
    return data
  },
  
  // ============== PLUGIN-HUB-2：一键操作 ==============
  
  /** 一键安装插件 */
  install: async (pluginId: string) => {
    const { data } = await api.post<import('@/types/pluginHub').RemotePluginWithLocalStatus>(
      `/api/dev/plugin_hub/${encodeURIComponent(pluginId)}/install`
    )
    return data
  },
  
  /** 一键更新插件 */
  update: async (pluginId: string) => {
    const { data } = await api.post<import('@/types/pluginHub').RemotePluginWithLocalStatus>(
      `/api/dev/plugin_hub/${encodeURIComponent(pluginId)}/update`
    )
    return data
  },
  
  /** 卸载插件 */
  uninstall: async (pluginId: string) => {
    const { data } = await api.post<{ success: boolean; plugin_id: string; message: string }>(
      `/api/dev/plugin_hub/${encodeURIComponent(pluginId)}/uninstall`
    )
    return data
  },
}

// 发现页 API (0.0.2 -> 0.0.3 多源版本)
export const discoverApi = {
  // 获取发现页首页内容（TMDB/豆瓣/Bangumi 热门聚合）
  getHome: () => api.get('/discover/home'),
  
  // 获取热门内容
  getTrending: (mediaType: 'movie' | 'tv' | 'all', timeWindow: 'day' | 'week' = 'week') => 
    api.get(`/discover/trending/${mediaType}`, { params: { time_window: timeWindow } })
}

// 音乐首页 API (0.0.3)
export const musicHomeApi = {
  // 获取音乐首页内容（榜单聚合）
  getHome: () => api.get('/music/home'),
}
