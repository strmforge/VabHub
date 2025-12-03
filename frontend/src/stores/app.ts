/**
 * 应用全局状态管理
 * UX-2 U2-1 增强：主题持久化
 * RELEASE-1 R0-1 增强：版本号与 Demo 模式
 */

import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { AppVersionInfo } from '@/types/app'

const THEME_STORAGE_KEY = 'vabhub-theme'

// 初始化主题
const getInitialTheme = (): 'light' | 'dark' => {
  const saved = localStorage.getItem(THEME_STORAGE_KEY)
  if (saved === 'light' || saved === 'dark') {
    return saved
  }
  // 检测系统偏好
  if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }
  return 'light'
}

export const useAppStore = defineStore('app', () => {
  // 版本信息
  const appVersion = ref<AppVersionInfo | null>(null)
  const isDemoMode = computed(() => appVersion.value?.demo_mode ?? false)
  
  // 主题（持久化）
  const theme = ref<'light' | 'dark'>(getInitialTheme())
  
  // 侧边栏
  const drawer = ref(true)
  
  // 加载状态
  const loading = ref(false)
  
  // 通知
  const unreadNotifications = ref(0)
  const notifications = ref<any[]>([])
  
  // 底部栏
  const showFooter = ref(false)
  
  // 音乐播放器
  const showMusicPlayer = ref(false)
  
  // 计算属性
  const isDark = computed(() => theme.value === 'dark')
  
  // 监听主题变化，保存到 localStorage
  watch(theme, (newTheme) => {
    localStorage.setItem(THEME_STORAGE_KEY, newTheme)
  })
  
  // 方法
  const toggleTheme = () => {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
  }
  
  const setTheme = (newTheme: 'light' | 'dark') => {
    theme.value = newTheme
  }
  
  const toggleDrawer = () => {
    drawer.value = !drawer.value
  }
  
  const setDrawer = (value: boolean) => {
    drawer.value = value
  }
  
  const setLoading = (value: boolean) => {
    loading.value = value
  }
  
  // 获取版本信息
  const fetchVersion = async () => {
    try {
      const { appApi } = await import('@/services/api')
      appVersion.value = await appApi.getVersion()
    } catch (error) {
      console.error('获取版本信息失败:', error)
    }
  }
  
  // 消息提示方法
  const showSuccessMessage = (message: string) => {
    // 这里可以集成具体的提示组件，如Vuetify的snackbar
    console.log('Success:', message)
    // 实际实现中应该触发全局消息提示
  }
  
  const showErrorMessage = (message: string) => {
    console.error('Error:', message)
    // 实际实现中应该触发全局错误提示
  }
  
  const showConfirmDialog = async (options: {
    title: string
    message: string
    confirmText?: string
    cancelText?: string
    type?: 'info' | 'warning' | 'error'
  }): Promise<boolean> => {
    // 这里应该显示确认对话框并返回用户选择
    // 暂时返回true用于开发测试
    return confirm(`${options.title}\n\n${options.message}`)
  }
  
  return {
    appVersion,
    isDemoMode,
    theme,
    drawer,
    loading,
    unreadNotifications,
    notifications,
    showFooter,
    showMusicPlayer,
    isDark,
    toggleTheme,
    setTheme,
    toggleDrawer,
    setDrawer,
    setLoading,
    fetchVersion,
    showSuccessMessage,
    showErrorMessage,
    showConfirmDialog
  }
})

