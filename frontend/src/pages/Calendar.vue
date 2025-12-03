<template>
  <div class="calendar-page">
    <PageHeader
      title="日历"
      subtitle="订阅发布时间管理"
    >
      <template #actions>
        <v-btn
          color="primary"
          prepend-icon="mdi-filter"
          @click="showFilterDialog = true"
        >
          筛选
        </v-btn>
        <v-btn
          icon="mdi-refresh"
          variant="text"
          @click="loadEvents"
          :loading="loading"
        />
      </template>
    </PageHeader>

    <v-container fluid class="pa-4">
      <!-- 日历视图选择 -->
      <v-card variant="outlined" class="mb-4">
        <v-card-text class="pa-3">
          <div class="d-flex align-center justify-space-between flex-wrap ga-2">
            <div class="d-flex align-center ga-2">
              <v-btn-toggle
                v-model="viewType"
                mandatory
                density="compact"
              >
                <v-btn value="month" prepend-icon="mdi-calendar-month">月视图</v-btn>
                <v-btn value="week" prepend-icon="mdi-calendar-week">周视图</v-btn>
                <v-btn value="list" prepend-icon="mdi-view-list">列表视图</v-btn>
              </v-btn-toggle>
            </div>
            <div class="d-flex align-center ga-2">
              <v-btn
                icon="mdi-chevron-left"
                variant="text"
                @click="previousPeriod"
              />
              <v-btn
                variant="text"
                @click="goToToday"
              >
                今天
              </v-btn>
              <v-btn
                icon="mdi-chevron-right"
                variant="text"
                @click="nextPeriod"
              />
            </div>
          </div>
        </v-card-text>
      </v-card>

      <!-- 月视图 -->
      <v-calendar
        v-if="viewType === 'month'"
        v-model="selectedDate"
        :events="calendarEvents"
        :event-color="getEventColor"
        :event-text-color="'white'"
        type="month"
        locale="zh-CN"
        :first-interval="0"
        :interval-count="24"
        @click:event="viewEvent"
        @click:date="viewDate"
      >
        <template #event="{ event }">
          <div class="event-item">
            <v-chip
              :color="event.color"
              size="x-small"
              variant="flat"
              class="event-chip"
            >
              {{ event.title }}
            </v-chip>
          </div>
        </template>
      </v-calendar>

      <!-- 周视图 -->
      <v-calendar
        v-else-if="viewType === 'week'"
        v-model="selectedDate"
        :events="calendarEvents"
        :event-color="getEventColor"
        :event-text-color="'white'"
        type="week"
        locale="zh-CN"
        :first-interval="0"
        :interval-count="24"
        @click:event="viewEvent"
        @click:date="viewDate"
      />

      <!-- 列表视图 -->
      <v-card v-else-if="viewType === 'list'">
        <v-card-title>事件列表</v-card-title>
        <v-card-text>
          <v-list density="comfortable">
            <v-list-item
              v-for="event in sortedEvents"
              :key="event.id"
              class="event-list-item"
            >
              <template #prepend>
                <v-avatar
                  :color="event.color || '#1976d2'"
                  size="40"
                >
                  <v-icon color="white">{{ getEventIcon(event.type) }}</v-icon>
                </v-avatar>
              </template>

              <v-list-item-title class="font-weight-bold">
                {{ event.title }}
              </v-list-item-title>
              <v-list-item-subtitle>
                <div class="d-flex align-center flex-wrap ga-2 mt-2">
                  <v-chip
                    :color="event.color || '#1976d2'"
                    size="x-small"
                    variant="flat"
                  >
                    {{ getEventTypeLabel(event.type) }}
                  </v-chip>
                  <span class="text-caption text-medium-emphasis">
                    {{ formatDateTime(event.date) }}
                  </span>
                  <span v-if="event.season" class="text-caption text-medium-emphasis">
                    第 {{ event.season }} 季
                  </span>
                </div>
                <div v-if="event.description" class="text-caption text-medium-emphasis mt-1">
                  {{ event.description }}
                </div>
              </v-list-item-subtitle>

              <template #append>
                <v-btn
                  icon="mdi-eye"
                  size="small"
                  variant="text"
                  @click="viewEvent(event)"
                />
              </template>
            </v-list-item>
          </v-list>
        </v-card-text>
      </v-card>

      <!-- 事件详情对话框 -->
      <v-dialog
        v-model="showEventDialog"
        max-width="600"
      >
        <v-card v-if="selectedEvent">
          <v-card-item class="py-3">
            <template #prepend>
              <v-avatar
                :color="selectedEvent.color || '#1976d2'"
                size="48"
              >
                <v-icon color="white">{{ getEventIcon(selectedEvent.type) }}</v-icon>
              </v-avatar>
            </template>
            <v-card-title>{{ selectedEvent.title }}</v-card-title>
            <v-card-subtitle>
              {{ formatDateTime(selectedEvent.date) }}
            </v-card-subtitle>
          </v-card-item>
          <v-card-text>
            <v-list density="compact">
              <v-list-item>
                <v-list-item-title>类型</v-list-item-title>
                <v-list-item-subtitle>{{ getEventTypeLabel(selectedEvent.type) }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="selectedEvent.description">
                <v-list-item-title>描述</v-list-item-title>
                <v-list-item-subtitle>{{ selectedEvent.description }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="selectedEvent.subscription_id">
                <v-list-item-title>订阅ID</v-list-item-title>
                <v-list-item-subtitle>{{ selectedEvent.subscription_id }}</v-list-item-subtitle>
              </v-list-item>
              <v-list-item v-if="selectedEvent.download_id">
                <v-list-item-title>下载ID</v-list-item-title>
                <v-list-item-subtitle>{{ selectedEvent.download_id }}</v-list-item-subtitle>
              </v-list-item>
            </v-list>
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn
              v-if="selectedEvent.subscription_id"
              color="primary"
              prepend-icon="mdi-open-in-new"
              @click="viewSubscription(selectedEvent.subscription_id)"
            >
              查看订阅
            </v-btn>
            <v-btn
              variant="text"
              @click="showEventDialog = false"
            >
              关闭
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>

      <!-- 筛选对话框 -->
      <v-dialog
        v-model="showFilterDialog"
        max-width="400"
      >
        <v-card>
          <v-card-title>筛选事件</v-card-title>
          <v-card-text>
            <v-checkbox
              v-model="eventTypeFilters"
              value="subscription"
              label="订阅事件"
              hide-details
            />
            <v-checkbox
              v-model="eventTypeFilters"
              value="download"
              label="下载事件"
              hide-details
            />
            <v-checkbox
              v-model="eventTypeFilters"
              value="media_update"
              label="媒体更新"
              hide-details
            />
          </v-card-text>
          <v-card-actions>
            <v-spacer />
            <v-btn
              variant="text"
              @click="showFilterDialog = false"
            >
              取消
            </v-btn>
            <v-btn
              color="primary"
              @click="applyFilters"
            >
              应用
            </v-btn>
          </v-card-actions>
        </v-card>
      </v-dialog>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'

const router = useRouter()

const loading = ref(false)
const viewType = ref('month')
const selectedDate = ref(new Date())
const calendarEvents = ref<any[]>([])
const showEventDialog = ref(false)
const showFilterDialog = ref(false)
const selectedEvent = ref<any>(null)
const eventTypeFilters = ref(['subscription', 'download', 'media_update'])

const sortedEvents = computed(() => {
  return [...calendarEvents.value].sort((a, b) => {
    return new Date(a.date).getTime() - new Date(b.date).getTime()
  })
})

const loadEvents = async () => {
  loading.value = true
  try {
    // 计算开始和结束日期
    const start = new Date(selectedDate.value)
    start.setMonth(start.getMonth() - 1)
    start.setDate(1)
    start.setHours(0, 0, 0, 0)

    const end = new Date(selectedDate.value)
    end.setMonth(end.getMonth() + 2)
    end.setDate(0)
    end.setHours(23, 59, 59, 999)

    const response = await api.get('/calendar', {
      params: {
        start_date: start.toISOString(),
        end_date: end.toISOString(),
        event_types: eventTypeFilters.value
      }
    })

    // 转换为v-calendar需要的格式
    calendarEvents.value = response.data.map((event: any) => ({
      ...event,
      start: new Date(event.date),
      end: new Date(event.date),
      name: event.title
    }))
  } catch (error: any) {
    console.error('加载日历事件失败:', error)
    alert('加载失败：' + (error.response?.data?.detail || '未知错误'))
  } finally {
    loading.value = false
  }
}

const getEventColor = (event: any) => {
  return event.color || '#1976d2'
}

const getEventIcon = (type: string) => {
  const icons: Record<string, string> = {
    subscription: 'mdi-bookmark',
    download: 'mdi-download',
    media_update: 'mdi-update'
  }
  return icons[type] || 'mdi-calendar'
}

const getEventTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    subscription: '订阅',
    download: '下载',
    media_update: '媒体更新'
  }
  return labels[type] || type
}

const viewEvent = (event: any) => {
  selectedEvent.value = event
  showEventDialog.value = true
}

const viewDate = (date: any) => {
  // 可以显示该日期的所有事件
  const dateEvents = calendarEvents.value.filter((e: any) => {
    const eventDate = new Date(e.date)
    return eventDate.toDateString() === date.date.toDateString()
  })
  console.log('日期事件:', dateEvents)
}

const viewSubscription = (subscriptionId: number) => {
  router.push({ name: 'Subscriptions', query: { id: subscriptionId } })
}

const previousPeriod = () => {
  if (viewType.value === 'month') {
    const date = new Date(selectedDate.value)
    date.setMonth(date.getMonth() - 1)
    selectedDate.value = date
  } else if (viewType.value === 'week') {
    const date = new Date(selectedDate.value)
    date.setDate(date.getDate() - 7)
    selectedDate.value = date
  }
  loadEvents()
}

const nextPeriod = () => {
  if (viewType.value === 'month') {
    const date = new Date(selectedDate.value)
    date.setMonth(date.getMonth() + 1)
    selectedDate.value = date
  } else if (viewType.value === 'week') {
    const date = new Date(selectedDate.value)
    date.setDate(date.getDate() + 7)
    selectedDate.value = date
  }
  loadEvents()
}

const goToToday = () => {
  selectedDate.value = new Date()
  loadEvents()
}

const applyFilters = () => {
  showFilterDialog.value = false
  loadEvents()
}

const formatDateTime = (dateStr: string) => {
  if (!dateStr) return ''
  try {
    const date = new Date(dateStr)
    return date.toLocaleString('zh-CN')
  } catch {
    return dateStr
  }
}

onMounted(() => {
  loadEvents()
})
</script>

<style scoped>
.calendar-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
}

.event-item {
  padding: 2px;
}

.event-chip {
  width: 100%;
  justify-content: flex-start;
}

.event-list-item {
  border-bottom: 1px solid rgba(var(--v-border-color), 0.12);
}
</style>
