/**
 * 通知状态管理 Store
 * NOTIFY-CENTER-1 P2: Notification Store 封装
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { notificationApi } from '@/services/api'
import type { UserNotificationItem, UserNotificationListResponse } from '@/types/notify'

export const useNotificationStore = defineStore('notification', () => {
  // ========== State ==========
  const notifications = ref<UserNotificationItem[]>([])
  const unreadCount = ref<number>(0)
  const isLoadingList = ref<boolean>(false)
  const isLoadingMarkAll = ref<boolean>(false)
  const hasMore = ref<boolean>(true)
  const currentPage = ref<number>(1)
  const pageSize = ref<number>(20)
  const total = ref<number>(0)
  const lastFetchTime = ref<number>(0)
  const error = ref<string | null>(null)
  const drawerOpen = ref<boolean>(false)
  const pollInterval = ref<number | null>(null)
  const isPolling = ref<boolean>(false)

  // ========== Computed ==========
  const hasUnreadNotifications = computed(() => unreadCount.value > 0)
  const unreadCountDisplay = computed(() => {
    if (unreadCount.value > 99) return '99+'
    return unreadCount.value.toString()
  })
  const isEmpty = computed(() => notifications.value.length === 0)
  const isLoading = computed(() => isLoadingList.value || isLoadingMarkAll.value)

  // ========== Actions ==========
  
  /**
   * 获取未读通知数量
   */
  const fetchUnreadCount = async (): Promise<void> => {
    try {
      error.value = null
      const response = await notificationApi.getUnreadCount()
      unreadCount.value = response.unread_count
    } catch (err) {
      console.error('获取未读通知数量失败:', err)
      error.value = '获取未读通知数量失败'
      throw err
    }
  }

  /**
   * 获取通知列表
   * @param options.fetchType 获取类型：'recent' | 'paginated'
   * @param options.reset 是否重置列表
   */
  const fetchNotifications = async (options: {
    fetchType?: 'recent' | 'paginated'
    reset?: boolean
  } = {}): Promise<void> => {
    const { fetchType = 'recent', reset = false } = options
    
    try {
      error.value = null
      isLoadingList.value = true
      
      if (reset) {
        notifications.value = []
        currentPage.value = 1
        hasMore.value = true
      }
      
      let response: UserNotificationListResponse
      
      if (fetchType === 'recent') {
        // 使用最近通知接口（适合抽屉快速加载）
        response = await notificationApi.getRecent(pageSize.value)
      } else {
        // 使用分页接口（适合完整列表页面）
        response = await notificationApi.list({
          page: currentPage.value,
          page_size: pageSize.value
        })
      }
      
      if (reset) {
        notifications.value = response.items
      } else {
        notifications.value.push(...response.items)
      }
      
      total.value = response.total
      unreadCount.value = response.unread_count
      lastFetchTime.value = Date.now()
      
      // 判断是否还有更多数据
      hasMore.value = notifications.value.length < total.value
      
    } catch (err) {
      console.error('获取通知列表失败:', err)
      error.value = '获取通知列表失败'
      throw err
    } finally {
      isLoadingList.value = false
    }
  }

  /**
   * 标记单条通知为已读
   * @param id 通知ID
   */
  const markNotificationAsRead = async (id: number): Promise<void> => {
    try {
      error.value = null
      
      // 先更新本地状态（乐观更新）
      const notification = notifications.value.find(n => n.id === id)
      if (notification && !notification.is_read) {
        notification.is_read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
      
      // 同步到后端
      await notificationApi.markRead(id)
      
    } catch (err) {
      console.error('标记通知为已读失败:', err)
      error.value = '标记通知为已读失败'
      
      // 回滚本地状态
      const notification = notifications.value.find(n => n.id === id)
      if (notification) {
        notification.is_read = false
        unreadCount.value += 1
      }
      
      throw err
    }
  }

  /**
   * 标记所有通知为已读
   */
  const markAllNotificationsAsRead = async (): Promise<void> => {
    try {
      error.value = null
      isLoadingMarkAll.value = true
      
      // 先更新本地状态（乐观更新）
      notifications.value.forEach(n => {
        n.is_read = true
      })
      unreadCount.value = 0
      
      // 同步到后端
      await notificationApi.markAllRead()
      
    } catch (err) {
      console.error('标记所有通知为已读失败:', err)
      error.value = '标记所有通知为已读失败'
      
      // 回滚本地状态并重新获取数据
      await fetchUnreadCount()
      await fetchNotifications({ reset: true })
      
      throw err
    } finally {
      isLoadingMarkAll.value = false
    }
  }

  /**
   * 打开通知抽屉
   */
  const openDrawer = async (): Promise<void> => {
    drawerOpen.value = true
    
    // 避免频繁重复请求（5秒内不重复请求）
    const now = Date.now()
    if (now - lastFetchTime.value > 5000 || notifications.value.length === 0) {
      await fetchNotifications({ reset: true })
    }
  }

  /**
   * 关闭通知抽屉
   */
  const closeDrawer = (): void => {
    drawerOpen.value = false
  }

  /**
   * 刷新通知数据
   */
  const refresh = async (): Promise<void> => {
    await Promise.all([
      fetchUnreadCount(),
      fetchNotifications({ reset: true })
    ])
  }

  /**
   * 清除错误状态
   */
  const clearError = (): void => {
    error.value = null
  }

  /**
   * 开始轮询未读数量
   * @param intervalMs 轮询间隔，默认30秒
   */
  const startPolling = (intervalMs: number = 30000): void => {
    stopPolling() // 先停止现有轮询
    
    isPolling.value = true
    pollInterval.value = setInterval(async () => {
      try {
        await fetchUnreadCount()
      } catch (err) {
        console.warn('轮询未读数量失败:', err)
      }
    }, intervalMs)
  }

  /**
   * 停止轮询
   */
  const stopPolling = (): void => {
    if (pollInterval.value) {
      clearInterval(pollInterval.value)
      pollInterval.value = null
    }
    isPolling.value = false
  }

  /**
   * 暂停轮询（用于页面隐藏等场景）
   */
  const pausePolling = (): void => {
    if (pollInterval.value) {
      clearInterval(pollInterval.value)
      pollInterval.value = null
    }
    // 保持 isPolling 状态，用于后续恢复
  }

  /**
   * 恢复轮询
   * @param intervalMs 轮询间隔，默认30秒
   */
  const resumePolling = (intervalMs: number = 30000): void => {
    if (isPolling.value && !pollInterval.value) {
      startPolling(intervalMs)
    }
  }

  return {
    // State
    notifications,
    unreadCount,
    isLoadingList,
    isLoadingMarkAll,
    hasMore,
    currentPage,
    pageSize,
    total,
    lastFetchTime,
    error,
    drawerOpen,
    pollInterval,
    isPolling,
    
    // Computed
    hasUnreadNotifications,
    unreadCountDisplay,
    isEmpty,
    isLoading,
    
    // Actions
    fetchUnreadCount,
    fetchNotifications,
    markNotificationAsRead,
    markAllNotificationsAsRead,
    openDrawer,
    closeDrawer,
    refresh,
    clearError,
    startPolling,
    stopPolling,
    pausePolling,
    resumePolling
  }
})
