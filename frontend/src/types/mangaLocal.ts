/**
 * 本地漫画库类型定义
 */

// import type { MangaSourceType } from './mangaSource'

export interface MangaSeriesLocal {
  id: number
  source_id: number
  remote_series_id: string
  title: string
  alt_titles?: string[]
  cover_url?: string  // 后端拼好的可访问 URL
  summary?: string
  authors?: string[]
  tags?: string[]
  status?: string
  language?: string
  is_favorite: boolean
  is_hidden: boolean
  total_chapters?: number
  downloaded_chapters?: number
  last_sync_at?: string
  created_at: string
  updated_at: string
}

export type MangaChapterStatus = 'PENDING' | 'DOWNLOADING' | 'READY' | 'FAILED'

export interface MangaChapterLocal {
  id: number
  series_id: number
  remote_chapter_id: string
  title: string
  number?: number
  volume?: number
  published_at?: string
  status: MangaChapterStatus
  page_count?: number
  last_error?: string | null
  created_at: string
  updated_at: string
}

export interface LocalMangaPage {
  index: number
  image_url: string
}

export interface MangaReadingProgress {
  id: number
  series_id: number
  chapter_id?: number | null
  last_page_index: number
  total_pages?: number | null
  is_finished: boolean
  last_read_at: string
  created_at: string
  updated_at: string
}

export interface MangaReadingHistoryItem {
  series_id: number
  series_title: string
  series_cover_url?: string
  source_name?: string
  last_chapter_id?: number
  last_chapter_title?: string
  last_page_index?: number
  total_pages?: number
  is_finished: boolean
  last_read_at: string
}

