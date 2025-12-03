<template>
  <div class="rss-item-list">
    <!-- 标题和统计 -->
    <div class="d-flex align-center justify-space-between mb-4">
      <div>
        <h3 class="text-h6">RSS项列表</h3>
        <p v-if="stats" class="text-caption text-medium-emphasis mt-1">
          总计: {{ stats.total }} | 
          已处理: {{ stats.processed }} | 
          已下载: {{ stats.downloaded }} | 
          跳过: {{ stats.skipped }}
        </p>
      </div>
      <v-btn
        size="small"
        variant="text"
        prepend-icon="mdi-refresh"
        :loading="loading"
        @click="loadItems"
      >
        刷新
      </v-btn>
    </div>

    <!-- 过滤 -->
    <v-card variant="outlined" class="mb-4">
      <v-card-text class="py-2">
        <v-row align="center" dense>
          <v-col cols="12" md="4">
            <v-text-field
              v-model="searchQuery"
              placeholder="搜索RSS项..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="processedFilter"
              :items="processedOptions"
              label="处理状态"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="downloadedFilter"
              :items="downloadedOptions"
              label="下载状态"
              variant="outlined"
              density="compact"
              hide-details
              clearable
            />
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- 加载状态 -->
    <template v-if="loading && items.length === 0">
      <v-card>
        <v-card-text class="d-flex justify-center align-center" style="min-height: 200px;">
          <div class="text-center">
            <v-progress-circular indeterminate color="primary" size="48" />
            <div class="mt-4 text-body-2 text-medium-emphasis">加载中...</div>
          </div>
        </v-card-text>
      </v-card>
    </template>

    <!-- 空状态 -->
    <template v-else-if="filteredItems.length === 0">
      <v-card variant="outlined">
        <v-card-text class="text-center pa-8">
          <v-icon size="64" color="grey-darken-1" class="mb-4">mdi-rss-box</v-icon>
          <div class="text-h6 font-weight-medium mb-2">暂无RSS项</div>
          <div class="text-body-2 text-medium-emphasis">
            该订阅还没有RSS项，请先检查更新
          </div>
        </v-card-text>
      </v-card>
    </template>

    <!-- RSS项列表 -->
    <template v-else>
      <v-card variant="outlined">
        <v-list>
          <template v-for="(item, index) in filteredItems" :key="item.id">
            <v-list-item
              :class="{
                'rss-item-processed': item.processed,
                'rss-item-downloaded': item.downloaded
              }"
            >
              <template #prepend>
                <v-icon
                  :color="getItemIconColor(item)"
                  class="me-3"
                >
                  {{ getItemIcon(item) }}
                </v-icon>
              </template>

              <v-list-item-title class="text-body-1 font-weight-medium">
                {{ item.title }}
              </v-list-item-title>

              <v-list-item-subtitle class="mt-1">
                <div class="d-flex align-center flex-wrap gap-2">
                  <v-chip
                    :color="item.processed ? 'success' : 'grey'"
                    size="x-small"
                    variant="flat"
                  >
                    {{ item.processed ? '已处理' : '未处理' }}
                  </v-chip>
                  <v-chip
                    v-if="item.downloaded"
                    color="primary"
                    size="x-small"
                    variant="flat"
                  >
                    已下载
                  </v-chip>
                  <span class="text-caption text-medium-emphasis">
                    <v-icon size="14" class="me-1">mdi-clock-outline</v-icon>
                    {{ formatDate(item.pub_date) }}
                  </span>
                  <span v-if="item.download_task_id" class="text-caption text-medium-emphasis">
                    <v-icon size="14" class="me-1">mdi-download</v-icon>
                    任务: {{ item.download_task_id }}
                  </span>
                </div>
              </v-list-item-subtitle>

              <template #append>
                <v-btn
                  icon="mdi-open-in-new"
                  size="small"
                  variant="text"
                  @click="openLink(item.link)"
                />
              </template>
            </v-list-item>
            <v-divider v-if="index < filteredItems.length - 1" />
          </template>
        </v-list>
      </v-card>

      <!-- 分页 -->
      <v-pagination
        v-if="totalPages > 1"
        v-model="currentPage"
        :length="totalPages"
        :total-visible="7"
        class="mt-4"
        @update:model-value="loadItems"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { rssApi } from '@/services/api'

interface RSSItem {
  id: number
  subscription_id: number
  item_hash: string
  title: string
  link: string
  description?: string
  pub_date?: string
  processed: boolean
  downloaded: boolean
  download_task_id?: string
  created_at: string
  processed_at?: string
}

interface Stats {
  total: number
  processed: number
  unprocessed: number
  downloaded: number
  skipped: number
}

interface Props {
  subscriptionId: number
  autoLoad?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  autoLoad: true
})

const loading = ref(false)
const items = ref<RSSItem[]>([])
const stats = ref<Stats | null>(null)
const searchQuery = ref('')
const processedFilter = ref<boolean | null>(null)
const downloadedFilter = ref<boolean | null>(null)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

const processedOptions = [
  { title: '全部', value: null },
  { title: '已处理', value: true },
  { title: '未处理', value: false }
]

const downloadedOptions = [
  { title: '全部', value: null },
  { title: '已下载', value: true },
  { title: '未下载', value: false }
]

const filteredItems = computed(() => {
  let result = items.value

  // 搜索过滤
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    result = result.filter(item =>
      item.title.toLowerCase().includes(query) ||
      (item.description && item.description.toLowerCase().includes(query))
    )
  }

  // 处理状态过滤
  if (processedFilter.value !== null) {
    result = result.filter(item => item.processed === processedFilter.value)
  }

  // 下载状态过滤
  if (downloadedFilter.value !== null) {
    result = result.filter(item => item.downloaded === downloadedFilter.value)
  }

  return result
})

const totalPages = computed(() => {
  return Math.ceil(total.value / pageSize.value)
})

const loadItems = async () => {
  if (!props.subscriptionId) return

  loading.value = true
  try {
    const params: any = {
      page: currentPage.value,
      page_size: pageSize.value
    }
    if (processedFilter.value !== null) {
      params.processed = processedFilter.value
    }
    if (downloadedFilter.value !== null) {
      params.downloaded = downloadedFilter.value
    }

    const [itemsResponse, statsResponse] = await Promise.all([
      rssApi.getSubscriptionRSSItems(props.subscriptionId, params),
      rssApi.getSubscriptionRSSItemsStats(props.subscriptionId)
    ])

    if (itemsResponse.data.items) {
      items.value = itemsResponse.data.items
      total.value = itemsResponse.data.total || 0
    } else {
      items.value = Array.isArray(itemsResponse.data) ? itemsResponse.data : []
      total.value = items.value.length
    }

    if (statsResponse.data) {
      stats.value = statsResponse.data
    }
  } catch (error: any) {
    console.error('加载RSS项列表失败:', error)
    items.value = []
    stats.value = null
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  if (!props.subscriptionId) return

  try {
    const response = await rssApi.getSubscriptionRSSItemsStats(props.subscriptionId)
    if (response.data) {
      stats.value = response.data
    }
  } catch (error: any) {
    console.error('加载RSS项统计失败:', error)
  }
}

const getItemIcon = (item: RSSItem) => {
  if (item.downloaded) return 'mdi-check-circle'
  if (item.processed) return 'mdi-check'
  return 'mdi-circle-outline'
}

const getItemIconColor = (item: RSSItem) => {
  if (item.downloaded) return 'success'
  if (item.processed) return 'info'
  return 'grey'
}

const formatDate = (date?: string) => {
  if (!date) return '未知'
  try {
    return new Date(date).toLocaleString('zh-CN')
  } catch {
    return date
  }
}

const openLink = (link: string) => {
  if (link) {
    window.open(link, '_blank')
  }
}

// 监听订阅ID变化
watch(() => props.subscriptionId, (newId) => {
  if (newId && props.autoLoad) {
    currentPage.value = 1
    loadItems()
  }
})

// 监听过滤条件变化
watch([processedFilter, downloadedFilter], () => {
  if (props.subscriptionId) {
    currentPage.value = 1
    loadItems()
  }
})

onMounted(() => {
  if (props.subscriptionId && props.autoLoad) {
    loadItems()
  }
})

// 暴露方法供父组件调用
defineExpose({
  loadItems,
  loadStats
})
</script>

<style scoped>
.rss-item-list {
  width: 100%;
}

.rss-item-processed {
  opacity: 0.8;
}

.rss-item-downloaded {
  background: rgba(var(--v-theme-success), 0.1);
}
</style>

