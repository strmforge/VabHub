/**
 * 自检类型定义
 * QA-1 实现
 */

export type SelfCheckStatus = 'pass' | 'warn' | 'fail' | 'skipped'

export interface SelfCheckItemResult {
  code: string
  name: string
  status: SelfCheckStatus
  message?: string
  details?: Record<string, any>
  duration_ms?: number
}

export interface SelfCheckGroupResult {
  code: string
  name: string
  status: SelfCheckStatus
  items: SelfCheckItemResult[]
}

export interface SelfCheckRunResult {
  started_at: string
  finished_at: string
  overall_status: SelfCheckStatus
  groups: SelfCheckGroupResult[]
  environment: Record<string, any>
}

// 辅助函数：获取状态颜色
export function getStatusColor(status: SelfCheckStatus): string {
  const colors: Record<SelfCheckStatus, string> = {
    pass: 'success',
    warn: 'warning',
    fail: 'error',
    skipped: 'grey',
  }
  return colors[status] || 'grey'
}

// 辅助函数：获取状态图标
export function getStatusIcon(status: SelfCheckStatus): string {
  const icons: Record<SelfCheckStatus, string> = {
    pass: 'mdi-check-circle',
    warn: 'mdi-alert',
    fail: 'mdi-close-circle',
    skipped: 'mdi-minus-circle',
  }
  return icons[status] || 'mdi-help-circle'
}

// 辅助函数：获取状态标签
export function getStatusLabel(status: SelfCheckStatus): string {
  const labels: Record<SelfCheckStatus, string> = {
    pass: '通过',
    warn: '警告',
    fail: '失败',
    skipped: '跳过',
  }
  return labels[status] || status
}

// 辅助函数：获取组名称
export function getGroupName(code: string): string {
  const names: Record<string, string> = {
    core: '核心检查',
    novel_tts: '小说 / TTS / 有声书',
    manga: '漫画',
    music: '音乐',
    notify: '通知',
    bot: 'Bot / Telegram',
    runners: 'Runner 状态',
  }
  return names[code] || code
}

// 辅助函数：获取组图标
export function getGroupIcon(code: string): string {
  const icons: Record<string, string> = {
    core: 'mdi-cog',
    novel_tts: 'mdi-book-open-page-variant',
    manga: 'mdi-image-multiple',
    music: 'mdi-music',
    notify: 'mdi-bell',
    bot: 'mdi-robot',
    runners: 'mdi-run',
  }
  return icons[code] || 'mdi-checkbox-marked-circle'
}
