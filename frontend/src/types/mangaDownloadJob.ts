/**
 * 漫画下载任务相关类型定义
 */

export type MangaDownloadJobStatus = 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED'

export interface MangaDownloadJob {
  id: number
  user_id: number
  source_id: number
  source_name: string
  remote_series_id: string
  remote_series_title: string
  target_series_id?: number
  mode: 'CHAPTER' | 'SERIES'
  status: MangaDownloadJobStatus
  error_message?: string
  created_at: string
  updated_at: string
  started_at?: string
  completed_at?: string
  progress?: {
    current: number
    total: number
    percentage: number
  }
}

export interface MangaDownloadJobSummary {
  total: number
  pending: number
  running: number
  success: number
  failed: number
}

export interface CreateDownloadJobRequest {
  source_id: number
  remote_series_id: string
  mode: 'CHAPTER' | 'SERIES'
  chapter_id?: number
  latest_n?: number
}

export interface MangaDownloadJobListResponse {
  items: MangaDownloadJob[]
  total: number
  page: number
  page_size: number
  has_next: boolean
  has_prev: boolean
}
