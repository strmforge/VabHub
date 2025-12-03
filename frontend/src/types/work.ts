/**
 * 作品中心（Work Hub）类型定义
 */

export interface WorkEBookFile {
  id: number
  file_path: string
  format?: string | null
  file_size_mb?: number | null
  source_site_id?: string | null
  source_torrent_id?: string | null
  download_task_id?: number | null
  created_at: string
}

export interface WorkEBook {
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

export interface WorkAudiobookFile {
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
  is_tts_generated?: boolean  // 是否由 TTS 自动生成
  tts_provider?: string | null  // TTS 提供商（dummy/http/edge_tts 等）
  created_at: string
}

export interface WorkComic {
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
}

export interface WorkComicFile {
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
}

export interface WorkVideoItem {
  id: number
  media_type: string // "movie" | "tv" | "anime" | "short_drama"
  title: string
  original_title?: string | null
  year?: number | null
  season_index?: number | null
  poster_url?: string | null
  rating?: number | null
  source_site_id?: number | null
  created_at: string
}

export interface WorkMusicItem {
  id: number
  title: string
  artist?: string | null
  album?: string | null
  year?: number | null
  genre?: string | null
  cover_url?: string | null
  created_at: string
}

export type WorkTargetType = "video" | "comic" | "music"
export type WorkLinkRelation = "include" | "exclude"

export interface WorkLink {
  id: number
  ebook_id: number
  target_type: WorkTargetType
  target_id: number
  relation: WorkLinkRelation
  created_at: string
  updated_at: string
}

export interface WorkDetailResponse {
  ebook: WorkEBook
  ebook_files: WorkEBookFile[]
  audiobooks: WorkAudiobookFile[]
  comics: WorkComic[]
  comic_files: WorkComicFile[]
  videos: WorkVideoItem[]
  music: WorkMusicItem[]
  links?: WorkLink[]  // 手动关联列表（可选，向后兼容）
}

