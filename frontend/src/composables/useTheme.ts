/**
 * 主题切换 Composable
 * UX-2 U2-1 实现
 */

import { ref, watch, onMounted } from 'vue'
import { useTheme as useVuetifyTheme } from 'vuetify'

const THEME_STORAGE_KEY = 'vabhub-theme'

// 全局状态（跨组件共享）
const isDark = ref(false)

export function useTheme() {
  const vuetifyTheme = useVuetifyTheme()

  // 初始化主题
  const initTheme = () => {
    // 1. 从 localStorage 读取用户偏好
    const savedTheme = localStorage.getItem(THEME_STORAGE_KEY)
    
    if (savedTheme) {
      isDark.value = savedTheme === 'dark'
    } else {
      // 2. 检测系统偏好
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
      isDark.value = prefersDark
    }
    
    // 应用主题
    applyTheme()
  }

  // 应用主题到 Vuetify
  const applyTheme = () => {
    vuetifyTheme.global.name.value = isDark.value ? 'dark' : 'light'
  }

  // 切换主题
  const toggleTheme = () => {
    isDark.value = !isDark.value
    localStorage.setItem(THEME_STORAGE_KEY, isDark.value ? 'dark' : 'light')
    applyTheme()
  }

  // 设置主题
  const setTheme = (theme: 'light' | 'dark') => {
    isDark.value = theme === 'dark'
    localStorage.setItem(THEME_STORAGE_KEY, theme)
    applyTheme()
  }

  // 监听系统主题变化
  onMounted(() => {
    initTheme()
    
    // 监听系统主题变化
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    mediaQuery.addEventListener('change', (e) => {
      // 只有在用户没有手动设置过主题时才跟随系统
      if (!localStorage.getItem(THEME_STORAGE_KEY)) {
        isDark.value = e.matches
        applyTheme()
      }
    })
  })

  // 监听 isDark 变化
  watch(isDark, () => {
    applyTheme()
  })

  return {
    isDark,
    toggleTheme,
    setTheme,
    initTheme,
  }
}
