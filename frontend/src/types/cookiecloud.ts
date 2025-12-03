/**
 * CookieCloud 相关类型定义
 */

// Cookie来源枚举
export enum CookieSource {
  MANUAL = 'MANUAL',
  COOKIECLOUD = 'COOKIECLOUD'
}

// CookieCloud设置基础类型
export interface CookieCloudSettings {
  enabled: boolean
  host?: string
  uuid?: string
  password?: string
  sync_interval_minutes: number
  safe_host_whitelist?: string[]
  last_sync_at?: string
  last_status?: string
  last_error?: string
  created_at: string
  updated_at: string
}

// CookieCloud设置更新类型
export interface CookieCloudSettingsUpdate {
  enabled?: boolean
  host?: string
  uuid?: string
  password?: string
  sync_interval_minutes?: number
  safe_host_whitelist?: string[]
}

// CookieCloud同步结果
export interface CookieCloudSyncResult {
  success: boolean
  total_sites: number
  synced_sites: number
  unmatched_sites: number
  error_sites: number
  errors: string[]
  sync_time: string
}

// CookieCloud单站点同步结果
export interface CookieCloudSiteSyncResult {
  site_id: number
  site_name: string
  success: boolean
  cookie_updated: boolean
  error_message?: string
  duration_seconds?: number
}

// CookieCloud连接测试结果
export interface CookieCloudTestResult {
  success: boolean
  message: string
  details?: Record<string, any>
}

// CookieCloud状态概览
export interface CookieCloudStatus {
  enabled: boolean
  configured: boolean
  last_sync_at?: string
  last_status?: string
  last_error?: string
  sync_interval_minutes: number
  total_sites: number
  cookiecloud_sites: number
  safe_domains: number
}

// CookieCloud同步历史记录
export interface CookieCloudSyncHistory {
  id: number
  sync_at: string
  status: string
  error?: string
  total_sites: number
  synced_sites: number
  duration_seconds: number
}

// API响应类型（基于后端ApiResponse格式）
export interface ApiResponse<T> {
  success: boolean
  data: T
  message: string
  code?: number
}

// 分页响应类型
export interface PaginationResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// CookieCloud状态类型
export type CookieCloudSyncStatus = 'SUCCESS' | 'ERROR' | 'PARTIAL' | 'NEVER' | 'RUNNING'

// CookieCloud配置验证结果
export interface CookieCloudValidationResult {
  valid: boolean
  errors: string[]
  warnings: string[]
}
