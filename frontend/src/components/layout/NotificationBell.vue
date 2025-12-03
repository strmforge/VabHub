<template>
  <div class="notification-bell">
    <v-menu
      v-model="menuOpen"
      location="bottom end"
      :close-on-content-click="false"
      :close-on-back="true"
      max-width="400"
      @update:model-value="onMenuToggle"
    >
      <template v-slot:activator="{ props }">
        <v-btn
          icon
          variant="text"
          v-bind="props"
          @click="loadNotifications"
        >
          <v-badge
            :content="unreadCount > 0 ? unreadCount : undefined"
            :model-value="unreadCount > 0"
            color="error"
            :max="99"
          >
            <v-icon>{{ unreadCount > 0 ? 'mdi-bell' : 'mdi-bell-outline' }}</v-icon>
          </v-badge>
        </v-btn>
      </template>

      <v-card>
        <v-card-title class="d-flex align-center">
          <v-icon class="mr-2">mdi-bell</v-icon>
          <span>通知中心</span>
          <v-spacer />
          <v-btn
            v-if="unreadCount > 0"
            icon
            size="small"
            variant="text"
            @click="handleMarkAllRead"
            :loading="markingRead"
          >
            <v-icon>mdi-check-all</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />

        <v-card-text class="pa-0" style="max-height: 400px; overflow-y: auto;">
          <!-- 加载状态 -->
          <div v-if="loading" class="pa-4">
            <div v-for="n in 3" :key="n" class="mb-3">
              <v-skeleton-loader type="list-item-avatar-two-line"></v-skeleton-loader>
            </div>
          </div>
          
          <!-- 通知列表 -->
          <v-list v-else-if="notifications.length > 0" density="compact">
            <v-list-item
              v-for="item in notifications.slice(0, 8)"
              :key="item.id"
              :class="{ 
                'notification-item-unread': !item.is_read,
                'notification-item-error': item.type === 'TTS_JOB_FAILED' || item.type === 'MANGA_SYNC_FAILED'
              }"
              @click="handleNotificationClick(item)"
            >
              <template v-slot:prepend>
                <!-- 未读状态指示器 -->
                <div v-if="!item.is_read" class="unread-indicator">
                  <v-icon color="warning" size="x-small">mdi-circle</v-icon>
                </div>
                <v-icon
                  :color="getNotificationColor(item)"
                  size="small"
                  class="ml-1"
                >
                  {{ getNotificationIcon(item) }}
                </v-icon>
              </template>

              <v-list-item-title class="text-body-2" :class="{ 'font-weight-bold': !item.is_read }">
                {{ item.title }}
              </v-list-item-title>
              
              <v-list-item-subtitle class="text-caption">
                {{ item.message }}
              </v-list-item-subtitle>
              
              <v-list-item-subtitle class="text-caption text-medium-emphasis mt-1">
                <div class="d-flex align-center flex-wrap ga-1">
                  <!-- 通知类型标签 -->
                  <v-chip
                    v-if="getNotificationTag(item)"
                    :color="getNotificationColor(item)"
                    size="x-small"
                    variant="flat"
                    class="font-weight-medium"
                  >
                    {{ getNotificationTag(item) }}
                  </v-chip>
                  
                  <!-- 来源标签 -->
                  <v-chip
                    :color="getSourceColor(inferNotificationSource(item))"
                    size="x-small"
                    variant="flat"
                  >
                    {{ getSourceLabel(inferNotificationSource(item)) }}
                  </v-chip>
                  
                  <!-- 时间显示 -->
                  <v-tooltip location="bottom">
                    <template #activator="{ props }">
                      <span v-bind="props" class="text-caption text-medium-emphasis">
                        {{ formatRelativeTime(item.created_at) }}
                      </span>
                    </template>
                    <span>{{ formatFullTime(item.created_at) }}</span>
                  </v-tooltip>
                </div>
              </v-list-item-subtitle>

              <!-- BOT-EXT-2: 动作按钮 -->
              <div
                v-if="item.actions && item.actions.length > 0"
                class="d-flex flex-wrap ga-1 mt-2"
              >
                <v-btn
                  v-for="action in item.actions.slice(0, 3)"
                  :key="action.id"
                  size="x-small"
                  variant="tonal"
                  :color="action.primary ? 'primary' : 'default'"
                  @click.stop="handleActionClick(action)"
                >
                  <v-icon v-if="action.icon" size="14" class="mr-1">{{ action.icon }}</v-icon>
                  {{ action.label }}
                </v-btn>
              </div>

              <template v-slot:append>
                <div class="d-flex align-center">
                  <!-- 错误状态指示器 -->
                  <v-icon
                    v-if="item.type === 'TTS_JOB_FAILED' || item.type === 'MANGA_SYNC_FAILED'"
                    size="small"
                    color="error"
                    class="ml-1"
                  >
                    mdi-alert
                  </v-icon>
                </div>
              </template>
            </v-list-item>
          </v-list>

          <!-- 空状态 -->
          <div v-else class="text-center pa-8 text-medium-emphasis">
            <v-icon size="48" color="grey-lighten-1" class="mb-2">mdi-bell-off</v-icon>
            <div class="text-body-2 mb-2">暂无通知</div>
            <div class="text-caption">当有新的TTS任务或系统通知时，会在这里显示</div>
          </div>
        </v-card-text>

        <v-divider />
        <v-card-actions class="px-4 py-3 border-t">
          <div class="d-flex align-center justify-space-between w-100">
            <div class="d-flex align-center">
              <v-btn
                v-if="unreadCount > 0"
                color="primary"
                variant="text"
                size="small"
                prepend-icon="mdi-check-all"
                @click="handleMarkAllRead"
                :loading="markingRead"
              >
                全部标记为已读
              </v-btn>
            </div>
            
            <div class="d-flex align-center ga-2">
              <v-btn
                color="grey"
                variant="text"
                size="small"
                prepend-icon="mdi-cog"
                @click="goToPreferencesPage"
              >
                设置
              </v-btn>
              
              <v-btn
                color="primary"
                variant="text"
                size="small"
                prepend-icon="mdi-bell"
                @click="goToNotificationsPage"
              >
                查看全部
              </v-btn>
              
              <v-btn
                color="grey"
                variant="text"
                size="small"
                @click="menuOpen = false"
              >
                关闭
              </v-btn>
            </div>
          </div>
        </v-card-actions>
      </v-card>
    </v-menu>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationStore } from '@/stores/notification'
import { mangaFollowApi } from '@/services/api'
import type { UserNotificationItem, NotificationAction } from '@/types/notify'
import { inferNotificationSource } from '@/types/notify'
import { useToast } from 'vue-toastification'

const toast = useToast()
const router = useRouter()
const notificationStore = useNotificationStore()

// 本地状态
const menuOpen = ref(false)

// Store 计算属性
const notifications = computed(() => notificationStore.notifications)
const unreadCount = computed(() => notificationStore.unreadCount)
const loading = computed(() => notificationStore.isLoadingList)
const markingRead = computed(() => notificationStore.isLoadingMarkAll)

// 加载通知列表（使用 store）
const loadNotifications = async () => {
  try {
    await notificationStore.fetchNotifications({ reset: true })
  } catch (error: any) {
    console.error('加载通知失败:', error)
    toast.error('加载通知失败')
  }
}


// 菜单开关回调
const onMenuToggle = (value: boolean) => {
  menuOpen.value = value
  if (value && !loading.value) {
    void loadNotifications()
  }
}

// 标记全部为已读（使用 store）
const handleMarkAllRead = async () => {
  try {
    await notificationStore.markAllNotificationsAsRead()
  } catch (error: any) {
    console.error('标记已读失败:', error)
    toast.error('标记已读失败')
  }
}

// 点击通知项（使用 store）
const handleNotificationClick = async (item: UserNotificationItem) => {
  try {
    // 如果未读，标记为已读
    if (!item.is_read) {
      await notificationStore.markNotificationAsRead(item.id)
    }
    
    // 如果是漫画更新通知，优先按漫画逻辑处理
    if (item.type === 'MANGA_UPDATED') {
      const payload = item.payload || {}
      const seriesId = (payload as any).series_id || (payload as any).seriesId || item.target_id

      if (seriesId) {
        // 可选：后台标记已读，不阻塞跳转
        try {
          void mangaFollowApi.markSeriesRead(seriesId as number)
        } catch (e) {
          console.error('Failed to mark series read from notification', e)
        }

        if ((payload as any).route_name && (payload as any).route_params) {
          router.push({
            name: (payload as any).route_name,
            params: (payload as any).route_params,
            query: (payload as any).extra?.query || {}
          })
        } else {
          router.push({
            name: 'MangaReaderPage',
            params: { series_id: String(seriesId) }
          })
        }
      } else {
        // 旧通知或缺少 seriesId，退回追更中心
        router.push({ name: 'MangaFollowCenter' })
      }
    } else if (item.payload?.route_name && item.payload.route_params) {
      // 使用payload中的路由信息跳转（包含params和可选 query）
      router.push({
        name: item.payload.route_name,
        params: item.payload.route_params,
        query: item.payload.extra?.query || {}
      })
    } else if (item.media_type === 'manga' && item.target_id) {
      // 漫画通知：优先跳转到阅读器
      router.push({ name: 'MangaReaderPage', params: { series_id: String(item.target_id) } })
    } else if (item.media_type === 'audiobook' && item.target_id) {
      // 兜底：跳到有声书详情
      router.push({ name: 'AudiobookDetail', params: { id: item.target_id } })
    } else if (item.ebook_id) {
      // 如果有 ebook_id，跳转到作品详情页（TTS通知的默认跳转）
      router.push({ name: 'WorkDetail', params: { ebookId: item.ebook_id } })
    } else {
      // 如果没有路由信息，跳转到通知详情页或默认页面
      console.warn('通知缺少路由信息，跳转到默认通知页面')
      router.push({ name: 'UserNotifications' })
    }
    
    // 关闭菜单
    menuOpen.value = false
  } catch (error: any) {
    console.error('处理通知点击失败:', error)
    // 即使跳转失败，也关闭菜单
    menuOpen.value = false
  }
}

// 跳转到通知页面
const goToNotificationsPage = () => {
  router.push({ name: 'UserNotifications' })
  menuOpen.value = false
}

// 跳转到通知偏好设置页面
const goToPreferencesPage = () => {
  router.push({ name: 'UserNotifyPreferences' })
  menuOpen.value = false
}

// BOT-EXT-2: 处理通知动作点击
const handleActionClick = async (action: NotificationAction) => {
  try {
    switch (action.type) {
      case 'open_web_url':
        if (action.url) {
          window.open(action.url, '_blank')
        }
        break
      
      case 'open_web_route':
        if (action.route_name) {
          router.push({
            name: action.route_name,
            params: action.route_params || {},
            query: action.route_query || {}
          })
          menuOpen.value = false
        }
        break
      
      case 'api_call':
      case 'mark_as_read':
        if (action.api_path) {
          const method = (action.api_method || 'POST').toUpperCase()
          const { default: axios } = await import('axios')
          
          if (method === 'POST') {
            await axios.post(action.api_path, action.api_body || {})
          } else if (method === 'PUT') {
            await axios.put(action.api_path, action.api_body || {})
          } else if (method === 'DELETE') {
            await axios.delete(action.api_path)
          }
          
          toast.success('操作成功')
          await loadNotifications()
        }
        break
      
      case 'open_manga':
        if (action.target_id) {
          router.push({ name: 'MangaReaderPage', params: { series_id: action.target_id } })
          menuOpen.value = false
        }
        break
      
      case 'open_novel':
        if (action.target_id) {
          router.push({ name: 'WorkDetail', params: { ebookId: action.target_id } })
          menuOpen.value = false
        }
        break
      
      case 'open_audiobook':
        if (action.target_id) {
          router.push({ name: 'AudiobookDetail', params: { id: action.target_id } })
          menuOpen.value = false
        }
        break
      
      case 'open_reading_center':
        router.push({ name: 'ReadingHub' })
        menuOpen.value = false
        break
      
      case 'open_music_center':
        router.push({ name: 'MusicCenter' })
        menuOpen.value = false
        break
      
      default:
        console.warn('未知动作类型:', action.type)
    }
  } catch (err: any) {
    console.error('执行动作失败:', err)
    toast.error(err.response?.data?.detail || err.message || '操作失败')
  }
}

// 来源相关辅助函数
const getSourceColor = (source: string): string => {
  const colors: Record<string, string> = {
    'SYSTEM': 'grey',
    'TTS': 'deep-purple',
    'AUDIOBOOK': 'blue',
    'MANGA': 'green',
    'NOVEL': 'orange',
    'OTHER': 'brown'
  }
  return colors[source] || 'grey'
}

const getSourceLabel = (source: string): string => {
  const labels: Record<string, string> = {
    'SYSTEM': '系统',
    'TTS': 'TTS',
    'AUDIOBOOK': '有声书',
    'MANGA': '漫画',
    'NOVEL': '小说',
    'OTHER': '其他'
  }
  return labels[source] || source
}

// 辅助函数
const getNotificationColor = (item: UserNotificationItem): string => {
  // TTS 通知特殊处理
  if (item.type === 'TTS_JOB_COMPLETED') return 'success'
  if (item.type === 'TTS_JOB_FAILED') return 'error'
  if (item.type === 'AUDIOBOOK_READY') return 'primary'
  
  // 漫画通知特殊处理
  if (item.type === 'MANGA_NEW_CHAPTER' || item.type === 'MANGA_UPDATED') return 'success'
  if (item.type === 'MANGA_SYNC_FAILED') return 'error'
  
  // 默认按严重程度
  const colors: Record<string, string> = {
    success: 'success',
    warning: 'warning',
    error: 'error',
    info: 'info'
  }
  return colors[item.severity || 'info'] || 'default'
}

const getNotificationIcon = (item: UserNotificationItem): string => {
  // TTS 通知特殊处理
  if (item.type === 'TTS_JOB_COMPLETED') return 'mdi-headphones'
  if (item.type === 'TTS_JOB_FAILED') return 'mdi-alert-circle'
  if (item.type === 'AUDIOBOOK_READY') return 'mdi-audiobook'
  
  // 漫画通知特殊处理
  if (item.type === 'MANGA_NEW_CHAPTER' || item.type === 'MANGA_UPDATED') return 'mdi-book-open-page-variant'
  if (item.type === 'MANGA_SYNC_FAILED') return 'mdi-alert-circle'
  
  // 默认按严重程度
  const icons: Record<string, string> = {
    success: 'mdi-check-circle',
    warning: 'mdi-alert',
    error: 'mdi-alert-circle',
    info: 'mdi-information'
  }
  return icons[item.severity || 'info'] || 'mdi-bell'
}

const getNotificationTag = (item: UserNotificationItem): string | null => {
  // TTS 通知特殊标签
  if (item.type === 'TTS_JOB_COMPLETED') return '有声书 · 完成'
  if (item.type === 'TTS_JOB_FAILED') return '有声书 · 失败'
  if (item.type === 'AUDIOBOOK_READY') return '有声书 · 就绪'
  
  // 漫画通知特殊标签
  if (item.type === 'MANGA_NEW_CHAPTER') return '漫画 · 新章节'
  if (item.type === 'MANGA_UPDATED') return '漫画 · 更新'
  if (item.type === 'MANGA_SYNC_FAILED') return '漫画 · 同步失败'
  
  // 其他媒体类型标签
  if (item.media_type === 'manga') return '漫画'
  if (item.media_type === 'novel') return '小说'
  if (item.media_type === 'audiobook') return '有声书'
  
  return null
}

const formatRelativeTime = (dateStr: string): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) return '刚刚'
  if (diffMins < 60) return `${diffMins} 分钟前`
  if (diffHours < 24) return `${diffHours} 小时前`
  if (diffDays === 1) return '昨天'
  if (diffDays < 7) return `${diffDays} 天前`
  
  // 超过7天，显示日期
  return date.toLocaleDateString('zh-CN')
}

// 完整时间格式化（用于tooltip）
const formatFullTime = (dateStr: string): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 初始化（使用 store）
onMounted(() => {
  // 初始化获取未读数量
  notificationStore.fetchUnreadCount()
  
  // 启动轮询
  notificationStore.startPolling(30000)
})

onUnmounted(() => {
  // 停止轮询
  notificationStore.stopPolling()
})
</script>

<style scoped>
.notification-bell {
  position: relative;
}

.notification-item-unread {
  background-color: rgba(var(--v-theme-primary), 0.04) !important;
  border-left: 3px solid rgb(var(--v-theme-primary));
}

.notification-item-error {
  border-left: 3px solid rgb(var(--v-theme-error));
}

.unread-indicator {
  display: flex;
  align-items: center;
  margin-right: 4px;
}

.v-list-item:hover {
  background-color: rgba(var(--v-theme-primary), 0.08) !important;
  transition: background-color 0.2s ease;
}

.v-list-item:active {
  background-color: rgba(var(--v-theme-primary), 0.12) !important;
}

/* 响应式调整 */
@media (max-width: 600px) {
  .v-list-item-title {
    font-size: 0.875rem !important;
  }
  
  .v-list-item-subtitle {
    font-size: 0.75rem !important;
  }
}
</style>

