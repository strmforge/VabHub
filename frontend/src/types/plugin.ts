/**
 * 插件类型定义
 * DEV-SDK-1 实现
 * PLUGIN-SDK-2 扩展：SDK 权限声明
 */

export type PluginStatus = 'INSTALLED' | 'ENABLED' | 'DISABLED' | 'BROKEN'

export interface PluginCapabilities {
  search_providers: string[]
  bot_commands: string[]
  workflows: string[]
}

export interface PluginInfo {
  id: number
  name: string
  display_name: string
  version: string
  description?: string
  author?: string
  homepage?: string
  entry_module: string
  front_entry?: string
  capabilities: PluginCapabilities | Record<string, any>
  status: PluginStatus
  plugin_dir?: string
  installed_at: string
  updated_at: string
  last_error?: string
  
  // PLUGIN-SDK-2：SDK 权限声明
  sdk_permissions?: string[]
  
  // PLUGIN-UX-3：配置 Schema
  config_schema?: Record<string, any> | null
  
  // 来源信息（PLUGIN-HUB-2）
  source?: string
  hub_id?: string
  repo_url?: string
  installed_ref?: string
  auto_update_enabled?: boolean
}

// ============== PLUGIN-UX-3：插件配置 ==============

export interface PluginConfig {
  plugin_id: string
  config: Record<string, any>
  updated_at?: string | null
}

// ============== PLUGIN-UX-3：Dashboard DSL ==============

export type PluginDashboardWidgetType = 'stat_card' | 'table' | 'text' | 'action_button'

export interface PluginDashboardWidget {
  id: string
  type: PluginDashboardWidgetType
  title?: string
  description?: string
  // stat_card
  value?: string
  unit?: string
  icon?: string
  color?: string
  // table
  columns?: string[]
  rows?: Record<string, any>[]
  // text
  markdown?: string
  // action_button
  action_api?: string
  action_method?: string
  action_params_schema?: Record<string, any>
  action_label?: string
}

export interface PluginDashboardSchema {
  widgets: PluginDashboardWidget[]
}

export interface PluginScanResult {
  scanned: number
  new_plugins: number
  updated_plugins: number
  broken_plugins: number
  plugins: PluginInfo[]
}

export interface WorkflowExtensionInfo {
  id: string
  name: string
  description: string
  plugin_id: string
  plugin_name: string
}

export interface WorkflowRunResult {
  workflow_id: string
  success: boolean
  result?: Record<string, any>
  error?: string
  duration_ms: number
}

// 辅助函数
export function getStatusColor(status: PluginStatus): string {
  const colors: Record<PluginStatus, string> = {
    INSTALLED: 'grey',
    ENABLED: 'success',
    DISABLED: 'warning',
    BROKEN: 'error',
  }
  return colors[status] || 'grey'
}

export function getStatusLabel(status: PluginStatus): string {
  const labels: Record<PluginStatus, string> = {
    INSTALLED: '已安装',
    ENABLED: '已启用',
    DISABLED: '已禁用',
    BROKEN: '已损坏',
  }
  return labels[status] || status
}

export function getStatusIcon(status: PluginStatus): string {
  const icons: Record<PluginStatus, string> = {
    INSTALLED: 'mdi-package-variant',
    ENABLED: 'mdi-check-circle',
    DISABLED: 'mdi-pause-circle',
    BROKEN: 'mdi-alert-circle',
  }
  return icons[status] || 'mdi-help-circle'
}

// ============== PLUGIN-SDK-2：SDK 权限相关 ==============

// SDK 权限中文标签映射
const SDK_PERMISSION_LABELS: Record<string, string> = {
  'download.read': '下载（读取）',
  'download.write': '下载（写入）',
  'media.read': '媒体库读取',
  'cloud115.task': '115 离线任务',
  'cloud115.read': '115 目录读取',
}

// 危险权限列表
const DANGEROUS_PERMISSIONS = new Set([
  'download.write',
  'cloud115.task',
])

/**
 * 获取 SDK 权限的中文标签
 */
export function getSdkPermissionLabel(permission: string): string {
  return SDK_PERMISSION_LABELS[permission] || permission
}

/**
 * 判断是否为危险权限
 */
export function isDangerousPermission(permission: string): boolean {
  return DANGEROUS_PERMISSIONS.has(permission)
}

/**
 * 获取权限的颜色（用于 chip 显示）
 */
export function getSdkPermissionColor(permission: string): string {
  return isDangerousPermission(permission) ? 'warning' : 'default'
}
