/**
 * 应用全局类型定义
 * RELEASE-1 R0-1 实现
 */

export interface AppVersionInfo {
  name: string
  version: string
  build_commit?: string | null
  build_date?: string | null
  demo_mode?: boolean
}
