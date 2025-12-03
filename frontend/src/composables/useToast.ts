/**
 * Toast通知组合式函数
 * 提供统一的Toast通知功能
 */

import { useToast as useVueToast } from 'vue-toastification'
import type { PluginOptions } from 'vue-toastification'

// vue-toastification 没有显式导出的 ToastOptions/ToastID 类型，这里做简易别名：
type ToastOptions = PluginOptions
type ToastID = number | string

interface ToastHandler {
  // 简洁别名（全局大量使用 toast.success/error/warning/info）
  success(message: string, options?: ToastOptions): ToastID
  error(message: string, options?: ToastOptions): ToastID
  warning(message: string, options?: ToastOptions): ToastID
  info(message: string, options?: ToastOptions): ToastID

  // 显式命名方法（原有导出）
  showSuccess(message: string, options?: ToastOptions): ToastID
  showError(message: string, options?: ToastOptions): ToastID
  showWarning(message: string, options?: ToastOptions): ToastID
  showInfo(message: string, options?: ToastOptions): ToastID

  showLoading(message: string, options?: ToastOptions): ToastID
  updateToast(toastId: ToastID, options: ToastOptions): void
  dismissToast(toastId?: ToastID): void
}

export function useToast(): ToastHandler {
  const toast = useVueToast()

  const showSuccess = (message: string, options?: ToastOptions) => {
    return toast.success(message, {
      timeout: 3000,
      ...options
    })
  }

  const showError = (message: string, options?: ToastOptions) => {
    return toast.error(message, {
      timeout: 5000,
      ...options
    })
  }

  const showWarning = (message: string, options?: ToastOptions) => {
    return toast.warning(message, {
      timeout: 4000,
      ...options
    })
  }

  const showInfo = (message: string, options?: ToastOptions) => {
    return toast.info(message, {
      timeout: 3000,
      ...options
    })
  }

  const showLoading = (message: string, options?: ToastOptions) => {
    // vue-toastification 本身未在类型定义中暴露 loading 方法，这里通过 any 访问，
    // 保持原有行为不变，仅解决类型检查问题。
    return (toast as any).loading(message, {
      timeout: false,
      ...options,
    }) as ToastID
  }

  const updateToast = (toastId: ToastID, options: ToastOptions) => {
    // 通过 any 调用以绕过复杂的重载签名，行为保持与原始 toast.update 一致
    (toast as any).update(toastId, options)
  }

  const dismissToast = (toastId?: ToastID) => {
    ;(toast as any).dismiss(toastId)
  }

  // 提供简洁别名，保持现有调用习惯（toast.success/error/...）
  const success = showSuccess
  const error = showError
  const warning = showWarning
  const info = showInfo

  return {
    success,
    error,
    warning,
    info,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    showLoading,
    updateToast,
    dismissToast,
  }
}

