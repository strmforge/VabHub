<template>
  <div class="manga-library-page">
    <!-- 顶部 PageHeader -->
    <PageHeader title="本地漫画库">
      <template v-slot:actions>
        <v-btn
          color="info"
          variant="outlined"
          size="small"
          prepend-icon="mdi-book-open-variant"
          @click="$router.push({ name: 'ReadingHubPage' })"
          class="mr-4"
        >
          阅读中心
        </v-btn>
        <v-text-field
          v-model="searchKeyword"
          variant="outlined"
          density="compact"
          placeholder="搜索漫画..."
          prepend-inner-icon="mdi-magnify"
          hide-details
          clearable
          style="max-width: 300px;"
          class="mr-4"
          @keyup.enter="loadList"
        />
        <v-select
          v-model="selectedSourceId"
          :items="sourceOptions"
          item-title="name"
          item-value="id"
          label="源"
          variant="outlined"
          density="compact"
          hide-details
          clearable
          style="max-width: 200px;"
          class="mr-4"
        />
        <v-switch
          v-model="onlyFavorite"
          label="只看收藏"
          color="primary"
          hide-details
          class="mt-0"
        />
        <v-switch
          v-model="onlyWithUpdates"
          label="只看有更新"
          color="success"
          hide-details
          class="mt-0 ml-4"
        />
      </template>
    </PageHeader>

    <!-- 内容区域 -->
    <v-container fluid>
      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-12">
        <v-progress-circular indeterminate color="primary" size="64" />
        <div class="mt-4 text-body-1 text-medium-emphasis">加载中...</div>
      </div>

      <!-- 错误状态 -->
      <v-alert
        v-else-if="error"
        type="error"
        variant="tonal"
        class="mb-4"
      >
        {{ error }}
      </v-alert>

      <!-- 列表 -->
      <v-row v-else-if="items.length > 0" dense>
        <v-col
          v-for="item in items"
          :key="item.id"
          cols="6"
          sm="4"
          md="3"
          lg="2"
        >
          <v-card
            class="manga-card"
            elevation="2"
            @click="goToReader(item.id)"
          >
            <v-img
              :src="item.cover_url || '/placeholder-manga.jpg'"
              aspect-ratio="2/3"
              cover
              class="manga-cover"
            >
              <template v-slot:placeholder>
                <div class="d-flex align-center justify-center fill-height">
                  <v-icon size="64" color="grey-lighten-1">mdi-book-open-page-variant</v-icon>
                </div>
              </template>
              <div class="source-chip">
                <v-chip size="x-small" variant="flat" color="primary">
                  {{ getSourceName(item.source_id) }}
                </v-chip>
              </div>
              <!-- 新章节标记 -->
              <div class="new-chapters-badge" v-if="getSyncStatus(item.id)?.has_updates">
                <v-chip size="small" variant="flat" color="success" class="animate-pulse">
                  <v-icon start size="x-small">mdi-star</v-icon>
                  新 {{ getSyncStatus(item.id)?.new_chapter_count || 0 }} 话
                </v-chip>
              </div>
              <!-- 上次同步时间 -->
              <div class="sync-time-badge" v-if="getSyncStatus(item.id)?.last_sync_at">
                <v-chip size="x-small" variant="elevated" color="grey-lighten-2">
                  {{ formatSyncTime(getSyncStatus(item.id)!.last_sync_at) }}
                </v-chip>
              </div>
              <div class="progress-overlay" v-if="item.total_chapters">
                <div class="progress-text">
                  {{ item.downloaded_chapters || 0 }} / {{ item.total_chapters }} 话
                </div>
              </div>
              <div class="reading-progress-overlay" v-if="getProgress(item.id)">
                <div class="progress-text">
                  {{ getProgressText(item.id) }}
                </div>
              </div>
            </v-img>
            <v-card-text class="pa-2">
              <div class="text-body-2 font-weight-medium text-truncate" :title="item.title">
                {{ item.title }}
              </div>
              <div class="d-flex justify-space-between align-center mt-1">
                <v-icon
                  :icon="item.is_favorite ? 'mdi-heart' : 'mdi-heart-outline'"
                  :color="item.is_favorite ? 'red' : 'grey'"
                  size="small"
                  @click.stop="toggleFavorite(item)"
                />
                <div class="d-flex gap-2 align-center">
                  <v-btn
                    icon
                    size="x-small"
                    variant="text"
                    :title="isFollowing(item.id) ? '取消追更' : '追更'
                    "
                    @click.stop="toggleFollow(item)"
                  >
                    <v-icon size="small" :color="isFollowing(item.id) ? 'amber' : 'grey'">
                      {{ isFollowing(item.id) ? 'mdi-bell-ring' : 'mdi-bell-outline' }}
                    </v-icon>
                  </v-btn>
                  <v-btn
                    v-if="getProgress(item.id) && !getProgress(item.id)!.is_finished"
                    size="x-small"
                    color="primary"
                    variant="flat"
                    @click.stop="goToReader(item.id)"
                  >
                    继续阅读
                  </v-btn>
                  <v-btn
                    icon
                    size="x-small"
                    variant="text"
                    :loading="syncingSeries.has(item.id)"
                    @click.stop="syncSeries(item.id)"
                    title="同步章节"
                  >
                    <v-icon size="small">mdi-sync</v-icon>
                  </v-btn>
                </div>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- 空状态 -->
      <v-alert
        v-else
        type="info"
        variant="tonal"
        class="mt-4"
      >
        暂无本地漫画，前往「远程漫画」导入
      </v-alert>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="d-flex justify-center align-center pa-4">
        <v-pagination
          v-model="page"
          :length="totalPages"
          :total-visible="7"
          @update:model-value="loadList"
        />
      </div>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { mangaLocalApi, mangaRemoteApi, mangaProgressApi, readingFavoriteApi, mangaFollowApi } from '@/services/api'
import type {
  MangaSeriesLocal,
  MangaReadingProgress
} from '@/types/mangaLocal'
import type { RemoteMangaSourceInfo } from '@/types/mangaSource'
import type { FollowedMangaItem } from '@/types/mangaFollow'
import PageHeader from '@/components/common/PageHeader.vue'

const router = useRouter()
const toast = useToast()

// 状态
const loading = ref(false)
const error = ref<string | null>(null)
const items = ref<MangaSeriesLocal[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(24)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

// 搜索和过滤
const searchKeyword = ref('')
const selectedSourceId = ref<number | null>(null)
const onlyFavorite = ref(false)
const onlyWithUpdates = ref(false)

// 同步状态映射
const syncStatusMap = ref<Map<number, any>>(new Map())

// 源列表（用于显示源名称）
const sources = ref<RemoteMangaSourceInfo[]>([])

// 阅读进度映射
const progressMap = ref<Map<number, MangaReadingProgress>>(new Map())
const syncingSeries = ref<Set<number>>(new Set())

// 追更中的系列 ID 集合
const followingSeriesIds = ref<Set<number>>(new Set())

// 从后端刷新追更中的系列列表
const refreshFollowingFromServer = async () => {
  try {
    const list: FollowedMangaItem[] = await mangaFollowApi.listFollowing()
    followingSeriesIds.value = new Set(list.map(item => item.series_id))
  } catch (err) {
    // 静默失败，不影响主流程
  }
}

// 是否已追更
const isFollowing = (seriesId: number): boolean => {
  return followingSeriesIds.value.has(seriesId)
}

// 切换追更状态
const toggleFollow = async (item: MangaSeriesLocal) => {
  try {
    if (isFollowing(item.id)) {
      await mangaFollowApi.unfollowSeries(item.id)
      const next = new Set(followingSeriesIds.value)
      next.delete(item.id)
      followingSeriesIds.value = next
      toast.info('已取消追更')
    } else {
      await mangaFollowApi.followSeries(item.id)
      const next = new Set(followingSeriesIds.value)
      next.add(item.id)
      followingSeriesIds.value = next
      toast.success('已开始追更')
    }
  } catch (err: any) {
    console.error('切换追更状态失败:', err)
    toast.error(err.response?.data?.detail || err.message || '操作追更失败')
  }
}

// 源选项
const sourceOptions = computed(() => {
  return sources.value.map(s => ({
    id: s.id,
    name: s.name
  }))
})

// 获取源名称
const getSourceName = (sourceId: number): string => {
  const source = sources.value.find(s => s.id === sourceId)
  return source?.name || '未知源'
}

// 加载列表
const loadList = async () => {
  try {
    loading.value = true
    error.value = null

    const response = await mangaLocalApi.listSeries({
      keyword: searchKeyword.value || undefined,
      source_id: selectedSourceId.value || undefined,
      favorite: onlyFavorite.value || undefined,
      page: page.value,
      page_size: pageSize.value
    })

    let filteredItems = response.items || []

    // 客户端筛选：只看有更新
    if (onlyWithUpdates.value) {
      filteredItems = filteredItems.filter(item => 
        // new_chapter_count 目前未在类型中声明，这里使用 any 访问以保持兼容
        (((item as any).new_chapter_count || 0) as number) > 0
      )
    }

    items.value = filteredItems
    total.value = onlyWithUpdates.value ? filteredItems.length : (response.total || 0)

    // 加载所有系列的阅读进度和同步状态
    await loadAllProgress()
    await loadAllSyncStatus()
    await refreshFollowingFromServer()
  } catch (err: any) {
    console.error('加载本地漫画列表失败:', err)
    error.value = err.response?.data?.detail || err.message || '加载列表失败'
    toast.error(error.value || '加载列表失败')
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 加载所有系列的阅读进度
const loadAllProgress = async () => {
  const progressPromises = items.value.map(async (item) => {
    try {
      const progress = await mangaProgressApi.getSeriesProgress(item.id)
      if (progress) {
        progressMap.value.set(item.id, progress)
      }
    } catch (err) {
      // 静默失败
    }
  })
  await Promise.all(progressPromises)
}

// 获取进度
const getProgress = (seriesId: number): MangaReadingProgress | null => {
  return progressMap.value.get(seriesId) || null
}

// 获取进度文本
const getProgressText = (seriesId: number): string => {
  const progress = getProgress(seriesId)
  if (!progress) return ''
  
  if (progress.is_finished) {
    return '已读完'
  }
  
  // 使用 chapter_id 字段来判断是否有有效进度
  if (progress.chapter_id && progress.last_page_index) {
    return `第 ${progress.last_page_index} 页`
  }
  
  return '已开始阅读'
}

// 获取同步状态
const getSyncStatus = (seriesId: number) => {
  return syncStatusMap.value.get(seriesId)
}

// 格式化同步时间
const formatSyncTime = (timeStr: string | null): string => {
  if (!timeStr) return ''
  const time = new Date(timeStr)
  const now = new Date()
  const diff = now.getTime() - time.getTime()
  const hours = Math.floor(diff / (1000 * 60 * 60))
  
  if (hours < 1) {
    const minutes = Math.floor(diff / (1000 * 60))
    return `${minutes}分钟前`
  } else if (hours < 24) {
    return `${hours}小时前`
  } else {
    const days = Math.floor(hours / 24)
    return `${days}天前`
  }
}

// 加载所有系列的同步状态
const loadAllSyncStatus = async () => {
  const statusPromises = items.value.map(async (item) => {
    try {
      const status = await mangaLocalApi.getSeriesSyncStatus(item.id)
      syncStatusMap.value.set(item.id, status)
    } catch (err) {
      // 静默失败，可能该系列没有同步过
    }
  })
  await Promise.all(statusPromises)
}

// 加载源列表
const loadSources = async () => {
  try {
    const data = await mangaRemoteApi.listSources({ only_enabled: true })
    sources.value = data
  } catch (err: any) {
    console.error('加载源列表失败:', err)
  }
}

// 跳转到阅读器
const goToReader = (seriesId: number) => {
  // 不指定 chapter_id，让阅读器根据进度自动定位
  router.push({ name: 'MangaReaderPage', params: { series_id: seriesId } })
}

// 同步系列
const syncSeries = async (seriesId: number) => {
  try {
    syncingSeries.value.add(seriesId)
    const result = await mangaLocalApi.syncSeries(seriesId, { download_new: false })
    
    const newChapters = result.new_chapters || 0
    if (newChapters > 0) {
      toast.success(`《${result.series_title}》同步完成，新增 ${newChapters} 个章节`)
      // 重新加载列表以更新统计和同步状态
      await loadList()
    } else {
      toast.info('没有新章节')
      // 即使没有新章节，也要更新同步状态
      await loadAllSyncStatus()
    }
  } catch (err: any) {
    console.error('同步系列失败:', err)
    toast.error(err.response?.data?.detail || err.message || '同步失败')
  } finally {
    syncingSeries.value.delete(seriesId)
  }
}

// 切换收藏状态
const toggleFavorite = async (item: MangaSeriesLocal) => {
  try {
    if (item.is_favorite) {
      // 取消收藏
      await readingFavoriteApi.removeFavorite({
        media_type: 'MANGA',
        target_id: item.id
      })
      toast.success('已取消收藏')
    } else {
      // 添加收藏
      await readingFavoriteApi.addFavorite({
        media_type: 'MANGA',
        target_id: item.id
      })
      toast.success('已添加到收藏')
    }
    
    // 重新加载列表以更新状态
    await loadList()
  } catch (err: any) {
    console.error('操作收藏失败:', err)
    toast.error(err.response?.data?.detail || err.message || '操作失败')
  }
}

// 监听过滤条件变化
watch([page, searchKeyword, selectedSourceId, onlyFavorite, onlyWithUpdates], () => {
  loadList()
})

// 初始化
onMounted(() => {
  loadSources()
  loadList()
  refreshFollowingFromServer()
})
</script>

<style scoped lang="scss">
.manga-library-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.manga-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2) !important;
  }

  .manga-cover {
    position: relative;
    border-radius: 4px 4px 0 0;

    .source-chip {
      position: absolute;
      top: 8px;
      left: 8px;
    }

    .new-chapters-badge {
      position: absolute;
      top: 8px;
      right: 8px;
      z-index: 2;
      
      .animate-pulse {
        animation: pulse 2s infinite;
      }
    }

    .sync-time-badge {
      position: absolute;
      bottom: 36px;
      right: 8px;
    }

    .progress-overlay {
      position: absolute;
      bottom: 0;
      left: 0;
      right: 0;
      background: linear-gradient(to top, rgba(0, 0, 0, 0.7), transparent);
      padding: 8px;
      color: white;
      font-size: 12px;

      .progress-text {
        text-align: center;
      }
    }

    .reading-progress-overlay {
      position: absolute;
      top: 8px;
      left: 8px;
      background: rgba(0, 0, 0, 0.7);
      padding: 4px 8px;
      border-radius: 4px;
      color: white;
      font-size: 11px;
    }
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
}
</style>

