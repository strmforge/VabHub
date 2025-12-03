<template>
  <v-card
    class="download-notification-card"
    :class="{
      'is-read': notification.is_read,
      'is-selected': selectable && selected,
      [`notification-${notificationType}`]: true
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

        <!-- 图标区域 -->
        <div class="icon-container mr-3">
          <v-avatar
            size="64"
            rounded="lg"
            :color="notificationTypeColor"
            class="icon-avatar"
          >
            <v-icon size="32" color="white">
              {{ notificationTypeIcon }}
            </v-icon>
          </v-avatar>
        </div>

        <!-- 内容区域 -->
        <div class="flex-grow-1">
          <!-- 标题和状态标签 -->
          <div class="d-flex align-center mb-1">
            <h4 class="text-subtitle-1 font-weight-medium mb-0">
              {{ notification.title }}
            </h4>
            <v-chip
              v-if="statusLabel"
              size="x-small"
              :color="notificationTypeColor"
              variant="tonal"
              class="ml-2"
            >
              {{ statusLabel }}
            </v-chip>
          </div>

          <!-- 消息内容 -->
          <p class="text-body-2 text-medium-emphasis mb-2">
            {{ notification.message }}
          </p>

          <!-- 下载通知特有信息 -->
          <div v-if="hasDownloadDetails" class="download-details mb-2">
            <!-- 订阅命中信息 -->
            <div v-if="isSubscriptionMatched" class="d-flex align-center mb-1">
              <v-icon size="16" class="mr-1">mdi-bookmark-check</v-icon>
              <span class="text-caption">订阅: {{ subscriptionName }}</span>
            </div>
            
            <!-- 下载完成信息 -->
            <div v-if="isTaskCompleted" class="d-flex flex-column gap-1">
              <div v-if="fileSize" class="d-flex align-center">
                <v-icon size="16" class="mr-1">mdi-harddisk</v-icon>
                <span class="text-caption">大小: {{ fileSize }}</span>
              </div>
              <div v-if="downloadDuration" class="d-flex align-center">
                <v-icon size="16" class="mr-1">mdi-clock-outline</v-icon>
                <span class="text-caption">耗时: {{ downloadDuration }}</span>
              </div>
              <div v-if="categoryLabel" class="d-flex align-center">
                <v-icon size="16" class="mr-1">mdi-folder</v-icon>
                <span class="text-caption">类型: {{ categoryLabel }}</span>
              </div>
            </div>
            
            <!-- HR 风险信息 -->
            <div v-if="isHrRisk" class="d-flex flex-column gap-1">
              <div class="d-flex align-center">
                <v-icon size="16" class="mr-1" :color="riskLevelColor">mdi-alert</v-icon>
                <span class="text-caption" :style="{ color: riskLevelColor }">
                  风险等级: {{ riskLevel }}
                </span>
              </div>
              <div v-if="reason" class="d-flex align-center">
                <v-icon size="16" class="mr-1">mdi-information</v-icon>
                <span class="text-caption">{{ reason }}</span>
              </div>
              <div v-if="minSeedTime" class="d-flex align-center">
                <v-icon size="16" class="mr-1">mdi-timer</v-icon>
                <span class="text-caption">保种要求: {{ minSeedTime }}</span>
              </div>
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
                :color="notificationTypeColor"
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

// 通知类型相关计算属性
const notificationType = computed(() => {
  return props.notification.type || 'unknown'
})

const notificationTypeColor = computed(() => {
  switch (notificationType.value) {
    case 'DOWNLOAD_SUBSCRIPTION_MATCHED': return 'blue'
    case 'DOWNLOAD_TASK_COMPLETED': return 'green'
    case 'DOWNLOAD_HR_RISK': return 'orange'
    default: return 'grey'
  }
})

const notificationTypeIcon = computed(() => {
  switch (notificationType.value) {
    case 'DOWNLOAD_SUBSCRIPTION_MATCHED': return 'mdi-bookmark-check'
    case 'DOWNLOAD_TASK_COMPLETED': return 'mdi-download-check'
    case 'DOWNLOAD_HR_RISK': return 'mdi-alert-triangle'
    default: return 'mdi-download'
  }
})

// 状态标签
const statusLabel = computed(() => {
  switch (notificationType.value) {
    case 'DOWNLOAD_SUBSCRIPTION_MATCHED': return '订阅命中'
    case 'DOWNLOAD_TASK_COMPLETED': return '下载完成'
    case 'DOWNLOAD_HR_RISK': return 'HR 风险'
    default: return undefined
  }
})

// 下载通知特有信息
const hasDownloadDetails = computed(() => {
  return isSubscriptionMatched.value || isTaskCompleted.value || isHrRisk.value
})

const isSubscriptionMatched = computed(() => {
  return notificationType.value === 'DOWNLOAD_SUBSCRIPTION_MATCHED'
})

const isTaskCompleted = computed(() => {
  return notificationType.value === 'DOWNLOAD_TASK_COMPLETED'
})

const isHrRisk = computed(() => {
  return notificationType.value === 'DOWNLOAD_HR_RISK'
})

// 订阅命中信息
const subscriptionName = computed(() => {
  return props.notification.payload?.subscription_name || '未知订阅'
})

// 下载完成信息
const fileSize = computed(() => {
  const size = props.notification.payload?.file_size_gb
  return size ? `${size.toFixed(2)} GB` : undefined
})

const downloadDuration = computed(() => {
  const duration = props.notification.payload?.download_duration_minutes
  return duration ? `${duration} 分钟` : undefined
})

const categoryLabel = computed(() => {
  return props.notification.payload?.category_label
})

// HR 风险信息
const riskLevel = computed(() => {
  return props.notification.payload?.risk_level || 'WARN'
})

const riskLevelColor = computed(() => {
  switch (riskLevel.value) {
    case 'H&R': return '#f44336' // red
    case 'HR': return '#ff9800'  // orange
    case 'H3': return '#ffc107'  // amber
    case 'H5': return '#ffc107'  // amber
    default: return '#ff9800'    // orange
  }
})

const reason = computed(() => {
  return props.notification.payload?.reason
})

const minSeedTime = computed(() => {
  const hours = props.notification.payload?.min_seed_time_hours
  return hours ? `${hours} 小时` : undefined
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
.download-notification-card {
  cursor: pointer;
  transition: all 0.2s ease;
  border-left: 4px solid transparent;
}

.download-notification-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.download-notification-card.is-read {
  opacity: 0.7;
  background-color: rgba(0, 0, 0, 0.02);
}

.download-notification-card.notification-DOWNLOAD_SUBSCRIPTION_MATCHED {
  border-left-color: #2196f3;
}

.download-notification-card.notification-DOWNLOAD_TASK_COMPLETED {
  border-left-color: #4caf50;
}

.download-notification-card.notification-DOWNLOAD_HR_RISK {
  border-left-color: #ff9800;
}

.icon-container {
  flex-shrink: 0;
}

.icon-avatar {
  border: 2px solid rgba(0, 0, 0, 0.1);
}

.download-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.download-details .v-icon {
  opacity: 0.7;
}

.gap-1 {
  gap: 4px;
}
</style>
