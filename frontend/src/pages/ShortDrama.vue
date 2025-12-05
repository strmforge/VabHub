<template>
  <div class="short-drama-page">
    <PageHeader
      title="短剧工作台"
      subtitle="集中查看短剧订阅 / 下载状态，串联闭环链路"
    >
      <template #actions>
        <v-btn
          color="primary"
          prepend-icon="mdi-bookmark-multiple"
          class="mr-2"
          @click="goToSubscriptions"
        >
          全部短剧订阅
        </v-btn>
        <v-btn
          color="secondary"
          variant="tonal"
          prepend-icon="mdi-download"
          class="mr-2"
          @click="goToDownloads"
        >
          下载中心
        </v-btn>
        <v-btn
          color="purple"
          variant="text"
          prepend-icon="mdi-puzzle"
          @click="goToPlugins"
        >
          插件配置
        </v-btn>
      </template>
    </PageHeader>

    <v-alert
      v-if="errorMessage"
      type="error"
      variant="tonal"
      class="mb-4"
    >
      {{ errorMessage }}
    </v-alert>

    <v-row class="mb-4" dense>
      <v-col cols="12" md="3">
        <v-card variant="outlined" class="stat-card">
          <v-card-text>
            <div class="text-caption text-medium-emphasis mb-1">短剧订阅</div>
            <div class="stat-value">{{ stats.totalSubscriptions }}</div>
            <div class="text-caption text-medium-emphasis">
              活跃 {{ stats.activeSubscriptions }} · 暂停 {{ stats.pausedSubscriptions }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card variant="outlined" class="stat-card">
          <v-card-text>
            <div class="text-caption text-medium-emphasis mb-1">短剧下载任务</div>
            <div class="stat-value">{{ stats.totalDownloads }}</div>
            <div class="text-caption text-medium-emphasis">
              下载中 {{ stats.downloadingDownloads }} · 已完成 {{ stats.completedDownloads }}
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card variant="outlined" class="stat-card">
          <v-card-text>
            <div class="text-caption text-medium-emphasis mb-1">平均单集时长</div>
            <div class="stat-value">{{ stats.avgEpisodeDuration }}</div>
            <div class="text-caption text-medium-emphasis">
              统计基于订阅元数据
            </div>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" md="3">
        <v-card variant="outlined" class="stat-card">
          <v-card-text>
            <div class="text-caption text-medium-emphasis mb-1">最近更新</div>
            <div class="stat-value text-body-1">{{ lastUpdatedText }}</div>
            <div class="text-caption text-medium-emphasis">
              <v-btn
                size="small"
                variant="text"
                prepend-icon="mdi-refresh"
                :loading="loading"
                @click="fetchData"
              >
                刷新
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <v-row dense>
      <v-col cols="12" lg="7">
        <v-card variant="outlined" class="h-100">
          <v-card-title class="d-flex align-center justify-space-between">
            <div>
              短剧订阅
              <v-chip size="small" color="purple" variant="flat" class="ml-2">
                {{ shortDramaSubscriptions.length }}
              </v-chip>
            </div>
            <v-btn variant="text" size="small" @click="goToSubscriptions">
              查看全部
            </v-btn>
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-row v-if="shortDramaSubscriptions.length" dense>
              <v-col
                v-for="subscription in shortDramaSubscriptions"
                :key="subscription.id"
                cols="12"
                md="6"
              >
                <SubscriptionCard
                  :subscription="subscription"
                  @edit="goToSubscriptions"
                  @delete="goToSubscriptions"
                  @search="goToSubscriptions"
                  @toggle-status="goToSubscriptions"
                />
                <div class="text-caption text-medium-emphasis mt-2">
                  {{ formatShortDramaMeta(subscription) }}
                </div>
              </v-col>
            </v-row>
            <v-alert
              v-else
              variant="tonal"
              type="info"
              density="comfortable"
            >
              暂无短剧订阅，前往订阅管理或插件页面创建。
            </v-alert>
          </v-card-text>
        </v-card>
      </v-col>
      <v-col cols="12" lg="5">
        <v-card variant="outlined" class="h-100">
          <v-card-title class="d-flex align-center justify-space-between">
            <div>短剧下载任务</div>
            <div class="d-flex ga-2">
              <v-select
                v-model="downloadStatusFilter"
                :items="downloadStatusOptions"
                density="compact"
                variant="outlined"
                hide-details
                style="width: 150px;"
              />
              <v-text-field
                v-model="downloadSearch"
                density="compact"
                variant="outlined"
                hide-details
                placeholder="搜索任务"
                prepend-inner-icon="mdi-magnify"
                style="width: 180px;"
              />
            </div>
          </v-card-title>
          <v-divider />
          <v-card-text>
            <v-data-table
              :headers="downloadHeaders"
              :items="filteredDownloads"
              :items-per-page="5"
              class="elevation-0"
              density="compact"
              no-data-text="暂无短剧下载任务"
            >
              <template #item.status="{ item }">
                <v-chip
                  size="x-small"
                  :color="statusColor(item.status)"
                  variant="flat"
                >
                  {{ statusText(item.status) }}
                </v-chip>
              </template>
              <template #item.progress="{ item }">
                <v-progress-linear
                  :model-value="item.progress || 0"
                  height="6"
                  :color="statusColor(item.status)"
                  rounded
                />
              </template>
              <template #item.actions="{ item }">
                <v-btn
                  variant="text"
                  size="small"
                  prepend-icon="mdi-open-in-new"
                  @click="goToDownloads"
                >
                  管理
                </v-btn>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import PageHeader from '@/components/common/PageHeader.vue'
import SubscriptionCard from '@/components/subscription/SubscriptionCard.vue'
import api, { downloadApi } from '@/services/api'
import { useToast } from '@/composables/useToast'

const toast = useToast()
const router = useRouter()

const loading = ref(false)
const errorMessage = ref('')
const lastUpdated = ref<Date | null>(null)

const subscriptions = ref<any[]>([])
const downloads = ref<any[]>([])

const downloadStatusFilter = ref('downloading')
const downloadSearch = ref('')

const downloadStatusOptions = [
  { title: '下载中', value: 'downloading' },
  { title: '已完成', value: 'completed' },
  { title: '暂停', value: 'paused' },
  { title: '失败', value: 'failed' },
  { title: '全部', value: 'all' }
]

const downloadHeaders = [
  { title: '标题', key: 'title', align: 'start' as const },
  { title: '状态', key: 'status', width: 90 },
  { title: '进度', key: 'progress', width: 140 },
  { title: '大小', key: 'size_gb', width: 90 },
  { title: '操作', key: 'actions', width: 80, sortable: false }
] as const

const stats = computed(() => {
  const total = subscriptions.value.length
  const active = subscriptions.value.filter((s) => s.status === 'active').length
  const paused = subscriptions.value.filter((s) => s.status === 'paused').length
  const downloadsTotal = downloads.value.length
  const downloadingCount = downloads.value.filter((d) => d.status === 'downloading').length
  const completedCount = downloads.value.filter((d) => d.status === 'completed').length

  const durations = subscriptions.value
    .map((s) => (s.extra_metadata?.short_drama?.episode_duration ?? 0) as number)
    .filter((d) => d > 0)

  const avgDuration = durations.length
    ? Math.round(durations.reduce((sum, d) => sum + d, 0) / durations.length / 60)
    : 0

  return {
    totalSubscriptions: total,
    activeSubscriptions: active,
    pausedSubscriptions: paused,
    totalDownloads: downloadsTotal,
    downloadingDownloads: downloadingCount,
    completedDownloads: completedCount,
    avgEpisodeDuration: avgDuration > 0 ? `${avgDuration} 分钟` : '未知'
  }
})

const shortDramaSubscriptions = computed(() => subscriptions.value.slice(0, 6))

const filteredDownloads = computed(() => {
  let list = downloads.value
  if (downloadStatusFilter.value !== 'all') {
    list = list.filter((item) => item.status === downloadStatusFilter.value)
  }
  if (downloadSearch.value) {
    const keyword = downloadSearch.value.toLowerCase()
    list = list.filter((item) => item.title?.toLowerCase().includes(keyword))
  }
  return list.slice(0, 8)
})

const lastUpdatedText = computed(() => {
  if (!lastUpdated.value) return '尚未刷新'
  return lastUpdated.value.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
})

const formatShortDramaMeta = (subscription: any) => {
  const meta = subscription.extra_metadata?.short_drama || subscription.short_drama_metadata
  if (!meta) return '尚未填写短剧元数据'
  const episodes = meta.total_episodes ? `${meta.total_episodes} 集` : '集数未知'
  const duration = meta.episode_duration
    ? `${Math.round(meta.episode_duration / 60)} 分钟/集`
    : '时长未知'
  const tag = Array.isArray(meta.source_category) ? meta.source_category.join(' / ') : meta.source_category
  return `${episodes} · ${duration}${tag ? ` · ${tag}` : ''}`
}

const statusColor = (status: string) => {
  const colors: Record<string, string> = {
    downloading: 'primary',
    completed: 'success',
    paused: 'warning',
    failed: 'error'
  }
  return colors[status] || 'grey'
}

const statusText = (status: string) => {
  const texts: Record<string, string> = {
    downloading: '下载中',
    completed: '已完成',
    paused: '已暂停',
    failed: '失败'
  }
  return texts[status] || status
}

const extractList = (payload: any) => {
  if (!payload) return []
  if (payload.items && Array.isArray(payload.items)) {
    return payload.items
  }
  if (Array.isArray(payload)) {
    return payload
  }
  return []
}

const fetchData = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const [subsResponse, downloadsResponse] = await Promise.all([
      api.get('/subscriptions', { params: { media_type: 'short_drama', page_size: 100 } }),
      downloadApi.getDownloads({ page: 1, page_size: 200 })
    ])

    const subsData = extractList(subsResponse.data)
    const downloadData = extractList(downloadsResponse.data).filter(
      (item: any) => item.media_type === 'short_drama'
    )

    subscriptions.value = subsData
    downloads.value = downloadData
    lastUpdated.value = new Date()
  } catch (error: any) {
    console.error('加载短剧数据失败:', error)
    errorMessage.value = error.message || '加载短剧数据失败'
    toast.error(errorMessage.value)
  } finally {
    loading.value = false
  }
}

const goToSubscriptions = () => {
  router.push({ name: 'Subscriptions', query: { media_type: 'short_drama' } })
}

const goToDownloads = () => {
  router.push({ name: 'Downloads', query: { media_type: 'short_drama' } })
}

const goToPlugins = () => {
  router.push({ name: 'Plugins' })
}

fetchData()
</script>

<style scoped lang="scss">
.short-drama-page {
  padding: 24px;
}

.stat-card {
  height: 100%;
}

.stat-value {
  font-size: 1.75rem;
  font-weight: 700;
}
</style>


