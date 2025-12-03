<template>
  <div class="user-notifications-page">
    <v-container fluid>
      <v-row>
        <v-col cols="12">
          <h1 class="text-h4 mb-6">用户通知</h1>
          
          <!-- 通知统计 -->
          <v-row class="mb-4">
            <v-col cols="12" md="3">
              <v-card>
                <v-card-text>
                  <div class="text-h6">{{ totalCount }}</div>
                  <div class="text-caption">全部通知</div>
                </v-card-text>
              </v-card>
            </v-col>
            <v-col cols="12" md="3">
              <v-card>
                <v-card-text>
                  <div class="text-h6">{{ unreadCount }}</div>
                  <div class="text-caption">未读通知</div>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          <!-- 通知列表 -->
          <v-card>
            <v-card-title>
              通知列表
              <v-spacer />
              <v-btn 
                color="primary"
                :disabled="unreadCount === 0"
                @click="handleMarkAllRead"
              >
                标记全部已读
              </v-btn>
            </v-card-title>
            
            <v-card-text>
              <div v-if="loading" class="text-center py-8">
                <v-progress-circular indeterminate />
                <div class="mt-2">加载中...</div>
              </div>
              
              <div v-else-if="notifications.length === 0" class="text-center py-8">
                <v-icon size="64" color="grey-lighten-1">mdi-bell-outline</v-icon>
                <div class="text-h6 mt-2">暂无通知</div>
              </div>
              
              <v-list v-else>
                <v-list-item
                  v-for="notification in notifications"
                  :key="notification.id"
                  :class="{ 'notification-unread': !notification.is_read }"
                  @click="handleNotificationClick(notification)"
                >
                  <template #prepend>
                    <v-icon :color="getNotificationColor(notification)">
                      {{ getNotificationIcon(notification) }}
                    </v-icon>
                  </template>
                  
                  <v-list-item-title :class="{ 'font-weight-bold': !notification.is_read }">
                    {{ notification.title }}
                  </v-list-item-title>
                  
                  <v-list-item-subtitle>
                    {{ notification.message }}
                  </v-list-item-subtitle>
                  
                  <template #append>
                    <v-btn
                      v-if="!notification.is_read"
                      icon="mdi-check"
                      size="small"
                      variant="text"
                      @click.stop="handleMarkRead(notification)"
                    />
                  </template>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

// Types
interface Notification {
  id: number
  title: string
  message: string
  is_read: boolean
  created_at: string
  type: string
}

// Router
const router = useRouter()

// Data
const notifications = ref<Notification[]>([])
const loading = ref(false)

// Computed
const totalCount = computed(() => notifications.value.length)
const unreadCount = computed(() => notifications.value.filter(n => !n.is_read).length)

// Methods
const loadNotifications = async () => {
  loading.value = true
  try {
    // Mock data - replace with actual API call
    notifications.value = [
      {
        id: 1,
        title: '测试通知',
        message: '这是一个测试通知',
        is_read: false,
        created_at: new Date().toISOString(),
        type: 'info'
      }
    ]
  } catch (error) {
    console.error('加载通知失败:', error)
  } finally {
    loading.value = false
  }
}

const handleMarkAllRead = async () => {
  try {
    // Mock API call
    notifications.value.forEach(n => n.is_read = true)
  } catch (error) {
    console.error('标记全部已读失败:', error)
  }
}

const handleMarkRead = async (notification: Notification) => {
  try {
    // Mock API call
    notification.is_read = true
  } catch (error) {
    console.error('标记已读失败:', error)
  }
}

const handleNotificationClick = (notification: Notification) => {
  // Handle notification click
  console.log('点击通知:', notification)
}

const getNotificationColor = (notification: Notification) => {
  switch (notification.type) {
    case 'success': return 'success'
    case 'warning': return 'warning'
    case 'error': return 'error'
    default: return 'info'
  }
}

const getNotificationIcon = (notification: Notification) => {
  switch (notification.type) {
    case 'success': return 'mdi-check-circle'
    case 'warning': return 'mdi-alert'
    case 'error': return 'mdi-alert-circle'
    default: return 'mdi-information'
  }
}

// Lifecycle
onMounted(() => {
  loadNotifications()
})
</script>

<style scoped>
.user-notifications-page {
  min-height: 100vh;
}

.notification-unread {
  background-color: rgba(var(--v-theme-primary), 0.08);
  font-weight: 500;
}
</style>