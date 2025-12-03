/**
 * 小说阅读器偏好设置 Composable
 * 
 * 管理阅读主题、字号等偏好设置，并持久化到 localStorage
 */
import { ref, watch, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'

export type ReaderTheme = 'light' | 'dark' | 'sepia'
export type ReaderFontSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'

export interface NovelReaderPreferences {
  theme: ReaderTheme
  fontSize: ReaderFontSize
}

const DEFAULT_PREFERENCES: NovelReaderPreferences = {
  theme: 'light',
  fontSize: 'md'
}

const STORAGE_KEY_PREFIX = 'vabhub.novelReader.prefs'

// 节流保存到 localStorage（300ms）
let saveTimer: ReturnType<typeof setTimeout> | null = null
const SAVE_DELAY = 300

/**
 * 获取存储键名（包含用户ID）
 */
function getStorageKey(): string {
  const authStore = useAuthStore()
  const userId = authStore.user?.id || 'anonymous'
  return `${STORAGE_KEY_PREFIX}.${userId}`
}

/**
 * 从 localStorage 读取偏好设置
 */
function loadPreferences(): NovelReaderPreferences {
  try {
    const key = getStorageKey()
    const stored = localStorage.getItem(key)
    if (stored) {
      const parsed = JSON.parse(stored) as Partial<NovelReaderPreferences>
      return {
        ...DEFAULT_PREFERENCES,
        ...parsed
      }
    }
  } catch (error) {
    console.warn('读取阅读器偏好设置失败:', error)
  }
  return { ...DEFAULT_PREFERENCES }
}

/**
 * 保存偏好设置到 localStorage（节流）
 */
function savePreferences(prefs: NovelReaderPreferences) {
  if (saveTimer) {
    clearTimeout(saveTimer)
  }
  
  saveTimer = setTimeout(() => {
    try {
      const key = getStorageKey()
      localStorage.setItem(key, JSON.stringify(prefs))
    } catch (error) {
      console.warn('保存阅读器偏好设置失败:', error)
    }
    saveTimer = null
  }, SAVE_DELAY)
}

/**
 * 使用阅读器偏好设置的 Composable
 */
export function useNovelReaderPreferences() {
  const preferences = ref<NovelReaderPreferences>(loadPreferences())

  // 监听偏好变化，自动保存
  watch(
    preferences,
    (newPrefs) => {
      savePreferences(newPrefs)
    },
    { deep: true }
  )

  // 主题切换（循环：light → sepia → dark → light）
  const cycleTheme = () => {
    const themes: ReaderTheme[] = ['light', 'sepia', 'dark']
    const currentIndex = themes.indexOf(preferences.value.theme)
    const nextIndex = (currentIndex + 1) % themes.length
    preferences.value.theme = themes[nextIndex]
  }

  // 字号选项
  const fontSizeOptions: ReaderFontSize[] = ['xs', 'sm', 'md', 'lg', 'xl']

  // 减小字号
  const decreaseFontSize = () => {
    const currentIndex = fontSizeOptions.indexOf(preferences.value.fontSize)
    if (currentIndex > 0) {
      preferences.value.fontSize = fontSizeOptions[currentIndex - 1]
    }
  }

  // 增大字号
  const increaseFontSize = () => {
    const currentIndex = fontSizeOptions.indexOf(preferences.value.fontSize)
    if (currentIndex < fontSizeOptions.length - 1) {
      preferences.value.fontSize = fontSizeOptions[currentIndex + 1]
    }
  }

  // 是否最小字号
  const isMinFontSize = computed(() => {
    return preferences.value.fontSize === fontSizeOptions[0]
  })

  // 是否最大字号
  const isMaxFontSize = computed(() => {
    return preferences.value.fontSize === fontSizeOptions[fontSizeOptions.length - 1]
  })

  return {
    preferences,
    cycleTheme,
    decreaseFontSize,
    increaseFontSize,
    isMinFontSize,
    isMaxFontSize
  }
}

