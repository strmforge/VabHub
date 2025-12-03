export interface FollowedMangaItem {
  follow_id: number
  series_id: number
  series_title: string
  cover_url?: string | null
  source_id: number
  unread_chapter_count: number
  last_synced_chapter_id?: number | null
  last_seen_chapter_id?: number | null
  created_at: string
  updated_at: string
}
