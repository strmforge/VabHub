/**
 * CookieCloud API 服务
 */

import api from '@/services/api'
import type {
  CookieCloudSettings,
  CookieCloudSettingsUpdate,
  CookieCloudSyncResult,
  CookieCloudSiteSyncResult,
  CookieCloudTestResult,
  CookieCloudStatus,
  CookieCloudSyncHistory,
  PaginationResponse
} from '@/types/cookiecloud'

// CookieCloud API 客户端
export class CookieCloudApi {
  // 获取CookieCloud设置
  static async getSettings(): Promise<CookieCloudSettings> {
    const response = await api.get<CookieCloudSettings>('/cookiecloud/settings')
    return response.data
  }

  // 更新CookieCloud设置
  static async updateSettings(settings: CookieCloudSettingsUpdate): Promise<CookieCloudSettings> {
    const response = await api.put<CookieCloudSettings>('/cookiecloud/settings', settings)
    return response.data
  }

  // 触发CookieCloud同步（异步）
  static async triggerSync(options?: {
    batch_size?: number
    site_timeout?: number
  }): Promise<CookieCloudSyncResult> {
    const response = await api.post<CookieCloudSyncResult>('/cookiecloud/sync', options)
    return response.data
  }

  // 立即触发CookieCloud同步（同步执行）
  static async triggerSyncImmediate(options?: {
    batch_size?: number
    site_timeout?: number
  }): Promise<CookieCloudSyncResult> {
    const response = await api.post<CookieCloudSyncResult>('/cookiecloud/sync-immediate', options)
    return response.data
  }

  // 触发单个站点的CookieCloud同步
  static async triggerSiteSync(siteId: number): Promise<CookieCloudSiteSyncResult> {
    const response = await api.post<CookieCloudSiteSyncResult>(`/cookiecloud/sync-site/${siteId}`)
    return response.data
  }

  // 测试CookieCloud连接
  static async testConnection(): Promise<CookieCloudTestResult> {
    const response = await api.post<CookieCloudTestResult>('/cookiecloud/test-connection')
    return response.data
  }

  // 获取CookieCloud状态概览
  static async getStatus(): Promise<CookieCloudStatus> {
    const response = await api.get<CookieCloudStatus>('/cookiecloud/status')
    return response.data
  }

  // 获取CookieCloud同步历史
  static async getSyncHistory(params?: {
    page?: number
    size?: number
  }): Promise<PaginationResponse<CookieCloudSyncHistory>> {
    const response = await api.get<PaginationResponse<CookieCloudSyncHistory>>('/cookiecloud/sync-history', {
      params
    })
    return response.data
  }

  // 验证CookieCloud配置
  static async validateSettings(settings: CookieCloudSettingsUpdate): Promise<boolean> {
    try {
      // 基础验证
      if (settings.enabled && (!settings.host || !settings.uuid || !settings.password)) {
        return false
      }

      // 验证主机地址格式
      if (settings.host && !settings.host.startsWith('http')) {
        return false
      }

      // 验证UUID长度
      if (settings.uuid && settings.uuid.length < 8) {
        return false
      }

      // 验证同步间隔
      if (settings.sync_interval_minutes && (settings.sync_interval_minutes < 5 || settings.sync_interval_minutes > 1440)) {
        return false
      }

      return true
    } catch (error) {
      console.error('验证CookieCloud设置失败:', error)
      return false
    }
  }

  // 格式化CookieCloud设置（用于前端显示）
  static formatSettingsForDisplay(settings: CookieCloudSettings): CookieCloudSettings {
    return {
      ...settings,
      password: settings.password ? '***' : ''
    }
  }

  // 准备CookieCloud设置（用于提交到后端）
  static prepareSettingsForSubmit(settings: CookieCloudSettingsUpdate): CookieCloudSettingsUpdate {
    const submitData = { ...settings }
    
    // 如果密码是脱敏状态，不提交密码字段
    if (submitData.password === '***') {
      delete submitData.password
    }

    // 清理主机地址末尾斜杠
    if (submitData.host) {
      submitData.host = submitData.host.replace(/\/$/, '')
    }

    return submitData
  }
}

export default CookieCloudApi
