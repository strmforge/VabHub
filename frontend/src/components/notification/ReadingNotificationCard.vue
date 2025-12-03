<template>
  <v-card
    class="reading-notification-card"
    :class="{
      'is-read': notification.is_read,
      'is-selected': selectable && selected,
      [`media-${mediaType}`]: true
    }"
    variant="outlined"
    @click="handleCardClick"
  >
    <v-card-text class="pa-4">
      <div class="d-flex align-start">
        <!-- 选择框（仅在可选择时显示） -->
        <div v-if="selectable" class="selection-container mr-3">
          <v-checkbox
            :model-value="selected"
            @update:model-value="handleToggleSelect"
            @click.stop
            density="compact"
            hide-details
            class="selection-checkbox"
          />
        </div>

        <!-- 封面图片 -->
        <div class="cover-container mr-3">
          <v-avatar
            size="64"
            rounded="lg"
            :image="coverUrl"
            class="cover-avatar"
          >
            <v-icon v-if="!coverUrl" size="32" :color="mediaTypeColor">
              {{ mediaTypeIcon }}
            </v-icon>
          </v-avatar>
        </div>

        <!-- 内容区域 -->
        <div class="flex-grow-1">
          <!-- 标题和来源标签 -->
          <div class="d-flex align-center mb-1">
            <h4 class="text-subtitle-1 font-weight-medium mb-0">
              {{ notification.title }}
            </h4>
            <v-chip
              v-if="sourceLabel"
              size="x-small"
              :color="mediaTypeColor"
              variant="tonal"
              class="ml-2"
            >
              {{ sourceLabel }}
            </v-chip>
          </div>

          <!-- 消息内容 -->
          <p class="text-body-2 text-medium-emphasis mb-2">
            {{ notification.message }}
          </p>

          <!-- 阅读通知特有信息 -->
          <div v-if="hasReadingDetails" class="reading-details mb-2">
            <div v-if="isMangaUpdate" class="d-flex align-center">
              <v-icon size="16" class="mr-1">mdi-book-open-variant</v-icon>
              <span class="text-caption">新增 {{ totalNewCount }} 话</span>
            </div>
            <div v-if="isAudiobookReady && totalChapters" class="d-flex align-center">
              <v-icon size="16" class="mr-1">mdi-headphones</v-icon>
              <span class="text-caption">{{ totalChapters }} 章节</span>
            </div>
          </div>

          <!-- 时间和操作 -->
          <div class="d-flex align-center justify-space-between">
            <span class="text-caption text-medium-emphasis">
              {{ formatTime(notification.created_at) }}
            </span>
            <div class="d-flex align-center">
              <v-btn
                v-if="hasRoute"
                size="small"
                variant="text"
                :color="mediaTypeColor"
                @click.stop="handleNavigate"
              >
                <v-icon size="16" class="mr-1">mdi-open-in-new</v-icon>
                查看
              </v-btn>
              <v-btn
                v-if="!notification.is_read"
                size="small"
                variant="text"
                icon="mdi-check"
                @click.stop="handleMarkRead"
              />
            </div>
          </div>
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import type { UserNotificationItem } from '@/types/notify'
import { notificationApi } from '@/services/api'

interface Props {
  notification: UserNotificationItem
  selectable?: boolean
  selected?: boolean
}

interface Emits {
  (e: 'mark-read', id: number): void
  (e: 'navigate', notification: UserNotificationItem): void
  (e: 'toggle-select', id: number): void
}

const props = withDefaults(defineProps<Props>(), {
  selectable: false,
  selected: false
})

const emit = defineEmits<Emits>()
const router = useRouter()

// 媒体类型相关计算属性
const mediaType = computed(() => props.notification.media_type || 'other')
const mediaTypeColor = computed(() => {
  switch (mediaType.value) {
    case 'manga': return 'purple'
    case 'novel': return 'blue'
    case 'audiobook': return 'green'
    default: return 'grey'
  }
})

const mediaTypeIcon = computed(() => {
  switch (mediaType.value) {
    case 'manga': return 'mdi-book-open-variant'
    case 'novel': return 'mdi-book'
    case 'audiobook': return 'mdi-headphones'
    default: return 'mdi-bell'
  }
})

// 封面图片
const coverUrl = computed(() => {
  return props.notification.payload?.cover_url || undefined
})

// 来源标签
const sourceLabel = computed(() => {
  return props.notification.payload?.source_label || undefined
})

// 阅读通知特有信息
const hasReadingDetails = computed(() => {
  return isMangaUpdate.value || isAudiobookReady.value
})

const isMangaUpdate = computed(() => {
  return props.notification.type === 'MANGA_UPDATED'
})

const isAudiobookReady = computed(() => {
  return props.notification.type === 'AUDIOBOOK_READY'
})

const totalNewCount = computed(() => {
  return props.notification.payload?.total_new_count || 0
})

const totalChapters = computed(() => {
  return props.notification.payload?.total_chapters || 0
})

// 路由相关
const hasRoute = computed(() => {
  return !!(props.notification.payload?.route_name)
})

const routeName = computed(() => {
  return props.notification.payload?.route_name
})

const routeParams = computed(() => {
  return props.notification.payload?.route_params || {}
})

// 事件处理
const handleCardClick = () => {
  if (hasRoute.value) {
    handleNavigate()
  }
}

const handleToggleSelect = () => {
  emit('toggle-select', props.notification.id)
}

const handleNavigate = async () => {
  if (!routeName.value) return
  
  try {
    // 标记为已读
    if (!props.notification.is_read) {
      await handleMarkRead()
    }
    
    // 导航到目标页面
    await router.push({
      name: routeName.value,
      params: routeParams.value
    })
    
    emit('navigate', props.notification)
  } catch (error) {
    console.error('导航失败:', error)
  }
}

const handleMarkRead = async () => {
  try {
    await notificationApi.markRead(props.notification.id)
    emit('mark-read', props.notification.id)
  } catch (error) {
    console.error('标记已读失败:', error)
  }
}

// 工具函数
const formatTime = (timeStr: string) => {
  const date = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  
  const minutes = Math.floor(diff / (1000 * 60))
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (minutes < 1) return '刚刚'
  if (minutes < 60) return `${minutes}分钟前`
  if (hours < 24) return `${hours}小时前`
  if (days < 7) return `${days}天前`
  
  return date.toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.reading-notification-card {
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 4px solid transparent;
}

.reading-notification-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.reading-notification-card.is-read {
  opacity: 0.7;
  background-color: rgba(0, 0, 0, 0.02);
}

.reading-notification-card.media-manga {
  border-left-color: #9c27b0;
}

.reading-notification-card.media-novel {
  border-left-color: #2196f3;
}

.reading-notification-card.media-audiobook {
  border-left-color: #4caf50;
}

.cover-container {
  flex-shrink: 0;
}

.cover-avatar {
  border: 2px solid rgba(0, 0, 0, 0.1);
}

.reading-details {
  display: flex;
  gap: 16px;
}

.reading-details .v-icon {
  opacity: 0.7;
}
</style>
