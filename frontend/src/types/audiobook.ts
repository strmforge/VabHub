/**
 * 有声书中心类型定义
 */

export interface AudiobookCenterWorkSummary {
  ebook_id: number
  title: string
  original_title?: string | null
  author?: string | null
  series?: string | null
  language?: string | null
  cover_url?: string | null
  updated_at: string
}

export interface AudiobookCenterListeningProgress {
  has_progress: boolean
  is_finished: boolean
  progress_percent: number
  last_played_at?: string | null
  current_file_id?: number | null
  current_chapter_title?: string | null
}

export interface AudiobookCenterReadingProgress {
  has_progress: boolean
  is_finished: boolean
  progress_percent: number
  current_chapter_index?: number | null
  current_chapter_title?: string | null
  last_read_at?: string | null
}

export interface AudiobookCenterTTSStatus {
  has_audiobook: boolean
  has_tts_audiobook: boolean
  last_job_status?: string | null
  last_job_at?: string | null
}

export interface AudiobookCenterItem {
  work: AudiobookCenterWorkSummary
  tts: AudiobookCenterTTSStatus
  listening: AudiobookCenterListeningProgress
  reading: AudiobookCenterReadingProgress
  is_favorite?: boolean
}

export interface AudiobookCenterListResponse {
  items: AudiobookCenterItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * 小说 Inbox 导入日志类型定义
 */

export interface NovelInboxLogItem {
  id: number
  original_path: string
  status: string
  reason?: string | null
  error_message?: string | null
  ebook_id?: number | null
  ebook_title?: string | null
  ebook_author?: string | null
  file_size?: number | null
  file_mtime?: string | null
  created_at: string
  updated_at: string
}

export interface NovelInboxLogListResponse {
  items: NovelInboxLogItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

export interface NovelInboxScanResult {
  scanned_files: number
  imported_count: number
  skipped_already_imported: number
  skipped_failed_before: number
  skipped_unsupported: number
  tts_jobs_created: number
  failed_count: number
}

