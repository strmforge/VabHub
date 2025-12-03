/**
 * 媒体播放行为统一 Hook
 * 
 * 统一处理电视墙卡片、MediaDetail页面的播放按钮行为
 * 避免各组件重复实现相同的播放逻辑
 */

import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { videoProgressApi } from '@/services/api'
import type { PlayerWallSourceInfo, PlayerWallStatusInfo } from '@/types/playerWall'
import type { VideoProgressResponse, VideoProgressInfo } from '@/types/videoProgress'
import { formatVideoProgress } from '@/types/videoProgress'

export interface PlayActionOptions {
  workId: number
  source: PlayerWallSourceInfo
  status?: PlayerWallStatusInfo
  preferredSource?: '115' | 'local' | 'auto'
}

export function useMediaPlayActions() {
  const router = useRouter()
  const toast = useToast()
  
  // 进度缓存状态
  const progressCache = ref<Map<number, VideoProgressResponse>>(new Map())
  const loadingProgress = ref<Set<number>>(new Set())

  /**
   * 获取作品播放进度
   */
  const getProgress = async (workId: number): Promise<VideoProgressInfo> => {
    // 检查缓存
    if (progressCache.value.has(workId)) {
      return formatVideoProgress(progressCache.value.get(workId)!)
    }
    
    try {
      loadingProgress.value.add(workId)
      const progress = await videoProgressApi.getProgress(workId)
      
      // 缓存结果
      progressCache.value.set(workId, progress)
      return formatVideoProgress(progress)
    } catch (error) {
      console.error(`获取作品 ${workId} 播放进度失败:`, error)
      // 返回空进度
      return formatVideoProgress({
        work_id: workId,
        position_seconds: 0,
        duration_seconds: undefined,
        progress_percent: 0,
        is_finished: false,
        has_progress: false,
        source_type: undefined,
        last_play_url: undefined,
        tmdb_id: undefined,
        last_played_at: undefined,
        updated_at: new Date().toISOString()
      })
    } finally {
      loadingProgress.value.delete(workId)
    }
  }

  /**
   * 更新作品播放进度
   */
  const updateProgress = async (workId: number, payload: {
    position_seconds: number
    duration_seconds?: number
    progress_percent: number
    is_finished: boolean
    source_type?: number
    last_play_url?: string
    tmdb_id?: number
  }): Promise<VideoProgressResponse> => {
    try {
      const updatedProgress = await videoProgressApi.updateProgress(workId, payload)
      
      // 更新缓存
      progressCache.value.set(workId, updatedProgress)
      return updatedProgress
    } catch (error) {
      console.error(`更新作品 ${workId} 播放进度失败:`, error)
      throw error
    }
  }

  /**
   * 删除作品播放进度
   */
  const deleteProgress = async (workId: number): Promise<void> => {
    try {
      await videoProgressApi.deleteProgress(workId)
      
      // 清除缓存
      progressCache.value.delete(workId)
    } catch (error) {
      console.error(`删除作品 ${workId} 播放进度失败:`, error)
      throw error
    }
  }

  /**
   * 清除进度缓存
   */
  const clearProgressCache = (workId?: number) => {
    if (workId) {
      progressCache.value.delete(workId)
    } else {
      progressCache.value.clear()
    }
  }

  /**
   * 跳转到作品详情页
   */
  const openDetail = (workId: number) => {
    router.push({ 
      name: 'WorkDetail', 
      params: { ebookId: workId.toString() }
    })
  }

  /**
   * 跳转到115远程播放页面
   */
  const goRemote115Player = (workId: number) => {
    router.push({ 
      name: 'Remote115Player', 
      params: { workId: workId.toString() }
    })
  }

  /**
   * 打开本地播放器
   * TODO: 实现本地播放逻辑
   */
  const openLocalPlayer = (workId: number) => {
    // 暂时显示提示，后续可以实现本地播放器
    toast.info('本地播放功能开发中')
    // 未来可能的实现：
    // router.push({ name: 'LocalPlayer', params: { workId: workId.toString() } })
    // 或者直接调用本地播放器API
  }

  /**
   * 获取播放按钮文本
   */
  const getPlayButtonText = (source: PlayerWallSourceInfo, preferredSource?: string): string => {
    const has115 = source.has_115
    const hasLocal = source.has_local

    if (preferredSource === 'local' && hasLocal) {
      return '本地播放'
    } else if (preferredSource === '115' && has115) {
      return '115播放'
    } else if (has115 && hasLocal) {
      return '115播放' // 双源时优先显示115
    } else if (has115) {
      return '115播放'
    } else if (hasLocal) {
      return '本地播放'
    } else {
      return '无播放源'
    }
  }

  /**
   * 获取可用的播放源列表
   */
  const getAvailableSources = (source: PlayerWallSourceInfo): Array<{
    type: '115' | 'local'
    label: string
    available: boolean
  }> => {
    return [
      { type: '115', label: '115播放', available: source.has_115 },
      { type: 'local', label: '本地播放', available: source.has_local }
    ].filter(s => s.available)
  }

  /**
   * 执行播放动作
   * 根据可用源和偏好选择最合适的播放方式
   */
  const play = (options: PlayActionOptions) => {
    const { workId, source, status, preferredSource = 'auto' } = options
    
    // 检查是否有可用的播放源
    const availableSources = getAvailableSources(source)
    
    if (availableSources.length === 0) {
      toast.warning('暂无可用的播放源')
      return
    }

    // 根据偏好选择播放源
    let selectedSource: '115' | 'local' | null = null

    if (preferredSource === '115' && source.has_115) {
      selectedSource = '115'
    } else if (preferredSource === 'local' && source.has_local) {
      selectedSource = 'local'
    } else if (preferredSource === 'auto') {
      // 自动选择：优先115，其次本地
      if (source.has_115) {
        selectedSource = '115'
      } else if (source.has_local) {
        selectedSource = 'local'
      }
    }

    if (!selectedSource) {
      toast.warning('没有匹配的播放源')
      return
    }

    // 执行对应的播放动作
    switch (selectedSource) {
      case '115':
        goRemote115Player(workId)
        break
      case 'local':
        openLocalPlayer(workId)
        break
      default:
        toast.warning('不支持的播放源类型')
    }
  }

  /**
   * 检查播放状态
   * 返回播放相关的状态信息
   */
  const getPlayStatus = (source: PlayerWallSourceInfo, status?: PlayerWallStatusInfo) => {
    const availableSources = getAvailableSources(source)
    const hasProgress = status?.has_progress || false
    const isFinished = status?.is_finished || false
    const progressPercent = status?.progress_percent || 0

    return {
      canPlay: availableSources.length > 0,
      availableSources,
      hasProgress,
      isFinished,
      progressPercent,
      playButtonText: getPlayButtonText(source),
      continuePlayText: hasProgress && !isFinished 
        ? `继续播放 · ${Math.round(progressPercent)}%` 
        : null,
      finishedText: isFinished ? '已看完' : null
    }
  }

  return {
    // 核心方法
    openDetail,
    goRemote115Player,
    openLocalPlayer,
    play,
    
    // 进度相关方法
    getProgress,
    updateProgress,
    deleteProgress,
    clearProgressCache,
    
    // 辅助方法
    getPlayButtonText,
    getAvailableSources,
    getPlayStatus,
    
    // 响应式状态
    progressCache: progressCache.value,
    loadingProgress: loadingProgress.value,
    
    // 工具方法
    checkCanPlay: (source: PlayerWallSourceInfo) => getAvailableSources(source).length > 0
  }
}
