<template>
  <div class="notifications-page">
    <PageHeader
      title="通知中心"
      subtitle="查看和管理系统通知"
    >
      <template #actions>
        <v-btn
          color="primary"
          prepend-icon="mdi-bell-plus"
          @click="showSendDialog = true"
        >
          发送通知
        </v-btn>
        <v-btn
          color="error"
          prepend-icon="mdi-delete-sweep"
          @click="handleDeleteAll"
          :disabled="notifications.length === 0"
        >
          清空所有
        </v-btn>
      </template>
    </PageHeader>

    <v-container fluid class="pa-4">
      <!-- 筛选栏 -->
      <v-card variant="outlined" class="mb-4">
        <v-card-text class="pa-3">
          <v-row dense align="center">
            <v-col cols="12" md="3">
              <v-select
                v-model="filters.type"
                :items="notificationTypes"
                label="类型"
                variant="outlined"
                density="compact"
                clearable
                @update:model-value="loadNotifications"
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-select
                v-model="filters.status"
                :items="statusTypes"
                label="状态"
                variant="outlined"
                density="compact"
                clearable
                @update:model-value="loadNotifications"
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-switch
                v-model="filters.unreadOnly"
                label="仅未读"
                hide-details
                density="compact"
                @update:model-value="loadNotifications"
              />
            </v-col>
            <v-col cols="12" md="3" class="text-right">
              <v-btn
                icon="mdi-refresh"
                variant="text"
                @click="loadNotifications"
                :loading="loading"
              />
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- 通知列表 -->
      <div v-if="loading" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" />
        <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
      </div>

      <div v-else-if="notifications.length === 0" class="text-center py-12">
        <v-icon size="80" color="grey-darken-1" class="mb-4">mdi-bell-off</v-icon>
        <div class="text-h5 font-weight-medium mb-2">暂无通知</div>
        <div class="text-body-2 text-medium-emphasis">
          系统通知将显示在这里
        </div>
      </div>

      <v-list v-else density="comfortable">
        <v-list-item
          v-for="notification in notifications"
          :key="notification.id"
          class="notification-item"
          :class="`notification-${notification.type}`"
        >
          <template #prepend>
            <v-avatar
              :color="getTypeColor(notification.type)"
              size="48"
            >
              <v-icon color="white">{{ getTypeIcon(notification.type) }}</v-icon>
            </v-avatar>
          </template>

          <v-list-item-title class="font-weight-bold">
            {{ notification.title }}
          </v-list-item-title>
          <v-list-item-subtitle>
            <div class="mt-2">{{ notification.message }}</div>
            <div class="d-flex align-center flex-wrap ga-2 mt-2">
              <v-chip
                v-for="channel in notification.channels"
                :key="channel"
                size="x-small"
                variant="flat"
                color="primary"
              >
                {{ getChannelLabel(channel) }}
              </v-chip>
              <v-chip
                :color="getStatusColor(notification.status)"
                size="x-small"
                variant="flat"
              >
                {{ getStatusLabel(notification.status) }}
              </v-chip>
              <span class="text-caption text-medium-emphasis">
                {{ formatDate(notification.created_at) }}
              </span>
            </div>
          </v-list-item-subtitle>

          <template #append>
            <div class="d-flex align-center ga-1">
              <v-btn
                icon="mdi-eye"
                size="small"
                variant="text"
                @click="viewNotification(notification)"
              />
              <v-btn
                icon="mdi-delete"
                size="small"
                variant="text"
                color="error"
                @click="deleteNotification(notification)"
              />
            </div>
          </template>
        </v-list-item>
      </v-list>
    </v-container>

    <!-- 发送通知对话框 -->
    <SendNotificationDialog
      v-model="showSendDialog"
      @sent="handleNotificationSent"
    />

    <!-- 通知详情对话框 -->
    <v-dialog
      v-model="showDetailDialog"
      max-width="600"
    >
      <v-card v-if="selectedNotification">
        <v-card-item class="py-3">
          <v-card-title>{{ selectedNotification.title }}</v-card-title>
          <v-card-subtitle>
            {{ formatDate(selectedNotification.created_at) }}
          </v-card-subtitle>
        </v-card-item>
        <v-card-text>
          <div class="text-body-1 mb-4">{{ selectedNotification.message }}</div>
          <v-divider class="my-4" />
          <div class="text-caption text-medium-emphasis">
            <div>类型: {{ getTypeLabel(selectedNotification.type) }}</div>
            <div>状态: {{ getStatusLabel(selectedNotification.status) }}</div>
            <div>渠道: {{ selectedNotification.channels.join(', ') }}</div>
            <div v-if="selectedNotification.sent_at">
              发送时间: {{ formatDate(selectedNotification.sent_at) }}
            </div>
          </div>
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn
            variant="text"
            @click="showDetailDialog = false"
          >
            关闭
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import SendNotificationDialog from '@/components/notification/SendNotificationDialog.vue'

const loading = ref(false)
const notifications = ref<any[]>([])
const showSendDialog = ref(false)
const showDetailDialog = ref(false)
const selectedNotification = ref<any>(null)

const filters = ref({
  type: null as string | null,
  status: null as string | null,
  unreadOnly: false
})

const notificationTypes = [
  { title: '信息', value: 'info' },
  { title: '成功', value: 'success' },
  { title: '警告', value: 'warning' },
  { title: '错误', value: 'error' }
]

const statusTypes = [
  { title: '待发送', value: 'pending' },
  { title: '已发送', value: 'sent' },
  { title: '部分成功', value: 'partial' },
  { title: '失败', value: 'failed' }
]

const loadNotifications = async () => {
  loading.value = true
  try {
    const params: any = {
      limit: 100
    }
    if (filters.value.type) {
      params.notification_type = filters.value.type
    }
    if (filters.value.status) {
      params.status = filters.value.status
    }
    if (filters.value.unreadOnly) {
      params.unread_only = true
    }

    const response = await api.get('/notifications', { params })
    notifications.value = response.data
  } catch (error: any) {
    console.error('加载通知列表失败:', error)
    alert('加载失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    loading.value = false
  }
}

const viewNotification = (notification: any) => {
  selectedNotification.value = notification
  showDetailDialog.value = true
}

const deleteNotification = async (notification: any) => {
  if (!confirm(`确定要删除通知"${notification.title}"吗？`)) {
    return
  }

  try {
    await api.delete(`/notifications/${notification.id}`)
    await loadNotifications()
  } catch (error: any) {
    console.error('删除通知失败:', error)
    alert('删除失败：' + (error.response?.data?.detail || '未知错误'))
  }
}

const handleDeleteAll = async () => {
  if (!confirm('确定要清空所有通知吗？')) {
    return
  }

  try {
    await api.delete('/notifications')
    await loadNotifications()
  } catch (error: any) {
    console.error('清空通知失败:', error)
    alert('清空失败：' + (error.response?.data?.detail || '未知错误'))
  }
}

const handleNotificationSent = () => {
  loadNotifications()
}

const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    info: 'info',
    success: 'success',
    warning: 'warning',
    error: 'error'
  }
  return colors[type] || 'grey'
}

const getTypeIcon = (type: string) => {
  const icons: Record<string, string> = {
    info: 'mdi-information',
    success: 'mdi-check-circle',
    warning: 'mdi-alert',
    error: 'mdi-alert-circle'
  }
  return icons[type] || 'mdi-bell'
}

const getTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    info: '信息',
    success: '成功',
    warning: '警告',
    error: '错误'
  }
  return labels[type] || type
}

const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'grey',
    sent: 'success',
    partial: 'warning',
    failed: 'error'
  }
  return colors[status] || 'grey'
}

const getStatusLabel = (status: string) => {
  const labels: Record<string, string> = {
    pending: '待发送',
    sent: '已发送',
    partial: '部分成功',
    failed: '失败'
  }
  return labels[status] || status
}

const getChannelLabel = (channel: string) => {
  const labels: Record<string, string> = {
    system: '系统',
    email: '邮件',
    telegram: 'Telegram',
    wechat: '微信',
    webhook: 'Webhook',
    push: '推送'
  }
  return labels[channel] || channel
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

onMounted(() => {
  loadNotifications()
})
</script>

<style scoped>
.notifications-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
}

.notification-item {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
  margin-bottom: 8px;
}

.notification-info {
  background: rgba(var(--v-theme-info), 0.1);
}

.notification-success {
  background: rgba(var(--v-theme-success), 0.1);
}

.notification-warning {
  background: rgba(var(--v-theme-warning), 0.1);
}

.notification-error {
  background: rgba(var(--v-theme-error), 0.1);
}
</style>

