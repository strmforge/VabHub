<template>
  <div class="reading-hub-page">
    <!-- 顶部 PageHeader -->
    <PageHeader title="阅读中心" subtitle="统一管理小说 / 漫画 / 有声书的阅读与收听进度">
      <template v-slot:actions>
        <v-btn
          variant="outlined"
          size="small"
          prepend-icon="mdi-bookshelf"
          @click="$router.push({ name: 'MyShelf' })"
          class="mr-2"
        >
          我的书架
        </v-btn>
        <v-btn
          variant="outlined"
          size="small"
          prepend-icon="mdi-heart"
          @click="$router.push({ name: 'ReadingFavoriteShelf' })"
          class="mr-2"
        >
          我的收藏
        </v-btn>
        <v-btn
          variant="outlined"
          size="small"
          prepend-icon="mdi-book-open-page-variant"
          @click="$router.push({ name: 'NovelCenter' })"
          class="mr-2"
        >
          小说中心
        </v-btn>
        <v-btn
          variant="outlined"
          size="small"
          prepend-icon="mdi-headphones"
          @click="$router.push({ name: 'AudiobookCenter' })"
          class="mr-2"
        >
          有声书中心
        </v-btn>
        <v-btn
          variant="outlined"
          size="small"
          prepend-icon="mdi-book-open-variant"
          @click="$router.push({ name: 'MangaLibraryPage' })"
        >
          本地漫画库
        </v-btn>
      </template>
    </PageHeader>

    <!-- 内容区域 -->
    <v-container fluid>
      <!-- Summary 卡片 -->
      <v-row v-if="stats" class="mb-4">
        <v-col cols="6" sm="3">
          <v-card 
            class="cursor-pointer hover-card"
            @click="$router.push({ name: 'MyShelf', query: { status: 'active' } })"
          >
            <v-card-text class="text-center">
              <div class="text-h4 font-weight-bold text-primary">{{ stats.ongoing_count }}</div>
              <div class="text-caption text-medium-emphasis">正在阅读</div>
              <div class="text-caption text-primary mt-1">
                <v-icon size="small">mdi-arrow-right</v-icon> 查看进行中
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card 
            class="cursor-pointer hover-card"
            @click="$router.push({ name: 'MyShelf', query: { status: 'finished' } })"
          >
            <v-card-text class="text-center">
              <div class="text-h4 font-weight-bold text-success">{{ stats.finished_count }}</div>
              <div class="text-caption text-medium-emphasis">已完成</div>
              <div class="text-caption text-success mt-1">
                <v-icon size="small">mdi-arrow-right</v-icon> 查看已完成
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card 
            class="cursor-pointer hover-card"
            @click="$router.push({ name: 'ReadingFavoriteShelf' })"
          >
            <v-card-text class="text-center">
              <div class="text-h4 font-weight-bold text-warning">{{ stats.favorites_count }}</div>
              <div class="text-caption text-medium-emphasis">收藏</div>
              <div class="text-caption text-warning mt-1">
                <v-icon size="small">mdi-arrow-right</v-icon> 查看收藏
              </div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="6" sm="3">
          <v-card 
            class="cursor-pointer hover-card"
            @click="activeTab = 'timeline'"
          >
            <v-card-text class="text-center">
              <div class="text-h4 font-weight-bold text-info">{{ stats.recent_activity_count }}</div>
              <div class="text-caption text-medium-emphasis">最近7天活动</div>
              <div class="text-caption text-info mt-1">
                <v-icon size="small">mdi-arrow-right</v-icon> 查看时间线
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Tabs -->
      <v-tabs v-model="activeTab" class="mb-4">
        <v-tab value="overview">概览</v-tab>
        <v-tab value="timeline">时间线</v-tab>
        <v-tab value="favorites">收藏</v-tab>
      </v-tabs>

      <!-- 过滤控件（概览和时间线共用） -->
      <div v-if="activeTab !== 'favorites'" class="d-flex align-center flex-wrap gap-3 mb-4">
        <v-select
          v-model="filterMediaType"
          :items="mediaTypeOptions"
          item-title="label"
          item-value="value"
          label="媒体类型"
          variant="outlined"
          density="compact"
          hide-details
          clearable
          style="max-width: 160px;"
        />
        <v-select
          v-model="filterStatus"
          :items="statusOptions"
          item-title="label"
          item-value="value"
          label="阅读状态"
          variant="outlined"
          density="compact"
          hide-details
          clearable
          style="max-width: 160px;"
        />
        <v-select
          v-model="sortBy"
          :items="sortOptions"
          item-title="label"
          item-value="value"
          label="排序"
          variant="outlined"
          density="compact"
          hide-details
          style="max-width: 160px;"
        />
      </div>

      <!-- 概览 Tab -->
      <div v-if="activeTab === 'overview'">
        <!-- 加载状态 -->
        <div v-if="loadingOngoing" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64" />
          <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
        </div>

        <!-- 错误状态 -->
        <v-alert v-else-if="errorOngoing" type="error" variant="tonal" class="mb-4">
          {{ errorOngoing }}
        </v-alert>

        <!-- 列表 -->
        <v-row v-else-if="filteredOngoingItems.length > 0" dense>
          <v-col
            v-for="item in filteredOngoingItems"
            :key="`${item.media_type}-${item.item_id}`"
            cols="12"
            sm="6"
            md="4"
            lg="3"
          >
            <ReadingItemCard
              :item="item"
              type="ongoing"
              @click="goToItem(item)"
            />
          </v-col>
        </v-row>

        <!-- 空状态 -->
        <v-card v-else class="text-center py-8">
          <v-card-text>
            <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-book-open-blank-variant</v-icon>
            <p class="text-h6 mb-2">暂无正在进行的阅读</p>
            <p class="text-body-2 text-medium-emphasis mb-6">
              开始阅读小说、漫画或收听有声书后，进度会显示在这里
            </p>
            
            <!-- 快捷入口按钮组 -->
            <div class="d-flex flex-wrap gap-3 justify-center">
              <v-btn
                color="primary"
                prepend-icon="mdi-book-open-variant"
                @click="$router.push({ name: 'NovelCenter' })"
                variant="flat"
              >
                去小说中心看看
              </v-btn>
              <v-btn
                color="info"
                prepend-icon="mdi-headphones"
                @click="$router.push({ name: 'AudiobookCenter' })"
                variant="flat"
              >
                去有声书中心看看
              </v-btn>
              <v-btn
                color="success"
                prepend-icon="mdi-image-multiple"
                @click="$router.push({ name: 'MangaCenter' })"
                variant="flat"
              >
                去漫画中心看看
              </v-btn>
            </div>
            
            <!-- 额外提示 -->
            <p class="text-caption text-medium-emphasis mt-4">
              或者查看已完成的收藏内容
            </p>
            <div class="d-flex gap-2 justify-center">
              <v-btn
                variant="text"
                prepend-icon="mdi-bookshelf"
                @click="$router.push({ name: 'MyShelf', query: { status: 'finished' } })"
                size="small"
              >
                查看已完成
              </v-btn>
              <v-btn
                variant="text"
                prepend-icon="mdi-heart"
                @click="$router.push({ name: 'ReadingFavoriteShelf' })"
                size="small"
              >
                查看收藏
              </v-btn>
            </div>
          </v-card-text>
        </v-card>
      </div>

      <!-- 时间线 Tab -->
      <div v-if="activeTab === 'timeline'">
        <!-- 加载状态 -->
        <div v-if="loadingActivity" class="text-center py-12">
          <v-progress-circular indeterminate color="primary" size="64" />
          <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
        </div>

        <!-- 错误状态 -->
        <v-alert v-else-if="errorActivity" type="error" variant="tonal" class="mb-4">
          {{ errorActivity }}
        </v-alert>

        <!-- 时间线列表 -->
        <v-timeline v-else-if="filteredActivityItems.length > 0" side="end" density="compact">
          <v-timeline-item
            v-for="item in filteredActivityItems"
            :key="`${item.media_type}-${item.item_id}-${item.occurred_at}`"
            :dot-color="getMediaColor(item.media_type)"
            size="small"
          >
            <template v-slot:icon>
              <v-icon size="small" color="white">{{ getActivityIcon(item.activity_type) }}</v-icon>
            </template>
            <v-card class="timeline-card" @click="goToActivityItem(item)">
              <v-card-text class="d-flex align-center pa-3">
                <v-avatar size="48" rounded class="mr-3">
                  <v-img v-if="item.cover_url" :src="item.cover_url" cover />
                  <v-icon v-else :color="getMediaColor(item.media_type)">
                    {{ getMediaIcon(item.media_type) }}
                  </v-icon>
                </v-avatar>
                <div class="flex-grow-1">
                  <div class="text-subtitle-2 font-weight-medium">{{ item.title }}</div>
                  <div class="text-caption text-medium-emphasis">{{ item.activity_label }}</div>
                  <div class="text-caption text-disabled">{{ formatDate(item.occurred_at) }}</div>
                </div>
                <v-chip :color="getMediaColor(item.media_type)" size="x-small" variant="flat">
                  {{ getMediaLabel(item.media_type) }}
                </v-chip>
              </v-card-text>
            </v-card>
          </v-timeline-item>
        </v-timeline>

        <!-- 空状态 -->
        <EmptyState
          v-else
          icon="mdi-timeline-clock-outline"
          title="暂无阅读活动"
          description="你的阅读、收听活动会按时间顺序显示在这里"
        />
      </div>

      <!-- 收藏 Tab -->
      <div v-if="activeTab === 'favorites'">
        <v-card class="text-center py-8">
          <v-card-text>
            <v-icon size="64" color="warning" class="mb-4">mdi-heart</v-icon>
            <div class="text-h6 mb-2">我的收藏在独立页面</div>
            <div class="text-body-2 text-medium-emphasis mb-4">
              统一收藏书架支持跨媒体类型管理收藏
            </div>
            <v-btn
              color="warning"
              variant="flat"
              prepend-icon="mdi-heart"
              @click="$router.push({ name: 'ReadingFavoriteShelf' })"
            >
              打开我的收藏
            </v-btn>
          </v-card-text>
        </v-card>
      </div>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { readingHubApi } from '@/services/api'
import type {
  ReadingOngoingItem,
  ReadingActivityItem,
  ReadingStats,
  ReadingMediaType,
  ReadingStatus
} from '@/types/readingHub'
import PageHeader from '@/components/common/PageHeader.vue'
import ReadingItemCard from '@/components/reading/ReadingItemCard.vue'
import EmptyState from '@/components/common/EmptyState.vue'

const router = useRouter()
const route = useRoute()
const toast = useToast()

// 状态
const activeTab = ref<'overview' | 'timeline' | 'favorites'>('overview')

// 过滤
const filterMediaType = ref<ReadingMediaType | null>(null)
const filterStatus = ref<ReadingStatus | null>(null)
const sortBy = ref<'activity' | 'title'>('activity')

// 正在进行
const loadingOngoing = ref(false)
const errorOngoing = ref<string | null>(null)
const ongoingItems = ref<ReadingOngoingItem[]>([])

// 活动时间线
const loadingActivity = ref(false)
const errorActivity = ref<string | null>(null)
const activityItems = ref<ReadingActivityItem[]>([])

// 统计
const stats = ref<ReadingStats | null>(null)

// 选项
const mediaTypeOptions = [
  { label: '全部', value: null },
  { label: '小说', value: 'NOVEL' as ReadingMediaType },
  { label: '有声书', value: 'AUDIOBOOK' as ReadingMediaType },
  { label: '漫画', value: 'MANGA' as ReadingMediaType }
]

const statusOptions = [
  { label: '全部', value: null },
  { label: '未开始', value: 'not_started' as ReadingStatus },
  { label: '进行中', value: 'in_progress' as ReadingStatus },
  { label: '已完成', value: 'finished' as ReadingStatus }
]

const sortOptions = [
  { label: '最近活动', value: 'activity' },
  { label: '标题 (A→Z)', value: 'title' }
]

// 过滤后的概览列表
const filteredOngoingItems = computed(() => {
  let items = [...ongoingItems.value]
  
  if (filterMediaType.value) {
    items = items.filter(item => item.media_type === filterMediaType.value)
  }
  if (filterStatus.value) {
    items = items.filter(item => item.status === filterStatus.value)
  }
  
  if (sortBy.value === 'title') {
    items.sort((a, b) => a.title.localeCompare(b.title, 'zh-CN'))
  }
  // 默认按活动时间排序（已经是后端返回的顺序）
  
  return items
})

// 过滤后的活动列表
const filteredActivityItems = computed(() => {
  let items = [...activityItems.value]
  
  if (filterMediaType.value) {
    items = items.filter(item => item.media_type === filterMediaType.value)
  }
  if (filterStatus.value) {
    items = items.filter(item => item.status === filterStatus.value)
  }
  
  return items
})

// 加载正在进行
const loadOngoing = async () => {
  try {
    loadingOngoing.value = true
    errorOngoing.value = null
    const data = await readingHubApi.listOngoing({ limit_per_type: 20 })
    ongoingItems.value = data
  } catch (err: unknown) {
    const error = err as { response?: { data?: { detail?: string } }; message?: string }
    console.error('加载正在进行列表失败:', err)
    errorOngoing.value = error.response?.data?.detail || error.message || '加载失败'
    toast.error(errorOngoing.value || '加载失败')
    ongoingItems.value = []
  } finally {
    loadingOngoing.value = false
  }
}

// 加载活动时间线
const loadActivity = async () => {
  try {
    loadingActivity.value = true
    errorActivity.value = null
    const data = await readingHubApi.getRecentActivity({ limit: 50 })
    activityItems.value = data
  } catch (err: unknown) {
    const error = err as { response?: { data?: { detail?: string } }; message?: string }
    console.error('加载活动时间线失败:', err)
    errorActivity.value = error.response?.data?.detail || error.message || '加载失败'
    toast.error(errorActivity.value || '加载失败')
    activityItems.value = []
  } finally {
    loadingActivity.value = false
  }
}

// 加载统计
const loadStats = async () => {
  try {
    const data = await readingHubApi.getStats()
    stats.value = data
  } catch (err: unknown) {
    console.error('加载统计失败:', err)
  }
}

// 跳转到项目
const goToItem = (item: ReadingOngoingItem) => {
  router.push({
    name: item.route_name,
    params: item.route_params
  })
}

const goToActivityItem = (item: ReadingActivityItem) => {
  router.push({
    name: item.route_name,
    params: item.route_params
  })
}

// 辅助函数
const getMediaColor = (type: ReadingMediaType): string => {
  const colors: Record<ReadingMediaType, string> = {
    NOVEL: 'blue',
    AUDIOBOOK: 'purple',
    MANGA: 'orange'
  }
  return colors[type] || 'grey'
}

const getMediaIcon = (type: ReadingMediaType): string => {
  const icons: Record<ReadingMediaType, string> = {
    NOVEL: 'mdi-book-open-page-variant',
    AUDIOBOOK: 'mdi-headphones',
    MANGA: 'mdi-book-open-variant'
  }
  return icons[type] || 'mdi-book'
}

const getMediaLabel = (type: ReadingMediaType): string => {
  const labels: Record<ReadingMediaType, string> = {
    NOVEL: '小说',
    AUDIOBOOK: '有声书',
    MANGA: '漫画'
  }
  return labels[type] || type
}

const getActivityIcon = (type: string): string => {
  const icons: Record<string, string> = {
    read: 'mdi-book-open-page-variant',
    listen: 'mdi-headphones',
    update: 'mdi-update'
  }
  return icons[type] || 'mdi-circle'
}

const formatDate = (dateStr: string): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))

  if (days === 0) {
    const hours = Math.floor(diff / (1000 * 60 * 60))
    if (hours === 0) {
      const mins = Math.floor(diff / (1000 * 60))
      return mins <= 1 ? '刚刚' : `${mins} 分钟前`
    }
    return `${hours} 小时前`
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days} 天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

// 监听 Tab 切换
watch(activeTab, (newTab) => {
  if (newTab === 'overview' && ongoingItems.value.length === 0) {
    loadOngoing()
  } else if (newTab === 'timeline' && activityItems.value.length === 0) {
    loadActivity()
  }
})

// 处理 URL query 参数（从通知跳转）
watch(() => route.query, (query) => {
  if (query.focus_media_type) {
    filterMediaType.value = query.focus_media_type as ReadingMediaType
    activeTab.value = 'overview'
  }
}, { immediate: true })

// 初始化
onMounted(() => {
  loadOngoing()
  loadStats()
})
</script>

<style scoped lang="scss">
.reading-hub-page {
  min-height: 100vh;
  background-color: rgb(var(--v-theme-surface));
}

.timeline-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  
  &:hover {
    transform: translateX(4px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }
}

.hover-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
  }
}

.cursor-pointer {
  cursor: pointer;
}
</style>
