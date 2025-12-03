/**
 * VabHub 主题配置
 * UX-2 U1-1 实现
 */

// 主色调
export const colors = {
  // 主色
  primary: '#1976D2',
  primaryDarken1: '#1565C0',
  primaryLighten1: '#42A5F5',
  
  // 辅色
  secondary: '#9C27B0',
  secondaryDarken1: '#7B1FA2',
  secondaryLighten1: '#BA68C8',
  
  // 功能色
  success: '#4CAF50',
  warning: '#FF9800',
  error: '#F44336',
  info: '#2196F3',
  
  // 媒体类型色
  novel: '#1976D2',      // 蓝色 - 小说
  audiobook: '#9C27B0',  // 紫色 - 有声书
  manga: '#FF9800',      // 橙色 - 漫画
  music: '#4CAF50',      // 绿色 - 音乐
  movie: '#F44336',      // 红色 - 电影
  series: '#00BCD4',     // 青色 - 剧集
}

// 圆角
export const borderRadius = {
  sm: '4px',
  md: '8px',
  lg: '12px',
  xl: '16px',
  pill: '9999px',
}

// 阴影
export const shadows = {
  soft: '0 2px 8px rgba(0, 0, 0, 0.08)',
  medium: '0 4px 16px rgba(0, 0, 0, 0.12)',
  strong: '0 8px 24px rgba(0, 0, 0, 0.16)',
}

// Vuetify 主题配置
export const lightTheme = {
  dark: false,
  colors: {
    primary: colors.primary,
    'primary-darken-1': colors.primaryDarken1,
    'primary-lighten-1': colors.primaryLighten1,
    secondary: colors.secondary,
    'secondary-darken-1': colors.secondaryDarken1,
    'secondary-lighten-1': colors.secondaryLighten1,
    success: colors.success,
    warning: colors.warning,
    error: colors.error,
    info: colors.info,
    background: '#FAFAFA',
    surface: '#FFFFFF',
    'surface-variant': '#F5F5F5',
    'on-surface': '#212121',
    'on-background': '#212121',
  },
}

export const darkTheme = {
  dark: true,
  colors: {
    primary: '#42A5F5',
    'primary-darken-1': '#1976D2',
    'primary-lighten-1': '#64B5F6',
    secondary: '#BA68C8',
    'secondary-darken-1': '#9C27B0',
    'secondary-lighten-1': '#CE93D8',
    success: '#66BB6A',
    warning: '#FFA726',
    error: '#EF5350',
    info: '#42A5F5',
    background: '#121212',
    surface: '#1E1E1E',
    'surface-variant': '#2D2D2D',
    'on-surface': '#E0E0E0',
    'on-background': '#E0E0E0',
  },
}

// 媒体类型图标映射
export const mediaTypeIcons: Record<string, string> = {
  novel: 'mdi-book-open-page-variant',
  ebook: 'mdi-book-open-page-variant',
  audiobook: 'mdi-headphones',
  manga: 'mdi-book-open-variant',
  comic: 'mdi-book-open-variant',
  music: 'mdi-music',
  movie: 'mdi-movie',
  series: 'mdi-television',
  tv: 'mdi-television',
}

// 媒体类型颜色映射
export const mediaTypeColors: Record<string, string> = {
  novel: colors.novel,
  ebook: colors.novel,
  audiobook: colors.audiobook,
  manga: colors.manga,
  comic: colors.manga,
  music: colors.music,
  movie: colors.movie,
  series: colors.series,
  tv: colors.series,
}

// 媒体类型标签映射
export const mediaTypeLabels: Record<string, string> = {
  novel: '小说',
  ebook: '电子书',
  audiobook: '有声书',
  manga: '漫画',
  comic: '漫画',
  music: '音乐',
  movie: '电影',
  series: '剧集',
  tv: '电视剧',
}

export default {
  colors,
  borderRadius,
  shadows,
  lightTheme,
  darkTheme,
  mediaTypeIcons,
  mediaTypeColors,
  mediaTypeLabels,
}
