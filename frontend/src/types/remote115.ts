/**
 * 115 远程播放类型定义
 */

export interface Remote115VideoQuality {
  id: string
  title: string
  height: number
  width: number
  url: string
}

export interface Remote115Subtitle {
  sid: string
  language: string
  title: string
  url: string
  is_default: boolean
}

export interface Remote115VideoProgress {
  position: number
}

export interface Remote115VideoPlayOptions {
  work_id: number
  pick_code: string
  file_name: string
  duration: number
  qualities: Remote115VideoQuality[]
  subtitles: Remote115Subtitle[]
  progress?: Remote115VideoProgress
}

