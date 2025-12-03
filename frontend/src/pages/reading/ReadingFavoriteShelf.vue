<template>
  <div class="reading-favorite-shelf-page">
    <!-- 页面头部 -->
    <v-container>
      <div class="d-flex justify-space-between align-center mb-4">
        <div>
          <h1 class="text-h4 mb-1">我的收藏</h1>
          <p class="text-body-2 text-medium-emphasis">跨媒体类型的个人收藏中心</p>
        </div>
        <div>
          <v-btn
            variant="outlined"
            prepend-icon="mdi-bookshelf"
            @click="$router.push({ name: 'MyShelf' })"
            class="mr-2"
          >
            我的书架
          </v-btn>
          <v-btn
            variant="outlined"
            prepend-icon="mdi-book-open-variant"
            @click="$router.push({ name: 'ReadingHubPage' })"
            class="mr-2"
          >
            阅读中心
          </v-btn>
          <v-btn
            variant="outlined"
            prepend-icon="mdi-book-open-page-variant"
            @click="$router.push({ name: 'NovelCenter' })"
            class="mr-2"
          >
            小说中心
          </v-btn>
          <v-btn
            variant="outlined"
            prepend-icon="mdi-headphones"
            @click="$router.push({ name: 'AudiobookCenter' })"
            class="mr-2"
          >
            有声书中心
          </v-btn>
          <v-btn
            variant="outlined"
            prepend-icon="mdi-image-multiple"
            @click="$router.push({ name: 'MangaCenter' })"
          >
            漫画中心
          </v-btn>
        </div>
      </div>

      <!-- 筛选区域 -->
      <v-card class="mb-4">
        <v-card-text>
          <div class="d-flex align-center flex-wrap gap-4">
            <!-- 媒体类型切换 Tab -->
            <v-tabs v-model="activeMediaType" @update:model-value="handleMediaTypeChange">
              <v-tab value="all">全部</v-tab>
              <v-tab value="NOVEL">小说</v-tab>
              <v-tab value="AUDIOBOOK">有声书</v-tab>
              <v-tab value="MANGA">漫画</v-tab>
            </v-tabs>

            <!-- 关键字搜索 -->
            <v-text-field
              v-model="filters.keyword"
              placeholder="搜索标题..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              style="max-width: 300px;"
              @keyup.enter="loadFavorites"
              clearable
            />

            <!-- 搜索按钮 -->
            <v-btn
              color="primary"
              prepend-icon="mdi-magnify"
              @click="loadFavorites"
            >
              搜索
            </v-btn>
          </div>
        </v-card-text>
      </v-card>

      <!-- 加载状态 -->
      <div v-if="loading" class="text-center py-8">
        <v-progress-circular indeterminate color="primary" />
        <p class="text-body-2 text-medium-emphasis mt-2">加载中...</p>
      </div>

      <!-- 空状态 -->
      <v-card v-else-if="items.length === 0" class="text-center py-8">
        <v-card-text>
          <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-heart-outline</v-icon>
          <p class="text-h6 mb-2">暂无收藏</p>
          <p class="text-body-2 text-medium-emphasis mb-6">
            {{ activeMediaType === 'all' ? '还没有收藏任何内容，从下面开始发现精彩内容吧' : 
               `还没有收藏${getMediaTypeLabel(activeMediaType)}，去${getMediaTypeLabel(activeMediaType)}中心看看吧` }}
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
            或者查看书架中已有的阅读进度
          </p>
          <div class="d-flex gap-2 justify-center">
            <v-btn
              variant="text"
              prepend-icon="mdi-bookshelf"
              @click="$router.push({ name: 'MyShelf' })"
              size="small"
            >
              查看我的书架
            </v-btn>
            <v-btn
              variant="text"
              prepend-icon="mdi-book-open-variant"
              @click="$router.push({ name: 'ReadingHubPage' })"
              size="small"
            >
              前往阅读中心
            </v-btn>
          </div>
        </v-card-text>
      </v-card>

      <!-- 收藏列表 -->
      <div v-else>
        <v-row>
          <v-col
            v-for="item in items"
            :key="`${item.media_type}_${item.item_id}`"
            cols="12"
            md="6"
            lg="4"
          >
            <v-card class="h-100 favorite-card" :class="{ 'is-favorite': true }">
              <v-card-text>
                <div class="d-flex">
                  <!-- 左侧：封面 -->
                  <div class="mr-4">
                    <v-avatar
                      size="80"
                      rounded="lg"
                      :color="item.cover_url ? undefined : getMediaTypeColor(item.media_type)"
                    >
                      <v-img
                        v-if="item.cover_url"
                        :src="item.cover_url"
                        cover
                      />
                      <span v-else class="text-h5 text-white">
                        {{ getMediaTypeIcon(item.media_type) }}
                      </span>
                    </v-avatar>
                  </div>

                  <!-- 中间：作品信息 -->
                  <div class="flex-grow-1">
                    <!-- 媒体类型标签 -->
                    <v-chip
                      size="small"
                      :color="getMediaTypeColor(item.media_type)"
                      variant="flat"
                      class="mb-2"
                    >
                      <v-icon start size="small">{{ getMediaTypeIcon(item.media_type) }}</v-icon>
                      {{ getMediaTypeLabel(item.media_type) }}
                    </v-chip>

                    <!-- 标题 -->
                    <router-link
                      :to="{ name: item.route_name, params: item.route_params }"
                      class="text-decoration-none"
                    >
                      <h3 class="text-h6 mb-1 text-primary">{{ item.title }}</h3>
                    </router-link>

                    <!-- 来源标签 -->
                    <div v-if="item.source_label" class="text-caption text-medium-emphasis mb-2">
                      {{ item.source_label }}
                    </div>

                    <!-- 阅读进度信息 -->
                    <div v-if="item.last_position_label" class="text-caption text-medium-emphasis mb-2">
                      <v-icon size="small" class="mr-1">mdi-bookmark-outline</v-icon>
                      {{ item.last_position_label }}
                    </div>

                    <!-- 漫画更新状态 -->
                    <div v-if="item.media_type === 'MANGA' && item.has_updates" class="mb-2">
                      <v-chip size="small" variant="flat" color="success" class="animate-pulse">
                        <v-icon start size="x-small">mdi-star</v-icon>
                        新 {{ item.new_chapter_count || 0 }} 话
                      </v-chip>
                    </div>

                    <!-- 漫画上次同步时间 -->
                    <div v-if="item.media_type === 'MANGA' && item.last_sync_at" class="text-caption text-medium-emphasis mb-2">
                      <v-icon size="small" class="mr-1">mdi-sync</v-icon>
                      追更于 {{ formatRelativeTime(item.last_sync_at) }}
                    </div>

                    <div v-if="item.last_read_at" class="text-caption text-medium-emphasis mb-3">
                      <v-icon size="small" class="mr-1">mdi-clock-outline</v-icon>
                      {{ formatRelativeTime(item.last_read_at) }}
                    </div>
                  </div>
                </div>

                <!-- 操作按钮 -->
                <div class="d-flex gap-2 mt-3">
                  <v-btn
                    color="primary"
                    variant="flat"
                    size="small"
                    :prepend-icon="getMediaTypeActionIcon(item.media_type)"
                    @click="handleOpenItem(item)"
                    class="flex-grow-1"
                  >
                    {{ getMediaTypeActionText(item.media_type) }}
                  </v-btn>
                  <v-btn
                    color="error"
                    variant="outlined"
                    size="small"
                    prepend-icon="mdi-heart-off"
                    @click="handleRemoveFavorite(item)"
                  >
                    取消收藏
                  </v-btn>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- 分页 -->
        <div class="d-flex justify-center mt-4">
          <v-pagination
            v-model="currentPage"
            :length="totalPages"
            :total-visible="7"
            @update:model-value="handlePageChange"
          />
        </div>
      </div>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { readingFavoriteApi, mangaLocalApi } from '@/services/api'
import type { ReadingShelfItem } from '@/types/readingFavorite'
import type { ReadingMediaType } from '@/types/readingHub'

const router = useRouter()

// 状态
const items = ref<ReadingShelfItem[]>([])
const loading = ref(false)
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(20)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

// 筛选
const activeMediaType = ref<string>('all')
const filters = ref({
  keyword: ''
})

// 加载数据
const loadFavorites = async () => {
  loading.value = true
  try {
    const mediaType = activeMediaType.value === 'all' ? undefined : activeMediaType.value as ReadingMediaType
    
    const favorites = await readingFavoriteApi.listFavorites({
      media_type: mediaType,
      limit: pageSize.value,
      offset: (currentPage.value - 1) * pageSize.value
    })
    
    // 为漫画项目加载同步状态
    const itemsWithSyncStatus = await Promise.all(
      favorites.map(async (item) => {
        if (item.media_type === 'MANGA') {
          try {
            // 获取漫画同步状态
            const syncStatus = await mangaLocalApi.getSeriesSyncStatus(item.item_id)
            return {
              ...item,
              new_chapter_count: syncStatus.new_chapter_count,
              last_sync_at: syncStatus.last_sync_at,
              has_updates: syncStatus.has_updates
            }
          } catch (err) {
            // 静默失败，返回原始数据
            return item
          }
        }
        return item
      })
    )
    
    items.value = itemsWithSyncStatus
    // 注意：API 目前没有返回总数，这里假设一次性加载所有数据
    total.value = itemsWithSyncStatus.length
  } catch (error) {
    console.error('加载收藏列表失败:', error)
  } finally {
    loading.value = false
  }
}

// 媒体类型切换
const handleMediaTypeChange = () => {
  currentPage.value = 1
  loadFavorites()
}

// 分页切换
const handlePageChange = () => {
  loadFavorites()
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 打开项目
const handleOpenItem = (item: ReadingShelfItem) => {
  router.push({
    name: item.route_name,
    params: item.route_params
  })
}

// 取消收藏
const handleRemoveFavorite = async (item: ReadingShelfItem) => {
  try {
    await readingFavoriteApi.removeFavorite({
      media_type: item.media_type,
      target_id: item.item_id
    })
    
    // 重新加载列表
    await loadFavorites()
  } catch (error) {
    console.error('取消收藏失败:', error)
  }
}

// 辅助函数
const getMediaTypeLabel = (mediaType: string): string => {
  const labels: Record<string, string> = {
    'NOVEL': '小说',
    'AUDIOBOOK': '有声书', 
    'MANGA': '漫画',
    'all': '全部'
  }
  return labels[mediaType] || mediaType
}

const getMediaTypeColor = (mediaType: ReadingMediaType): string => {
  const colors: Record<ReadingMediaType, string> = {
    'NOVEL': 'primary',
    'AUDIOBOOK': 'info',
    'MANGA': 'secondary'
  }
  return colors[mediaType] || 'grey'
}

const getMediaTypeIcon = (mediaType: ReadingMediaType): string => {
  const icons: Record<ReadingMediaType, string> = {
    'NOVEL': '📖',
    'AUDIOBOOK': '🎧',
    'MANGA': '📚'
  }
  return icons[mediaType] || '📄'
}

const getMediaTypeActionIcon = (mediaType: ReadingMediaType): string => {
  const icons: Record<ReadingMediaType, string> = {
    'NOVEL': 'mdi-book-open-variant',
    'AUDIOBOOK': 'mdi-headphones',
    'MANGA': 'mdi-book-open-page-variant'
  }
  return icons[mediaType] || 'mdi-open-in-new'
}

const getMediaTypeActionText = (mediaType: ReadingMediaType): string => {
  const texts: Record<ReadingMediaType, string> = {
    'NOVEL': '阅读',
    'AUDIOBOOK': '收听',
    'MANGA': '阅读'
  }
  return texts[mediaType] || '打开'
}

const formatRelativeTime = (dateStr: string): string => {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) {
    return '刚刚'
  } else if (diffMins < 60) {
    return `${diffMins} 分钟前`
  } else if (diffHours < 24) {
    return `${diffHours} 小时前`
  } else if (diffDays < 7) {
    return `${diffDays} 天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

// 初始化
onMounted(() => {
  loadFavorites()
})
</script>

<style scoped lang="scss">
.reading-favorite-shelf-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.favorite-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  
  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
  }

  .animate-pulse {
    animation: pulse 2s infinite;
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
</style>

<style scoped>
.reading-favorite-shelf-page {
  min-height: 100vh;
  background-color: rgb(var(--v-theme-surface));
}

.favorite-card {
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.favorite-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.favorite-card.is-favorite {
  border-color: rgb(var(--v-theme-primary));
}
</style>