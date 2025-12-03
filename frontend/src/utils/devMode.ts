/**
 * 开发者模式工具函数
 * 用于控制开发/调试功能的可见性
 */
export function isDevMode(): boolean {
  return import.meta.env.VITE_DEV_MODE === 'true'
}

