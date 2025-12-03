<template>
  <div class="manga-history-page">
    <!-- 顶部 PageHeader -->
    <PageHeader title="漫画阅读历史">
      <template v-slot:actions>
        <v-switch
          v-model="onlyUnfinished"
          label="只看未读完"
          color="primary"
          hide-details
          class="mt-0"
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

      <!-- 历史列表 -->
      <v-row v-else-if="filteredHistory.length > 0" dense>
        <v-col
          v-for="item in filteredHistory"
          :key="item.series_id"
          cols="6"
          sm="4"
          md="3"
          lg="2"
        >
          <v-card
            class="history-card"
            elevation="2"
            @click="goToReader(item.series_id)"
          >
            <v-img
              :src="item.series_cover_url || '/placeholder-manga.jpg'"
              aspect-ratio="2/3"
              cover
              class="history-cover"
            >
              <template v-slot:placeholder>
                <div class="d-flex align-center justify-center fill-height">
                  <v-icon size="64" color="grey-lighten-1">mdi-book-open-page-variant</v-icon>
                </div>
              </template>
              <div class="status-chip">
                <v-chip
                  :color="item.is_finished ? 'success' : 'primary'"
                  size="x-small"
                  variant="flat"
                >
                  {{ item.is_finished ? '已读完' : '继续阅读' }}
                </v-chip>
              </div>
            </v-img>
            <v-card-text class="pa-2">
              <div class="text-body-2 font-weight-medium text-truncate" :title="item.series_title">
                {{ item.series_title }}
              </div>
              <div class="text-caption text-medium-emphasis mt-1">
                <div v-if="item.last_chapter_title">
                  {{ item.last_chapter_title }}
                </div>
                <div v-if="item.last_page_index && item.total_pages">
                  第 {{ item.last_page_index }} / {{ item.total_pages }} 页
                </div>
                <div class="mt-1">
                  {{ formatDate(item.last_read_at) }}
                </div>
                <div v-if="item.source_name" class="mt-1">
                  <v-chip size="x-small" variant="outlined">
                    {{ item.source_name }}
                  </v-chip>
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
        暂无阅读历史
      </v-alert>

      <!-- 加载更多 -->
      <div v-if="hasMore" class="text-center pa-4">
        <v-btn
          color="primary"
          variant="outlined"
          :loading="loadingMore"
          @click="loadMore"
        >
          加载更多
        </v-btn>
      </div>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useToast } from '@/composables/useToast'
import { mangaProgressApi } from '@/services/api'
import type { MangaReadingHistoryItem } from '@/types/mangaLocal'
import PageHeader from '@/components/common/PageHeader.vue'

const router = useRouter()
const toast = useToast()

// 状态
const loading = ref(false)
const loadingMore = ref(false)
const error = ref<string | null>(null)
const history = ref<MangaReadingHistoryItem[]>([])
const onlyUnfinished = ref(false)
const offset = ref(0)
const limit = 20
const hasMore = ref(true)

// 过滤后的历史
const filteredHistory = computed(() => {
  if (onlyUnfinished.value) {
    return history.value.filter(item => !item.is_finished)
  }
  return history.value
})

// 格式化日期
const formatDate = (dateStr: string): string => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  const now = new Date()
  const diff = now.getTime() - date.getTime()
  const days = Math.floor(diff / (1000 * 60 * 60 * 24))
  
  if (days === 0) {
    return '今天'
  } else if (days === 1) {
    return '昨天'
  } else if (days < 7) {
    return `${days} 天前`
  } else {
    return date.toLocaleDateString('zh-CN')
  }
}

// 加载历史
const loadHistory = async (reset: boolean = false) => {
  try {
    if (reset) {
      loading.value = true
      offset.value = 0
      history.value = []
      hasMore.value = true
    } else {
      loadingMore.value = true
    }
    
    error.value = null

    const data = await mangaProgressApi.listHistory({
      limit,
      offset: offset.value
    })

    if (reset) {
      history.value = data
    } else {
      history.value.push(...data)
    }

    offset.value += data.length
    hasMore.value = data.length === limit
  } catch (err: any) {
    console.error('加载阅读历史失败:', err)
    error.value = err.response?.data?.detail || err.message || '加载失败'
    toast.error(error.value)
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

// 加载更多
const loadMore = () => {
  loadHistory(false)
}

// 跳转到阅读器
const goToReader = (seriesId: number) => {
  // 不指定 chapter_id，让阅读器根据进度自动定位
  router.push({ name: 'MangaReaderPage', params: { series_id: seriesId } })
}

// 监听筛选条件
watch(onlyUnfinished, () => {
  // 筛选在 computed 中处理，无需重新加载
})

// 初始化
onMounted(() => {
  loadHistory(true)
})
</script>

<style scoped lang="scss">
.manga-history-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}

.history-card {
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2) !important;
  }

  .history-cover {
    position: relative;
    border-radius: 4px 4px 0 0;

    .status-chip {
      position: absolute;
      top: 8px;
      right: 8px;
    }
  }
}
</style>

