/**
 * 小说中心类型定义
 */

export interface NovelCenterEBookSummary {
  id: number
  title: string
  original_title?: string | null
  author?: string | null
  series?: string | null
  language?: string | null
  cover_url?: string | null
  updated_at: string
}

export interface NovelCenterListeningProgress {
  has_progress: boolean
  is_finished: boolean
  progress_percent: number
  current_file_id?: number | null
  current_chapter_title?: string | null
  last_played_at?: string | null
}

export interface NovelCenterReadingProgress {
  has_progress: boolean
  is_finished: boolean
  progress_percent: number
  current_chapter_index?: number | null
  current_chapter_title?: string | null
  last_read_at?: string | null
}

export interface NovelCenterItem {
  ebook: NovelCenterEBookSummary
  has_audiobook: boolean
  has_tts_audiobook: boolean
  last_tts_job_status?: string | null
  last_tts_job_at?: string | null
  listening: NovelCenterListeningProgress
  reading: NovelCenterReadingProgress
  is_favorite?: boolean
}

export interface NovelCenterListResponse {
  items: NovelCenterItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

/**
 * 小说阅读器类型定义
 */

export interface NovelChapterSummary {
  index: number
  title: string
  length?: number | null
}

export interface NovelChapterTextResponse {
  ebook_id: number
  chapter_index: number
  title: string
  content: string
}

export interface UserNovelReadingProgress {
  ebook_id: number
  current_chapter_index: number
  chapter_offset: number
  is_finished: boolean
  last_read_at: string
}

export interface NovelSearchHit {
  chapter_index: number
  chapter_title?: string | null
  snippet: string
}

/**
 * 我的书架类型定义
 */

export interface MyShelfWorkSummary {
  ebook_id: number
  title: string
  original_title?: string | null
  author?: string | null
  series?: string | null
  language?: string | null
  cover_url?: string | null
  updated_at: string
}

export interface MyShelfReadingProgress {
  has_progress: boolean
  is_finished: boolean
  progress_percent: number
  current_chapter_index?: number | null
  current_chapter_title?: string | null
  last_read_at?: string | null
}

export interface MyShelfListeningProgress {
  has_progress: boolean
  is_finished: boolean
  progress_percent: number
  current_file_id?: number | null
  current_chapter_title?: string | null
  last_listened_at?: string | null
}

export interface MyShelfTTSStatus {
  has_audiobook: boolean
  has_tts_audiobook: boolean
  last_job_status?: string | null
  last_job_at?: string | null
}

export interface MyShelfItem {
  work: MyShelfWorkSummary
  reading: MyShelfReadingProgress
  listening: MyShelfListeningProgress
  tts: MyShelfTTSStatus
}

export interface MyShelfListResponse {
  items: MyShelfItem[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

