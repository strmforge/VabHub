// 全局规则设置相关类型定义

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
  created_at?: string
  updated_at?: string
}

export interface ModeProfile {
  name: string
  description: string
  settings: Partial<GlobalRulesSettings>
}

export interface HrModeOption {
  value: 'A_SAFE' | 'B_BALANCED' | 'C_PRO'
  title: string
  description: string
  icon: string
  color: string
  warning?: string
}

export interface PolicyOption {
  value: string
  title: string
  description: string
}

export interface GlobalRulesFormState {
  loading: boolean
  saving: boolean
  resetting: boolean
  settings: GlobalRulesSettings
}

// HR模式配置
export const HR_MODE_CONFIG: Record<GlobalRulesSettings['hr_mode'], HrModeOption> = {
  A_SAFE: {
    value: 'A_SAFE',
    title: 'A档',
    description: '保种安全模式',
    icon: 'mdi-shield-outline',
    color: 'info'
  },
  B_BALANCED: {
    value: 'B_BALANCED',
    title: 'B档',
    description: '平衡模式',
    icon: 'mdi-balance',
    color: 'success'
  },
  C_PRO: {
    value: 'C_PRO',
    title: 'C档',
    description: '老司机模式',
    icon: 'mdi-fire',
    color: 'warning',
    warning: '如使用，系统将禁用『网盘移动上传』或『本地移动保存』，避免导致保种炸雷，请谨慎使用。'
  }
}

// HR策略选项
export const HR_POLICY_OPTIONS: PolicyOption[] = [
  {
    value: 'IGNORE',
    title: '忽略',
    description: '完全不管HR，显示所有种子'
  },
  {
    value: 'SAFE_SKIP',
    title: '安全跳过',
    description: '默认跳过H&R/HR等高风险种子'
  },
  {
    value: 'STRICT_SKIP',
    title: '严格跳过',
    description: '跳过H&R/HR/H3/H5/UNKNOWN等所有HR种子'
  }
]

// 分辨率策略选项
export const RESOLUTION_POLICY_OPTIONS: PolicyOption[] = [
  {
    value: 'AUTO',
    title: '自动选择',
    description: '根据档位和内容类型自动选择合适分辨率'
  },
  {
    value: 'MAX_TIER',
    title: '最高档位',
    description: '只限制最高分辨率，允许低分辨率'
  },
  {
    value: 'FIXED_TIER',
    title: '固定档位',
    description: '只选择指定分辨率档位的种子'
  }
]

// 分辨率档位选项
export const RESOLUTION_TIER_OPTIONS: PolicyOption[] = [
  {
    value: 'LOW_720P',
    title: '720p及以下',
    description: '低分辨率档位'
  },
  {
    value: 'MID_1080P',
    title: '1080p及以下',
    description: '中等分辨率档位'
  },
  {
    value: 'HIGH_4K',
    title: '4K及以下',
    description: '高分辨率档位'
  }
]

// 源质量策略选项
export const SOURCE_QUALITY_OPTIONS: PolicyOption[] = [
  {
    value: 'ANY',
    title: '任意',
    description: '不限制源质量'
  },
  {
    value: 'NO_TRASH',
    title: '禁用低质',
    description: '禁用CAM/TS/TC等明显低质量源'
  },
  {
    value: 'HIGH_ONLY',
    title: '仅高质量',
    description: '只要REMUX/BLURAY/UHD/高码WEB-DL'
  }
]

// HDR策略选项
export const HDR_POLICY_OPTIONS: PolicyOption[] = [
  {
    value: 'ANY',
    title: '任意',
    description: '不限制HDR或SDR'
  },
  {
    value: 'HDR_PREFERRED',
    title: 'HDR优先',
    description: '优先HDR，但不强制'
  },
  {
    value: 'SDR_ONLY',
    title: '仅SDR',
    description: '只选择SDR版本'
  }
]

// 编码策略选项
export const CODEC_POLICY_OPTIONS: PolicyOption[] = [
  {
    value: 'ANY',
    title: '任意',
    description: '不限制编码格式'
  },
  {
    value: 'PREFER_H265',
    title: 'H265优先',
    description: '优先H265/HEVC编码'
  },
  {
    value: 'PREFER_H264',
    title: 'H264优先',
    description: '优先H264/AVC编码'
  }
]

// 字幕策略选项
export const SUBTITLE_POLICY_OPTIONS: PolicyOption[] = [
  {
    value: 'ANY',
    title: '任意',
    description: '不限制字幕'
  },
  {
    value: 'REQUIRE_ZH',
    title: '必须中文',
    description: '必须包含简体或繁体中文字幕'
  }
]

// 音轨策略选项
export const AUDIO_LANG_POLICY_OPTIONS: PolicyOption[] = [
  {
    value: 'ANY',
    title: '任意',
    description: '不限制音轨语言'
  },
  {
    value: 'ORIGINAL_PREFERRED',
    title: '原声优先',
    description: '优先原语言+多轨'
  },
  {
    value: 'AVOID_MANDARIN_ONLY',
    title: '避开纯国语',
    description: '尽量避开只有国语配音的版本'
  }
]

// 3D策略选项
export const EXTRA_FEATURE_POLICY_OPTIONS: PolicyOption[] = [
  {
    value: 'ALLOW_3D',
    title: '允许3D',
    description: '包含3D版本'
  },
  {
    value: 'FORBID_3D',
    title: '禁止3D',
    description: '过滤掉所有3D版本'
  }
]
