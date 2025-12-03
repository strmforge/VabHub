/**
 * Plugin Hub 类型定义
 * PLUGIN-HUB-1 & PLUGIN-HUB-4 实现
 */

// 插件支持的功能
export interface PluginSupports {
  search: boolean
  bot_commands: boolean
  ui_panels: boolean
  workflows: boolean
}

// 频道类型
export type PluginChannel = 'official' | 'community'

// Hub 源配置（PLUGIN-HUB-4）
export interface PluginHubSource {
  id: string
  name: string
  url: string
  channel: PluginChannel
  enabled: boolean
  icon_url?: string | null
  description?: string | null
}

// 远程插件信息
export interface RemotePluginInfo {
  id: string
  name: string
  description?: string | null
  author?: string | null
  tags: string[]
  
  // 仓库信息
  homepage?: string | null
  repo?: string | null
  download_url?: string | null
  
  // 版本信息
  version?: string | null
  min_core_version?: string | null
  
  // 功能支持
  supports: PluginSupports
  panels: string[]
  
  // 其他
  enabled_by_default: boolean
  extra?: Record<string, unknown>
  
  // 作者 & 频道信息（PLUGIN-HUB-3）
  author_name?: string | null
  author_url?: string | null
  channel?: PluginChannel | string | null
  
  // Hub 来源信息（PLUGIN-HUB-4）
  hub_id?: string | null
  hub_name?: string | null
}

// 带本地状态的远程插件信息
export interface RemotePluginWithLocalStatus extends RemotePluginInfo {
  installed: boolean
  local_version?: string | null
  has_update: boolean
  local_plugin_id?: number | null
  
  // 本地来源信息（PLUGIN-HUB-2）
  source?: string | null
  installed_ref?: string | null
  local_repo_url?: string | null
  auto_update_enabled?: boolean | null
  
  // 本地状态（PLUGIN-HUB-4）
  enabled?: boolean
}

// Plugin Hub 索引响应
export interface PluginHubIndexResponse {
  hub_name: string
  hub_version: number
  plugins: RemotePluginWithLocalStatus[]
  fetched_at?: string | null
  cached: boolean
}

// 安装指南响应
export interface PluginInstallGuideResponse {
  plugin_id: string
  plugin_name: string
  installed: boolean
  has_update: boolean
  guide: string
}

// README 响应
export interface PluginReadmeResponse {
  content: string | null
  message?: string
}

// Plugin Hub 配置响应（PLUGIN-HUB-3）
export interface PluginHubConfigResponse {
  community_visible: boolean
  community_install_enabled: boolean
  official_orgs: string[]
}

// ============== 辅助函数 ==============

export function getInstallStatusLabel(plugin: RemotePluginWithLocalStatus): string {
  if (plugin.installed && plugin.has_update) {
    return '可更新'
  } else if (plugin.installed) {
    return '已安装'
  } else {
    return '未安装'
  }
}

export function getInstallStatusColor(plugin: RemotePluginWithLocalStatus): string {
  if (plugin.installed && plugin.has_update) {
    return 'orange'
  } else if (plugin.installed) {
    return 'success'
  } else {
    return 'grey'
  }
}

export function getSupportsIcons(supports: PluginSupports): Array<{ icon: string; label: string; enabled: boolean }> {
  return [
    { icon: 'mdi-magnify', label: '搜索扩展', enabled: supports.search },
    { icon: 'mdi-robot', label: 'Bot 命令', enabled: supports.bot_commands },
    { icon: 'mdi-view-dashboard', label: 'UI 面板', enabled: supports.ui_panels },
    { icon: 'mdi-cog-play', label: 'Workflow', enabled: supports.workflows },
  ]
}

// ============== Channel 辅助函数（PLUGIN-HUB-3） ==============

export function getChannelLabel(channel?: string | null): string {
  switch (channel) {
    case 'official': return '官方'
    case 'community': return '社区'
    default: return '未知'
  }
}

export function getChannelColor(channel?: string | null): string {
  switch (channel) {
    case 'official': return 'primary'
    case 'community': return 'orange'
    default: return 'grey'
  }
}

export function getChannelIcon(channel?: string | null): string {
  switch (channel) {
    case 'official': return 'mdi-shield-check'
    case 'community': return 'mdi-account-group'
    default: return 'mdi-help-circle'
  }
}

export function isOfficialPlugin(plugin: RemotePluginInfo): boolean {
  return plugin.channel === 'official'
}

export function isCommunityPlugin(plugin: RemotePluginInfo): boolean {
  return plugin.channel === 'community'
}
