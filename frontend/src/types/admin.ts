/**
 * 系统运维类型定义
 * ADMIN-1 实现
 */

export interface RunnerStatus {
  name: string
  key: string
  last_run_at?: string | null
  last_status?: string | null  // "success" | "failed" | "unknown"
  last_message?: string | null
}

export interface ExternalSourceStatus {
  name: string
  type: string  // manga / music / indexer
  url?: string | null
  last_check_at?: string | null
  last_status: string  // ok / error / disabled / unknown
  message?: string | null
}

export interface StorageInfo {
  name: string
  path?: string | null
  total_items: number
  size_description?: string | null
  status: string  // ok / warning / error / empty / unknown
}

export interface AdminDashboardResponse {
  runners: RunnerStatus[]
  external_sources: ExternalSourceStatus[]
  storage: StorageInfo[]
}
