/**
 * Onboarding 类型定义
 * LAUNCH-1 L2-2 实现
 */

export interface OnboardingStatus {
  completed: boolean
  completed_at?: string | null
  completed_by?: string | null
}

export interface OnboardingSettings {
  language: string
  timezone: string
  adminUsername?: string
  adminPassword?: string
  adminEmail?: string
  ebookLibraryRoot: string
  comicLibraryRoot: string
  musicLibraryRoot: string
  ttsOutputRoot: string
}
