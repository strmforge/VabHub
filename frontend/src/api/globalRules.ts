import api from '@/services/api'

export interface GlobalRulesSettings {
  hr_mode: 'A_SAFE' | 'B_BALANCED' | 'C_PRO'
  hr_policy: 'IGNORE' | 'SAFE_SKIP' | 'STRICT_SKIP'
  resolution_policy: 'AUTO' | 'MAX_TIER' | 'FIXED_TIER'
  resolution_tier: 'LOW_720P' | 'MID_1080P' | 'HIGH_4K'
  source_quality_policy: 'ANY' | 'NO_TRASH' | 'HIGH_ONLY'
  hdr_policy: 'ANY' | 'HDR_PREFERRED' | 'SDR_ONLY'
  codec_policy: 'ANY' | 'PREFER_H265' | 'PREFER_H264'
  subtitle_policy: 'ANY' | 'REQUIRE_ZH'
  audio_lang_policy: 'ANY' | 'ORIGINAL_PREFERRED' | 'AVOID_MANDARIN_ONLY'
  extra_feature_policy: 'ALLOW_3D' | 'FORBID_3D'
}

export interface ModeProfile {
  name: string
  description: string
  settings: Partial<GlobalRulesSettings>
}

export const globalRulesApi = {
  // 获取全局规则设置
  async getGlobalRules(): Promise<{ data: GlobalRulesSettings }> {
    const response = await api.get('/api/settings/rules/global')
    return response.data
  },

  // 更新全局规则设置
  async updateGlobalRules(settings: Partial<GlobalRulesSettings>): Promise<{ data: GlobalRulesSettings }> {
    const response = await api.put('/api/settings/rules/global', settings)
    return response.data
  },

  // 重置全局规则为默认值
  async resetGlobalRules(): Promise<{ data: GlobalRulesSettings }> {
    const response = await api.post('/api/settings/rules/global/reset')
    return response.data
  },

  // 获取预设模式配置
  async getModeProfiles(): Promise<{ data: ModeProfile[] }> {
    const response = await api.get('/api/settings/rules/global/mode-profiles')
    return response.data
  },

  // 应用预设模式
  async applyModeProfile(mode: 'A_SAFE' | 'B_BALANCED' | 'C_PRO'): Promise<{ data: GlobalRulesSettings }> {
    const response = await api.post(`/api/settings/rules/global/apply-mode/${mode}`)
    return response.data
  }
}
