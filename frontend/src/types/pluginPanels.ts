/**
 * 插件面板类型定义
 * DEV-SDK-2 实现
 */

// 面板放置位置
export type PluginPanelPlacement =
  | 'home_dashboard'
  | 'admin_dashboard'
  | 'task_center'
  | 'reading_center'
  | 'dev_plugin'
  | 'custom'

// 面板类型
export type PluginPanelType =
  | 'metric_grid'
  | 'list'
  | 'markdown'
  | 'log_stream'
  | 'status_card'

// 面板定义
export interface PluginPanelDefinition {
  id: string
  title: string
  description?: string
  placement: PluginPanelPlacement
  type: PluginPanelType
  endpoint?: string
  order: number
  enabled_by_default: boolean
  config?: Record<string, any>
}

// 带插件信息的面板
export interface PluginPanelWithPlugin {
  plugin_id: string
  plugin_name: string
  panel: PluginPanelDefinition
}

// 面板数据响应
export interface PluginPanelDataResponse {
  type: PluginPanelType
  meta?: Record<string, any>
  payload: any
}

// ============== 面板数据类型 ==============

// Metric Grid 面板数据
export interface MetricCard {
  label: string
  value: number | string
  unit?: string
  icon?: string
  color?: string
  trend?: 'up' | 'down' | 'flat'
}

export interface MetricGridPayload {
  cards: MetricCard[]
}

// List 面板数据
export interface ListColumn {
  key: string
  title: string
  width?: number | string
  align?: 'left' | 'center' | 'right'
}

export interface ListPayload {
  columns: ListColumn[]
  rows: Record<string, any>[]
  total?: number
}

// Markdown 面板数据
export interface MarkdownPayload {
  content: string
}

// Log Stream 面板数据
export interface LogEntry {
  timestamp: string
  level: 'info' | 'warn' | 'error' | 'debug'
  message: string
}

export interface LogStreamPayload {
  entries: LogEntry[]
}

// Status Card 面板数据
export interface StatusCardPayload {
  status: 'ok' | 'warning' | 'error' | 'unknown'
  message: string
  icon?: string
  details?: Record<string, any>
}

// ============== 辅助函数 ==============

export function getPlacementLabel(placement: PluginPanelPlacement): string {
  const labels: Record<PluginPanelPlacement, string> = {
    home_dashboard: '首页仪表盘',
    admin_dashboard: '管理员面板',
    task_center: '任务中心',
    reading_center: '阅读中心',
    dev_plugin: '插件开发',
    custom: '自定义',
  }
  return labels[placement] || placement
}

export function getPanelTypeLabel(type: PluginPanelType): string {
  const labels: Record<PluginPanelType, string> = {
    metric_grid: '指标卡片',
    list: '列表',
    markdown: 'Markdown',
    log_stream: '日志流',
    status_card: '状态卡',
  }
  return labels[type] || type
}

export function getPanelTypeIcon(type: PluginPanelType): string {
  const icons: Record<PluginPanelType, string> = {
    metric_grid: 'mdi-view-grid',
    list: 'mdi-format-list-bulleted',
    markdown: 'mdi-language-markdown',
    log_stream: 'mdi-text-long',
    status_card: 'mdi-card-text',
  }
  return icons[type] || 'mdi-puzzle'
}
