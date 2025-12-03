/**
 * 统一媒体库类型定义
 */

export type MediaType = 'movie' | 'tv' | 'anime' | 'ebook' | 'audiobook' | 'comic' | 'music'

export interface WorkFormats {
  has_ebook: boolean
  has_audiobook: boolean
  has_comic: boolean
  has_music: boolean
}

export interface LibraryPreviewItem {
  id: number
  media_type: MediaType
  title: string
  year?: number | null
  cover_url?: string | null
  created_at: string
  work_formats?: WorkFormats | null  // 作品形态概览（仅对 ebook 类型有意义）
  extra?: {
    // 通用字段
    ebook_id?: number  // audiobook 类型时，用于跳转到作品详情页
    
    // Movie/TV/Anime 特有
    tmdb_id?: number
    imdb_id?: string
    rating?: number
    
    // EBook 特有
    author?: string
    series?: string
    isbn?: string
    
    // Audiobook 特有
    narrator?: string
    duration_seconds?: number
    
    // Comic 特有
    volume_index?: number | string
    illustrator?: string
    region?: string
    
    // Music 特有
    album?: string
    genre?: string
    album_artist?: string
  } | null
}

export interface LibraryPreviewResponse {
  items: LibraryPreviewItem[]
  total: number
  page: number
  page_size: number
}

export interface EBookFile {
  id: number
  ebook_id: number
  file_path: string
  file_size_bytes?: number | null
  file_size_mb?: number | null
  format: string
  source_site_id?: string | null
  source_torrent_id?: string | null
  download_task_id?: number | null
  is_deleted: boolean
  created_at: string
}

export interface EBookDetail {
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
  created_at: string
  updated_at: string
  files: EBookFile[]
}

export interface AudiobookFile {
  id: number
  ebook_id: number
  file_path: string
  file_size_bytes?: number | null
  file_size_mb?: number | null
  format: string
  duration_seconds?: number | null
  bitrate_kbps?: number | null
  channels?: number | null
  sample_rate_hz?: number | null
  narrator?: string | null
  language?: string | null
  source_site_id?: string | null
  source_torrent_id?: string | null
  download_task_id?: number | null
  is_deleted: boolean
  created_at: string
}

