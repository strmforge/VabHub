/**
 * 漫画源类型定义
 */

export type MangaSourceType = 'OPDS' | 'SUWAYOMI' | 'KOMGA' | 'GENERIC_HTTP'

export interface MangaSource {
  id: number
  name: string
  type: MangaSourceType
  base_url: string
  api_key?: string
  username?: string
  password?: string
  is_enabled: boolean
  extra_config?: Record<string, any>
  created_at: string
  updated_at: string
}

export interface MangaSourceCreatePayload {
  name: string
  type: MangaSourceType
  base_url: string
  api_key?: string
  username?: string
  password?: string
  is_enabled: boolean
  extra_config?: Record<string, any>
}

export interface MangaSourceUpdatePayload extends Partial<MangaSourceCreatePayload> {}

// 远程漫画相关类型
export interface RemoteMangaSourceInfo {
  id: number
  name: string
  type: MangaSourceType
  is_enabled: boolean
}

export interface RemoteMangaSeries {
  source_id: number
  source_type: MangaSourceType
  remote_id: string
  title: string
  alt_titles?: string[]
  cover_url?: string
  status?: string
  authors?: string[]
  tags?: string[]
  summary?: string
  chapters_count?: number
}

export interface RemoteMangaChapter {
  source_id: number
  source_type: MangaSourceType
  series_remote_id: string
  remote_id: string
  title: string
  number?: number
  volume?: number
  published_at?: string
}

export interface RemoteMangaSearchResult {
  total: number
  page: number
  page_size: number
  items: RemoteMangaSeries[]
}

// 聚合搜索相关类型
export interface SourceSearchResult {
  source_id: number
  source_name: string
  source_type: MangaSourceType
  success: boolean
  error_message?: string
  result?: RemoteMangaSearchResult
}

export interface AggregatedSearchResult {
  query: string
  total_sources: number
  successful_sources: number
  failed_sources: number
  results_by_source: SourceSearchResult[]
  total_items: number
  has_failures: boolean
}

// 漫画源库/书架信息（用于按库浏览）
export interface MangaLibraryInfo {
  id: string
  name: string
}

