/**
 * 全局搜索类型定义
 * SEARCH-1 实现
 */

export interface GlobalSearchItem {
  media_type: string  // movie/series/novel/audiobook/manga/music
  id: string
  title: string
  sub_title?: string | null
  cover_url?: string | null
  route_name?: string | null
  route_params?: Record<string, any> | null
  score?: number | null
}

export interface GlobalSearchResponse {
  items: GlobalSearchItem[]
}
