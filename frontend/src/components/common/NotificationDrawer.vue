<template>
  <v-navigation-drawer
    v-model="drawerOpen"
    location="right"
    temporary
    width="400"
    @update:modelValue="handleDrawerChange"
  >
    <!-- 头部 -->
    <v-card-title class="d-flex align-center pa-4">
      <v-icon class="mr-2">mdi-bell</v-icon>
      通知中心
      <v-chip 
        v-if="hasUnreadNotifications" 
        size="small" 
        color="primary" 
        class="ml-2"
      >
        {{ unreadCountDisplay }}
      </v-chip>
      <v-spacer />
      <v-btn
        icon
        size="small"
        variant="text"
        :loading="isLoadingMarkAll"
        :disabled="!hasUnreadNotifications || isLoading"
        @click="handleMarkAllAsRead"
      >
        <v-icon>mdi-check-all</v-icon>
        <v-tooltip activator="parent">全部标记为已读</v-tooltip>
      </v-btn>
    </v-card-title>
    
    <!-- 分类快速过滤 -->
    <v-card-text class="pa-3 pt-0">
      <div class="d-flex align-center mb-2">
        <span class="text-caption text-medium-emphasis mr-2">快速筛选：</span>
      </div>
      <div class="category-chip-group">
        <v-chip
          v-for="category in categoryOptions"
          :key="category.value"
          :color="selectedCategory === category.value ? category.color : 'default'"
          :variant="selectedCategory === category.value ? 'flat' : 'outlined'"
          size="small"
          class="mr-2 mb-2"
          @click="handleCategoryFilter(category.value)"
        >
          <v-icon start :icon="category.icon" size="x-small"></v-icon>
          {{ category.label }}
          <v-chip
            v-if="categoryUnreadCount[category.value] > 0"
            size="x-small"
            :color="selectedCategory === category.value ? 'on-primary' : category.color"
            class="ml-1"
          >
            {{ categoryUnreadCount[category.value] }}
          </v-chip>
        </v-chip>
        <v-chip
          v-if="selectedCategory"
          size="small"
          variant="text"
          @click="handleCategoryFilter(null)"
        >
          <v-icon start icon="mdi-close" size="x-small"></v-icon>
          清除
        </v-chip>
      </div>
    </v-card-text>
    
    <v-divider />
    
    <!-- 内容区域 -->
    <div class="notification-drawer-content">
      <!-- 加载状态 -->
      <div v-if="isLoadingList" class="text-center py-8">
        <v-progress-circular indeterminate color="primary" size="24" />
        <p class="text-body-2 text-medium-emphasis mt-2">加载中...</p>
      </div>
      
      <!-- 错误状态 -->
      <div v-else-if="error" class="text-center py-8">
        <v-icon size="48" color="error">mdi-alert-circle</v-icon>
        <p class="text-body-2 text-error mt-2">{{ error }}</p>
        <v-btn size="small" variant="outlined" @click="handleRetry">
          重试
        </v-btn>
      </div>
      
      <!-- 通知列表 -->
      <v-list v-else-if="!isEmpty" class="notification-list">
        <v-list-item
          v-for="notification in notifications"
          :key="notification.id"
          :class="{ 'notification-unread': !notification.is_read }"
          :title="notification.title"
          :subtitle="notification.message"
          @click="handleNotificationClick(notification)"
        >
          <template #prepend>
            <v-icon :color="getCategoryColor(notification.category)">
              {{ getCategoryIcon(notification.category) }}
            </v-icon>
          </template>
          <template v-slot:append>
            <div class="d-flex align-center">
              <!-- 分类标签 -->
              <v-chip
                :color="getCategoryColor(notification.category)"
                size="x-small"
                variant="flat"
                class="mr-2"
              >
                {{ getCategoryLabel(notification.category) }}
              </v-chip>
              <!-- 未读标识 -->
              <v-chip
                v-if="!notification.is_read"
                size="x-small"
                color="primary"
                variant="flat"
                class="mr-2"
              />
              <!-- 时间 -->
              <span class="text-caption text-medium-emphasis">
                {{ formatTime(notification.created_at) }}
              </span>
            </div>
          </template>
        </v-list-item>
        
        <!-- 加载更多 -->
        <v-list-item v-if="hasMore && !isLoadingList" class="text-center">
          <v-btn
            variant="outlined"
            size="small"
            :loading="isLoadingList"
            @click="handleLoadMore"
          >
            加载更多
          </v-btn>
        </v-list-item>
      </v-list>
      
      <!-- 空状态 -->
      <div v-else class="text-center py-8">
        <v-icon size="64" color="grey-lighten-1">mdi-bell-outline</v-icon>
        <p class="text-h6 mb-2">暂无通知</p>
        <p class="text-body-2 text-medium-emphasis mb-4">
          {{ selectedCategory ? '该分类下暂无通知' : '当前没有任何通知消息' }}
        </p>
        <v-btn
          variant="outlined"
          prepend-icon="mdi-home"
          @click="handleGoHome"
        >
          去首页看看
        </v-btn>
      </div>
    </div>
    
    <!-- 底部操作 -->
    <template v-slot:append>
      <v-divider />
      <div class="pa-3">
        <v-btn
          block
          variant="elevated"
          color="primary"
          prepend-icon="mdi-view-dashboard"
          class="mb-2"
          @click="handleGoToFullPage"
        >
          查看全部通知
        </v-btn>
        <v-btn
          block
          variant="text"
          size="small"
          prepend-icon="mdi-cog"
          @click="handleGoToSettings"
        >
          通知设置
        </v-btn>
      </div>
    </template>
  </v-navigation-drawer>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { notificationApi } from '@/services/api'
import { useNotificationStore } from '@/stores/notification'
import type { UserNotificationItem, NotificationCategory } from '@/types/notify'

interface Props {
  modelValue: boolean
}

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
}>()

const router = useRouter()
const notificationStore = useNotificationStore()

// ========== 响应式数据 ==========
const drawerOpen = computed({
  get: () => notificationStore.drawerOpen,
  set: (value) => {
    if (value) {
      notificationStore.openDrawer()
    } else {
      notificationStore.closeDrawer()
    }
  }
})

// 分类过滤状态
const selectedCategory = ref<NotificationCategory | null>(null)
const categoryUnreadCount = ref<Record<string, number>>({
  reading: 0,
  download: 0,
  music: 0,
  plugin: 0,
  system: 0,
  other: 0
})

// 分类选项
const categoryOptions = [
  { value: 'reading' as NotificationCategory, label: '阅读', icon: 'mdi-book-open-variant', color: 'primary' },
  { value: 'download' as NotificationCategory, label: '下载', icon: 'mdi-download', color: 'success' },
  { value: 'music' as NotificationCategory, label: '音乐', icon: 'mdi-music', color: 'purple' },
  { value: 'plugin' as NotificationCategory, label: '插件', icon: 'mdi-puzzle', color: 'orange' },
  { value: 'system' as NotificationCategory, label: '系统', icon: 'mdi-cog', color: 'grey' },
  { value: 'other' as NotificationCategory, label: '其他', icon: 'mdi-bell', color: 'blue-grey' }
]

// ========== Store 计算属性 ==========
const notifications = computed(() => notificationStore.notifications)
const unreadCountDisplay = computed(() => notificationStore.unreadCountDisplay)
const hasUnreadNotifications = computed(() => notificationStore.hasUnreadNotifications)
const isLoadingList = computed(() => notificationStore.isLoadingList)
const isLoadingMarkAll = computed(() => notificationStore.isLoadingMarkAll)
const isLoading = computed(() => notificationStore.isLoading)
const hasMore = computed(() => notificationStore.hasMore)
const error = computed(() => notificationStore.error)
const isEmpty = computed(() => notificationStore.isEmpty)

// ========== 工具函数 ==========
const getCategoryColor = (category: NotificationCategory) => {
  const colorMap: Record<NotificationCategory, string> = {
    reading: 'primary',
    download: 'success',
    music: 'purple',
    plugin: 'orange',
    system: 'grey',
    other: 'blue-grey'
  }
  return colorMap[category] || 'grey'
}

const getCategoryLabel = (category: NotificationCategory) => {
  const labelMap: Record<NotificationCategory, string> = {
    reading: '阅读',
    download: '下载',
    music: '音乐',
    plugin: '插件',
    system: '系统',
    other: '其他'
  }
  return labelMap[category] || '其他'
}

const getCategoryIcon = (category: NotificationCategory) => {
  const iconMap: Record<NotificationCategory, string> = {
    reading: 'mdi-book-open-variant',
    download: 'mdi-download',
    music: 'mdi-music',
    plugin: 'mdi-puzzle',
    system: 'mdi-cog',
    other: 'mdi-bell'
  }
  return iconMap[category] || 'mdi-bell'
}

const formatTime = (timeStr: string): string => {
  const time = new Date(timeStr)
  const now = new Date()
  const diffMs = now.getTime() - time.getTime()
  const diffMins = Math.floor(diffMs / (1000 * 60))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins}分钟前`
  if (diffHours < 24) return `${diffHours}小时前`
  if (diffDays < 7) return `${diffDays}天前`
  return time.toLocaleDateString('zh-CN')
}

// 加载分类未读数量
const loadCategoryUnreadCount = async () => {
  try {
    const response = await notificationApi.getCategoryUnreadCount()
    categoryUnreadCount.value = response.unread_by_category || {
      reading: 0,
      download: 0,
      music: 0,
      plugin: 0,
      system: 0,
      other: 0
    }
  } catch (error) {
    console.error('加载分类未读数量失败:', error)
  }
}

// ========== 事件处理函数 ==========
const handleDrawerChange = (value: boolean) => {
  if (value !== notificationStore.drawerOpen) {
    if (value) {
      notificationStore.openDrawer()
    } else {
      notificationStore.closeDrawer()
    }
  }
}

// 分类过滤处理
const handleCategoryFilter = async (category: NotificationCategory | null) => {
  selectedCategory.value = category
  await loadFilteredNotifications()
}

// 加载过滤后的通知
const loadFilteredNotifications = async () => {
  try {
    const params: any = {
      limit: 20,
      offset: 0
    }
    
    if (selectedCategory.value) {
      params.category = selectedCategory.value
    }
    
    // 直接使用API而不是store，因为store不支持分类过滤
    const response = await notificationApi.list(params)
    
    // 更新store的临时数据（不使用store的分页逻辑）
    notificationStore.notifications = response.items
    notificationStore.unreadCount = response.unread_count
    
  } catch (error) {
    console.error('加载过滤通知失败:', error)
  }
}

const handleNotificationClick = async (notification: UserNotificationItem) => {
  try {
    // 标记为已读
    if (!notification.is_read) {
      await notificationStore.markNotificationAsRead(notification.id)
      // 更新分类未读数量
      await loadCategoryUnreadCount()
    }
    
    // 根据通知类型跳转到对应页面
    await handleNotificationNavigation(notification)
    
    // 关闭抽屉
    notificationStore.closeDrawer()
    
  } catch (err) {
    console.error('处理通知点击失败:', err)
  }
}

const handleNotificationNavigation = async (notification: UserNotificationItem) => {
  const { type, ebook_id, tts_job_id, media_type, payload } = notification
  
  // 根据通知类型和关联数据跳转
  switch (type) {
    case 'TTS_JOB_COMPLETED':
    case 'TTS_JOB_FAILED':
      if (tts_job_id) {
        router.push({ name: 'TtsJobsPage' })
      }
      break
      
    case 'AUDIOBOOK_READY':
    case 'AUDIOBOOK_NEW_TRACK':
      if (ebook_id) {
        router.push({ 
          name: 'AudiobookDetail', 
          params: { id: ebook_id } 
        })
      } else {
        router.push({ name: 'AudiobookCenter' })
      }
      break
      
    case 'MANGA_NEW_CHAPTER':
    case 'MANGA_UPDATED':
      if (media_type === 'manga') {
        router.push({ name: 'MangaCenter' })
      }
      break
      
    case 'NOVEL_NEW_CHAPTER':
      if (media_type === 'novel') {
        router.push({ name: 'NovelCenter' })
      }
      break
      
    case 'DOWNLOAD_SUBSCRIPTION_MATCHED':
    case 'DOWNLOAD_TASK_COMPLETED':
    case 'DOWNLOAD_HR_RISK':
      // 下载通知使用 payload 中的路由信息
      if (payload?.route_name) {
        router.push({ 
          name: payload.route_name, 
          params: payload.route_params || {} 
        })
      } else {
        // 默认跳转到下载任务页面
        router.push({ name: 'DownloadTasksPage' })
      }
      break
      
    case 'SYSTEM_MESSAGE':
      // 系统消息跳转到设置页面
      router.push({ name: 'Settings' })
      break
      
    default:
      // 默认跳转到首页
      router.push({ name: 'Home' })
  }
}

const handleMarkAllAsRead = async () => {
  try {
    if (selectedCategory.value) {
      // 按分类标记已读
      await notificationApi.markCategoryRead(selectedCategory.value)
    } else {
      // 标记所有已读
      await notificationStore.markAllNotificationsAsRead()
    }
    // 刷新通知列表和分类未读数量
    await Promise.all([
      loadFilteredNotifications(),
      loadCategoryUnreadCount()
    ])
  } catch (err) {
    console.error('标记所有通知为已读失败:', err)
  }
}

const handleLoadMore = async () => {
  try {
    notificationStore.currentPage += 1
    await notificationStore.fetchNotifications({ 
      fetchType: 'paginated', 
      reset: false 
    })
  } catch (err) {
    console.error('加载更多通知失败:', err)
  }
}

const handleRetry = async () => {
  try {
    notificationStore.clearError()
    await loadFilteredNotifications()
  } catch (err) {
    console.error('重试失败:', err)
  }
}

const handleGoHome = () => {
  notificationStore.closeDrawer()
  router.push({ name: 'Home' })
}

const handleGoToSettings = () => {
  notificationStore.closeDrawer()
  router.push({ name: 'UserNotifyPreferencesPage' })
}

// 跳转到全屏页
const handleGoToFullPage = () => {
  notificationStore.closeDrawer()
  
  // 构建查询参数
  const query: any = {}
  if (selectedCategory.value) {
    query.category = selectedCategory.value
  }
  
  router.push({ 
    name: 'UserNotifications', 
    query 
  })
}

// 监听抽屉打开状态，加载分类未读数量
watch(() => drawerOpen.value, async (isOpen) => {
  if (isOpen) {
    await Promise.all([
      loadCategoryUnreadCount(),
      loadFilteredNotifications()
    ])
  }
})

// ========== 生命周期 ==========
onMounted(() => {
  // 组件挂载时获取未读数量
  notificationStore.fetchUnreadCount()
})
</script>

<style scoped>
.notification-drawer-content {
  height: calc(100vh - 120px);
  overflow-y: auto;
}

.notification-list {
  padding: 0;
}

.notification-unread {
  background-color: rgba(var(--v-theme-primary), 0.08);
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.notification-unread:hover {
  background-color: rgba(var(--v-theme-primary), 0.12);
}

/* 自定义滚动条 */
.notification-drawer-content::-webkit-scrollbar {
  width: 4px;
}

.notification-drawer-content::-webkit-scrollbar-track {
  background: transparent;
}

.notification-drawer-content::-webkit-scrollbar-thumb {
  background: rgba(var(--v-theme-on-surface), 0.2);
  border-radius: 2px;
}

.notification-drawer-content::-webkit-scrollbar-thumb:hover {
  background: rgba(var(--v-theme-on-surface), 0.3);
}

/* 通知项悬停效果 */
.v-list-item {
  transition: background-color 0.2s ease;
}

.v-list-item:hover {
  background-color: rgba(var(--v-theme-on-surface), 0.04);
}

/* 未读标识动画 */
.v-chip.v-chip--size-x-small {
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
  100% {
    opacity: 1;
  }
}

/* 加载状态样式 */
.text-center.py-8 .v-progress-circular {
  margin-bottom: 8px;
}

/* 空状态样式 */
.text-center.py-8 .v-icon {
  margin-bottom: 16px;
}

/* 底部操作区域样式 */
.v-navigation-drawer__append {
  border-top: 1px solid rgba(var(--v-border-color), 0.12);
}
</style>

