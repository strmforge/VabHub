/**
 * 视频播放进度相关类型定义
 */

export interface VideoProgressBase {
  position_seconds: number
  duration_seconds?: number
  progress_percent: number
  is_finished: boolean
  source_type?: number // 1=本地，2=115
  last_play_url?: string
  tmdb_id?: number
}

export interface VideoProgressUpdate extends VideoProgressBase {
  // 继承所有基础字段，用于更新请求
}

export interface VideoProgressResponse extends VideoProgressBase {
  work_id: number
  has_progress: boolean
  last_played_at?: string
  updated_at: string
}

export interface VideoProgressListResponse {
  items: VideoProgressResponse[]
  total: number
  page: number
  page_size: number
}

// 播放源类型枚举
export enum VideoSourceType {
  LOCAL = 1,
  REMOTE_115 = 2
}

// 播放状态枚举
export enum VideoPlayStatus {
  NOT_STARTED = 'not_started',
  PLAYING = 'playing',
  PAUSED = 'paused',
  FINISHED = 'finished'
}

// 进度信息辅助类型
export interface VideoProgressInfo {
  canContinue: boolean
  continueText?: string
  isFinished: boolean
  finishedText?: string
  progressPercent: number
  positionText: string
  durationText: string
}

// 格式化工具函数
export const formatVideoProgress = (progress: VideoProgressResponse): VideoProgressInfo => {
  const { position_seconds, duration_seconds, progress_percent, is_finished, has_progress } = progress
  
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = Math.floor(seconds % 60)
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    } else {
      return `${minutes}:${secs.toString().padStart(2, '0')}`
    }
  }
  
  const positionText = formatTime(position_seconds)
  const durationText = duration_seconds ? formatTime(duration_seconds) : '--:--'
  
  let canContinue = has_progress && !is_finished
  let continueText: string | undefined
  let finishedText: string | undefined
  
  if (canContinue) {
    continueText = `继续播放 · ${Math.round(progress_percent)}%`
  }
  
  if (is_finished) {
    finishedText = '已看完'
  }
  
  return {
    canContinue,
    continueText,
    isFinished: is_finished,
    finishedText,
    progressPercent: progress_percent,
    positionText,
    durationText
  }
}
