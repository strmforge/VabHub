/**
 * TTS 相关类型定义
 */

export type TTSJobStatus = "queued" | "running" | "success" | "partial" | "failed"

export interface TTSJob {
  id: number
  ebook_id: number
  status: TTSJobStatus
  provider?: string | null
  strategy?: string | null
  requested_at: string
  started_at?: string | null
  finished_at?: string | null
  total_chapters?: number | null
  processed_chapters: number
  created_files_count: number
  error_count: number
  last_error?: string | null
  created_by?: string | null
  details?: Record<string, any> | null
}

export interface TTSWorkProfile {
  id: number
  ebook_id: number
  preset_id?: number | null
  provider?: string | null
  language?: string | null
  voice?: string | null
  speed?: number | null
  pitch?: number | null
  enabled: boolean
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface TTSVoicePreset {
  id: number
  name: string
  provider?: string | null
  language?: string | null
  voice?: string | null
  speed?: number | null
  pitch?: number | null
  is_default: boolean
  notes?: string | null
  created_at: string
  updated_at: string
}

export interface TTSWorkBatchFilter {
  language?: string
  author_substring?: string
  series_substring?: string
  tag_keyword?: string
  created_from?: string // ISO
  created_to?: string   // ISO
  has_profile?: boolean | null
}

export interface TTSWorkBatchPreviewItem {
  ebook_id: number
  title: string
  author?: string | null
  series?: string | null
  language?: string | null
  created_at: string
  has_profile: boolean
  profile_enabled?: boolean | null
  profile_preset_id?: number | null
  profile_preset_name?: string | null
}

export interface TTSWorkBatchPreviewResponse {
  total: number
  limit: number
  items: TTSWorkBatchPreviewItem[]
}

export interface ApplyTTSWorkPresetRequest {
  preset_id: number
  filter: TTSWorkBatchFilter
  override_existing?: boolean
  enable_profile?: boolean
  dry_run?: boolean
}

export interface ApplyTTSWorkPresetResult {
  matched_ebooks: number
  created_profiles: number
  updated_profiles: number
  skipped_existing_profile: number
}

// ========== TTS Playground ==========

export interface TTSPlaygroundRequest {
  text: string
  language?: string
  voice?: string
  speed?: number
  pitch?: number
  ebook_id?: number
  provider?: string
  skip_rate_limit?: boolean
}

export interface TTSPlaygroundResponse {
  success: boolean
  message: string
  provider?: string | null
  language?: string | null
  voice?: string | null
  speed?: number | null
  pitch?: number | null
  char_count: number
  duration_seconds?: number | null
  audio_url?: string | null
  rate_limited: boolean
  rate_limit_reason?: string | null
}

// ========== 用户版 TTS Flow ==========

export interface UserWorkTTSStatus {
  ebook_id: number
  has_tts_audiobook: boolean
  last_job_status?: 'queued' | 'running' | 'partial' | 'success' | 'failed'
  last_job_requested_at?: string | null
  last_job_finished_at?: string | null
  last_job_message?: string | null
  total_chapters?: number | null
  generated_chapters?: number | null
}

export interface UserTTSJobEnqueueResponse {
  success: boolean
  job_id: number
  ebook_id: number
  status: string
  message: string
  already_exists?: boolean
}

export interface UserTTSJobOverviewItem {
  job_id: number
  ebook_id: number
  ebook_title: string
  ebook_author?: string | null
  status: string
  requested_at: string
  finished_at?: string | null
  progress?: {
    generated_chapters?: number
    total_chapters?: number
  } | null
  last_message?: string | null
}

// ========== 用户批量 TTS ==========

export interface UserTTSBatchFilter {
  language?: string | null
  author_substring?: string | null
  series_substring?: string | null
  tag_keyword?: string | null
  only_without_audiobook: boolean
  only_without_active_job: boolean
  max_candidates: number
}

export interface UserTTSBatchPreviewItem {
  ebook_id: number
  title: string
  author?: string | null
  language?: string | null
  has_audiobook: boolean
  has_tts_audiobook: boolean
  active_job_status?: string | null
  last_job_status?: string | null
}

export interface UserTTSBatchPreviewResponse {
  total_candidates: number
  items: UserTTSBatchPreviewItem[]
}

export interface UserTTSBatchEnqueueRequest {
  filter: UserTTSBatchFilter
  max_new_jobs: number
  skip_if_has_tts: boolean
}

export interface UserTTSBatchEnqueueResult {
  total_candidates: number
  skipped_has_audiobook: number
  skipped_has_tts: number
  skipped_has_active_job: number
  enqueued_new_jobs: number
  already_had_jobs: number
}

// ========== TTS 存储管理（Dev）==========

export type TTSStorageCleanupScope = 'all' | 'playground_only' | 'job_only' | 'other_only'

export interface TTSStorageCategoryStats {
  files: number
  size_bytes: number
}

export interface TTSStorageAutoCleanupStatus {
  enabled: boolean
  last_run_at?: string | null
  last_run_status?: string | null
  last_run_deleted_files?: number | null
  last_run_freed_bytes?: number | null
  last_run_reason?: string | null
}

export interface TTSStorageOverviewResponse {
  root: string
  total_files: number
  total_size_bytes: number
  by_category: Record<string, TTSStorageCategoryStats>
  auto_cleanup?: TTSStorageAutoCleanupStatus | null
}

export interface TTSStorageCleanupPreviewRequest {
  scope: TTSStorageCleanupScope
  min_age_days: number
  max_files: number
  mode?: 'manual' | 'policy'  // 清理模式：'manual' 手动参数模式，'policy' 按策略推荐模式
}

export interface TTSStorageCleanupPreviewItem {
  path: string
  size_bytes: number
  mtime: string
  category: string
}

export interface TTSStorageCleanupPreviewResponse {
  root: string
  total_matched_files: number
  total_freed_bytes: number
  sample: TTSStorageCleanupPreviewItem[]
  used_policy?: boolean  // 是否使用了策略模式
  policy_name?: string | null  // 使用的策略名称（如果 used_policy=true）
}

export interface TTSStorageCleanupExecuteRequest extends TTSStorageCleanupPreviewRequest {
  dry_run: boolean
}

export interface TTSStorageCleanupExecuteResponse {
  root: string
  deleted_files: number
  freed_bytes: number
  dry_run: boolean
  message: string
}

// ========== TTS Storage Policy ==========

export interface TTSStorageCategoryPolicy {
  min_keep_days: number  // 至少保留多少天内的文件不删（0 表示不按天限制）
  min_keep_files: number  // 至少保留多少个最新文件
  max_keep_files: number | null  // 最多允许保留多少个文件（null 表示不限制）
}

export interface TTSStoragePolicy {
  name: string
  playground: TTSStorageCategoryPolicy
  job: TTSStorageCategoryPolicy
  other: TTSStorageCategoryPolicy
}

// ========== Audiobook Player ==========

export interface UserAudiobookChapter {
  file_id: number
  title: string
  duration_seconds?: number | null
  is_tts_generated: boolean
  tts_provider?: string | null
  order: number
}

export interface UserWorkAudiobookStatus {
  has_audiobook: boolean
  current_file_id?: number | null
  current_position_seconds: number
  current_duration_seconds?: number | null
  progress_percent?: number | null
  chapters: UserAudiobookChapter[]
}

