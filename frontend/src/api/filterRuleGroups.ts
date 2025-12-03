import api from '@/services/api'

export interface FilterRuleGroup {
  id: number
  user_id: number
  name: string
  description: string
  media_types: string[]
  priority: number
  rules: any[]
  enabled: boolean
  created_at: string
  updated_at: string
  created_by: number
  updated_by: number
}

export interface FilterRuleGroupRequest {
  name: string
  description?: string
  media_types: string[]
  priority?: number
  rules: any[]
  enabled?: boolean
}

export interface FilterRuleGroupResponse {
  items: FilterRuleGroup[]
  total: number
  page: number
  size: number
}

export const filterRuleGroupsApi = {
  // 获取过滤规则组列表
  async getFilterRuleGroups(params?: {
    page?: number
    size?: number
    media_type?: string
    enabled?: boolean
    search?: string
  }): Promise<{ data: FilterRuleGroupResponse }> {
    const response = await api.get('/filter-rule-groups', { params })
    return response.data
  },

  // 获取单个过滤规则组
  async getFilterRuleGroup(id: number): Promise<{ data: FilterRuleGroup }> {
    const response = await api.get(`/filter-rule-groups/${id}`)
    return response.data
  },

  // 创建过滤规则组
  async createFilterRuleGroup(group: FilterRuleGroupRequest): Promise<{ data: FilterRuleGroup }> {
    const response = await api.post('/filter-rule-groups', group)
    return response.data
  },

  // 更新过滤规则组
  async updateFilterRuleGroup(id: number, group: Partial<FilterRuleGroupRequest>): Promise<{ data: FilterRuleGroup }> {
    const response = await api.put(`/filter-rule-groups/${id}`, group)
    return response.data
  },

  // 删除过滤规则组
  async deleteFilterRuleGroup(id: number): Promise<void> {
    await api.delete(`/filter-rule-groups/${id}`)
  },

  // 批量删除过滤规则组
  async deleteFilterRuleGroups(ids: number[]): Promise<void> {
    await api.delete('/filter-rule-groups', { data: { ids } })
  },

  // 启用/禁用过滤规则组
  async toggleFilterRuleGroup(id: number, enabled: boolean): Promise<{ data: FilterRuleGroup }> {
    const response = await api.patch(`/filter-rule-groups/${id}/toggle`, { enabled })
    return response.data
  },

  // 获取媒体类型选项
  async getMediaTypeOptions(): Promise<{ data: string[] }> {
    const response = await api.get('/filter-rule-groups/media-types')
    return response.data
  },

  // 验证规则组配置
  async validateRuleGroup(group: FilterRuleGroupRequest): Promise<{ data: { valid: boolean; errors?: string[] } }> {
    const response = await api.post('/filter-rule-groups/validate', group)
    return response.data
  }
}
