import api from '@/services/api'

export interface DefaultSubscriptionConfig {
  quality: string
  resolution: string
  effect: string
  min_seeders: number
  auto_download: boolean
  best_version: boolean
  include: string
  exclude: string
  filter_group_ids: number[]
  allow_hr: boolean
  allow_h3h5: boolean
  strict_free_only: boolean
  sites: number[]
  downloader: string
  save_path: string
}

export interface MediaTypeConfig {
  [mediaType: string]: DefaultSubscriptionConfig
}

export interface AllConfigsResponse {
  configs: MediaTypeConfig
  supported_media_types: string[]
}

export const subscriptionDefaultsApi = {
  // 获取指定媒体类型的默认配置
  async getDefaultConfig(mediaType: string): Promise<{ data: DefaultSubscriptionConfig }> {
    const response = await api.get(`/subscriptions/default-config/${mediaType}`)
    return response.data
  },

  // 保存指定媒体类型的默认配置
  async saveDefaultConfig(mediaType: string, config: Partial<DefaultSubscriptionConfig>): Promise<{ data: DefaultSubscriptionConfig }> {
    const response = await api.post(`/subscriptions/default-config/${mediaType}`, config)
    return response.data
  },

  // 重置指定媒体类型的默认配置
  async resetDefaultConfig(mediaType: string): Promise<{ data: DefaultSubscriptionConfig }> {
    const response = await api.delete(`/subscriptions/default-config/${mediaType}`)
    return response.data
  },

  // 获取所有媒体类型的默认配置
  async getAllConfigs(): Promise<{ data: AllConfigsResponse }> {
    const response = await api.get('/subscriptions/default-config')
    return response.data
  },

  // 获取支持的媒体类型列表
  async getSupportedMediaTypes(): Promise<{ data: string[] }> {
    const response = await api.get('/subscriptions/default-config/media-types')
    return response.data
  },

  // 将默认配置应用到订阅数据
  async applyDefaultConfigToSubscription(mediaType: string, subscriptionData: any): Promise<{ data: any }> {
    const response = await api.post(`/subscriptions/default-config/apply/${mediaType}`, subscriptionData)
    return response.data
  }
}
