/**
 * 阅读收藏类型定义
 */

import type { ReadingMediaType } from './readingHub'

export interface UserFavoriteMedia {
  id: number
  media_type: ReadingMediaType
  target_id: number
  created_at: string
  updated_at: string
}

export interface ReadingShelfItem {
  media_type: ReadingMediaType
  item_id: number
  title: string
  cover_url?: string
  source_label?: string
  last_position_label?: string | null
  is_finished: boolean
  last_read_at?: string | null
  route_name: string
  route_params: Record<string, any>
  // 漫画特有的更新状态
  new_chapter_count?: number
  last_sync_at?: string | null
  has_updates?: boolean
}

export interface FavoriteCheckResponse {
  is_favorite: boolean
}

export interface FavoriteOperationResponse {
  ok: boolean
  message: string
}