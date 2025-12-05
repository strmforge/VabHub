<template>
  <div>
    <v-container>
      <!-- 页面头部 -->
      <PageHeader
        title="有声书中心"
        subtitle="总览所有已生成或正在生成的有声书，快速继续收听"
      >
        <template #actions>
          <v-btn
            color="info"
            variant="outlined"
            prepend-icon="mdi-book-open-variant"
            @click="$router.push({ name: 'ReadingHubPage' })"
            class="mr-2"
          >
            阅读中心
          </v-btn>
          <v-btn
            color="default"
            variant="outlined"
            prepend-icon="mdi-book-open-page-variant"
            @click="$router.push({ name: 'NovelCenter' })"
            class="mr-2"
          >
            小说中心
          </v-btn>
          <v-btn
            v-if="hasTTSCenter"
            color="default"
            variant="outlined"
            prepend-icon="mdi-text-to-speech"
            @click="$router.push({ name: 'TTSCenter' })"
          >
            TTS 任务中心
          </v-btn>
        </template>
      </PageHeader>

      <!-- 统计卡片 -->
      <v-row class="mt-4">
        <v-col cols="12" sm="6" md="3">
          <v-card>
            <v-card-text>
              <div class="text-caption text-medium-emphasis">总有声书作品数</div>
              <div class="text-h5 mt-1">{{ stats.totalWorks }}</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-card>
            <v-card-text>
              <div class="text-caption text-medium-emphasis">已完成 TTS</div>
              <div class="text-h5 mt-1">{{ stats.completedTTS }}</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-card>
            <v-card-text>
              <div class="text-caption text-medium-emphasis">正在生成中</div>
              <div class="text-h5 mt-1">{{ stats.generating }}</div>
            </v-card-text>
          </v-card>
        </v-col>
        <v-col cols="12" sm="6" md="3">
          <v-card>
            <v-card-text>
              <div class="text-caption text-medium-emphasis">已开始但未听完</div>
              <div class="text-h5 mt-1">{{ stats.inProgress }}</div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- 筛选区域 -->
      <v-card class="mt-4">
        <v-card-text>
          <v-row>
            <v-col cols="12" md="4">
              <v-text-field
                v-model="filters.keyword"
                label="关键字（标题/作者）"
                density="compact"
                variant="outlined"
                clearable
                prepend-inner-icon="mdi-magnify"
                @keyup.enter="applyFilters"
              />
            </v-col>
            <v-col cols="12" md="3">
              <v-select
                v-model="filters.tts_status"
                :items="ttsStatusOptions"
                label="TTS 状态"
                density="compact"
                variant="outlined"
                clearable
                @update:model-value="applyFilters"
              />
            </v-col>
            <v-col cols="12" md="2">
              <v-select
                v-model="filters.progress_filter"
                :items="progressFilterOptions"
                label="听书进度"
                density="compact"
                variant="outlined"
                clearable
                @update:model-value="applyFilters"
              />
            </v-col>
            <v-col cols="12" md="2">
              <v-select
                v-model="filters.sort_by"
                :items="sortByOptions"
                label="排序方式"
                density="compact"
                variant="outlined"
                @update:model-value="applyFilters"
              />
            </v-col>
            <v-col cols="12" md="1">
              <v-btn
                color="default"
                variant="outlined"
                block
                @click="resetFilters"
              >
                重置
              </v-btn>
            </v-col>
          </v-row>
        </v-card-text>
      </v-card>

      <!-- 作品列表 -->
      <v-card class="mt-4">
        <v-card-title>
          有声书作品
          <v-spacer />
          <span class="text-body-2 text-medium-emphasis">
            共 {{ total }} 部
          </span>
        </v-card-title>
        <v-card-text>
          <v-data-table
            :headers="headers"
            :items="items"
            :loading="loading"
            :items-per-page="pageSize"
            hide-default-footer
            no-data-text="暂无有声书作品"
          >
            <!-- 收藏列 -->
            <template v-slot:item.favorite="{ item }">
              <v-btn
                size="small"
                variant="text"
                :color="item.is_favorite ? 'yellow' : 'default'"
                :icon="item.is_favorite ? 'mdi-heart' : 'mdi-heart-outline'"
                :loading="favoriteLoading[item.work.ebook_id]"
                @click="handleToggleFavorite(item)"
              >
                <v-tooltip activator="parent">
                  {{ item.is_favorite ? '取消收藏' : '添加到收藏' }}
                </v-tooltip>
              </v-btn>
            </template>

            <!-- 作品列 -->
            <template v-slot:item.work="{ item }">
              <div>
                <router-link
                  :to="{ name: 'WorkDetail', params: { ebookId: item.work.ebook_id } }"
                  class="text-decoration-none text-primary font-weight-medium"
                >
                  {{ item.work.title }}
                </router-link>
                <div v-if="item.work.original_title" class="text-caption text-medium-emphasis">
                  {{ item.work.original_title }}
                </div>
                <div class="text-caption text-medium-emphasis mt-1">
                  <span v-if="item.work.author">{{ item.work.author }}</span>
                  <span v-if="item.work.series" class="ml-2">· {{ item.work.series }}</span>
                </div>
              </div>
            </template>

            <!-- 有声书状态列 -->
            <template v-slot:item.audiobook_status="{ item }">
              <div>
                <v-chip
                  v-if="item.tts.has_audiobook"
                  color="success"
                  size="small"
                  variant="flat"
                  class="mr-1 mb-1"
                >
                  有有声书
                </v-chip>
                <v-chip
                  v-if="item.tts.has_tts_audiobook"
                  color="primary"
                  size="small"
                  variant="flat"
                >
                  TTS 生成
                </v-chip>
                <span v-if="!item.tts.has_audiobook" class="text-caption text-medium-emphasis">—</span>
              </div>
            </template>

            <!-- TTS 任务状态列 -->
            <template v-slot:item.tts_status="{ item }">
              <div v-if="item.tts.last_job_status">
                <v-chip
                  :color="getJobStatusColor(item.tts.last_job_status)"
                  size="small"
                  variant="flat"
                >
                  {{ getJobStatusLabel(item.tts.last_job_status) }}
                </v-chip>
              </div>
              <span v-else class="text-caption text-medium-emphasis">无任务</span>
            </template>

            <!-- 听书进度列（包含阅读进度） -->
            <template v-slot:item.listening="{ item }">
              <div>
                <!-- 阅读进度（第一行） -->
                <div class="mb-2">
                  <span class="text-caption text-medium-emphasis mr-1">阅读：</span>
                  <span v-if="!item.reading.has_progress">
                    <v-chip size="x-small" variant="outlined" color="default">
                      未开始
                    </v-chip>
                  </span>
                  <span v-else-if="item.reading.is_finished">
                    <v-chip size="x-small" variant="flat" color="success">
                      已读完
                    </v-chip>
                  </span>
                  <span v-else class="text-caption">
                    已读 {{ item.reading.progress_percent.toFixed(1) }}%
                  </span>
                </div>
                <!-- 听书进度（第二行） -->
                <div>
                  <span class="text-caption text-medium-emphasis mr-1">听书：</span>
                  <span v-if="!item.listening.has_progress">
                    <v-chip size="x-small" variant="outlined" color="default">
                      未开始
                    </v-chip>
                  </span>
                  <span v-else-if="item.listening.is_finished">
                    <v-chip size="x-small" variant="flat" color="success">
                      已听完
                    </v-chip>
                  </span>
                  <span v-else class="text-caption">
                    已听 {{ item.listening.progress_percent.toFixed(1) }}%
                  </span>
                </div>
              </div>
            </template>

            <!-- 最近活动列 -->
            <template v-slot:item.last_activity="{ item }">
              <span v-if="getLastActivity(item)">
                {{ formatRelativeTime(getLastActivity(item)!) }}
              </span>
              <span v-else class="text-caption text-medium-emphasis">—</span>
            </template>

            <!-- 操作列 -->
            <template v-slot:item.actions="{ item }">
              <v-btn
                size="small"
                variant="text"
                color="primary"
                prepend-icon="mdi-book-open-page-variant"
                @click="$router.push({ name: 'NovelReader', params: { ebookId: item.work.ebook_id } })"
                class="mr-2"
              >
                阅读
              </v-btn>
              <v-btn
                size="small"
                variant="text"
                color="info"
                prepend-icon="mdi-play"
                @click="handleContinueListening(item.work.ebook_id)"
                class="mr-2"
              >
                继续收听
              </v-btn>
              <v-btn
                v-if="!item.tts.has_tts_audiobook || item.tts.last_job_status === 'failed'"
                size="small"
                variant="text"
                color="success"
                :loading="generatingTTS[item.work.ebook_id]"
                :disabled="generatingTTS[item.work.ebook_id]"
                @click="handleGenerateTTS(item.work.ebook_id)"
              >
                {{ item.tts.has_tts_audiobook ? '重新生成 TTS' : '生成 TTS' }}
              </v-btn>
            </template>
          </v-data-table>

          <!-- 分页 -->
          <div v-if="totalPages > 1" class="d-flex align-center justify-center mt-4">
            <v-pagination
              v-model="page"
              :length="totalPages"
              :total-visible="7"
              @update:model-value="handlePageChange"
            />
            <v-select
              v-model="pageSize"
              :items="[10, 20, 50, 100]"
              density="compact"
              variant="outlined"
              style="width: 100px; margin-left: 16px"
              @update:model-value="handlePageSizeChange"
            />
          </div>
        </v-card-text>
      </v-card>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { audiobookCenterApi, ttsUserApi, readingFavoriteApi } from '@/services/api'
import { useToast } from '@/composables/useToast'
import { formatRelativeTime } from '@/utils/formatters'
import type { AudiobookCenterItem } from '@/types/audiobook'
// ReadingMediaType 用于 readingFavoriteApi 调用
import PageHeader from '@/components/common/PageHeader.vue'

const router = useRouter()
const toast = useToast()

// 状态
const loading = ref(false)
const items = ref<AudiobookCenterItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const totalPages = ref(0)

// 筛选条件
const filters = ref({
  keyword: '',
  tts_status: '',
  progress_filter: '',
  sort_by: '' as '' | 'last_activity' | 'last_tts_job' | 'last_played'
})

// 排序选项
const sortByOptions = [
  { title: '默认', value: '' },
  { title: '最近活动', value: 'last_activity' },
  { title: '最近 TTS 生成', value: 'last_tts_job' },
  { title: '最近播放', value: 'last_played' }
]

// TTS 状态选项
const ttsStatusOptions = [
  { title: '全部', value: '' },
  { title: '已完成', value: 'success' },
  { title: '正在生成', value: 'queued' },
  { title: '生成中', value: 'running' },
  { title: '失败', value: 'failed' },
  { title: '无 TTS', value: 'none' }
]

// 听书进度选项
const progressFilterOptions = [
  { title: '全部', value: '' },
  { title: '未开始', value: 'not_started' },
  { title: '进行中', value: 'in_progress' },
  { title: '已完成', value: 'finished' }
]

// 生成 TTS 加载状态
const generatingTTS = ref<Record<number, boolean>>({})

// 收藏功能加载状态
const favoriteLoading = ref<Record<number, boolean>>({})

// 表格列
const headers = [
  { title: '收藏', key: 'favorite', sortable: false, width: '80px' },
  { title: '作品', key: 'work', sortable: false },
  { title: '有声书状态', key: 'audiobook_status', sortable: false },
  { title: 'TTS 任务状态', key: 'tts_status', sortable: false },
  { title: '听书进度', key: 'listening', sortable: false },
  { title: '最近活动', key: 'last_activity', sortable: false },
  { title: '操作', key: 'actions', sortable: false }
]

// 统计信息
const stats = computed(() => {
  const totalWorks = items.value.length
  const completedTTS = items.value.filter(item => 
    item.tts.has_tts_audiobook && item.tts.last_job_status === 'success'
  ).length
  const generating = items.value.filter(item => {
    const status = item.tts.last_job_status
    return status === 'queued' || status === 'running' || status === 'partial'
  }).length
  const inProgress = items.value.filter(item => 
    item.listening.has_progress && !item.listening.is_finished
  ).length
  
  return {
    totalWorks,
    completedTTS,
    generating,
    inProgress
  }
})

// 检查是否有 TTS 中心路由
const hasTTSCenter = computed(() => {
  // 简单检查路由是否存在
  return router.resolve({ name: 'TTSCenter' }).name === 'TTSCenter'
})

// 加载列表
const loadItems = async () => {
  loading.value = true
  try {
    const params: any = {
      page: page.value,
      page_size: pageSize.value
    }
    
    if (filters.value.keyword) {
      params.keyword = filters.value.keyword
    }
    if (filters.value.tts_status) {
      params.tts_status = filters.value.tts_status
    }
    if (filters.value.progress_filter) {
      params.progress_filter = filters.value.progress_filter
    }
    
    const response = await audiobookCenterApi.getList(params)
    
    let resultItems = response.items || []
    
    // 前端排序
    if (filters.value.sort_by) {
      resultItems = [...resultItems].sort((a, b) => {
        const getActivityTime = (item: AudiobookCenterItem): number => {
          const times: number[] = []
          if (item.tts.last_job_at) times.push(new Date(item.tts.last_job_at).getTime())
          if (item.listening.last_played_at) times.push(new Date(item.listening.last_played_at).getTime())
          return times.length > 0 ? Math.max(...times) : 0
        }
        
        if (filters.value.sort_by === 'last_activity') {
          return getActivityTime(b) - getActivityTime(a)
        } else if (filters.value.sort_by === 'last_tts_job') {
          const aTime = a.tts.last_job_at ? new Date(a.tts.last_job_at).getTime() : 0
          const bTime = b.tts.last_job_at ? new Date(b.tts.last_job_at).getTime() : 0
          return bTime - aTime
        } else if (filters.value.sort_by === 'last_played') {
          const aTime = a.listening.last_played_at ? new Date(a.listening.last_played_at).getTime() : 0
          const bTime = b.listening.last_played_at ? new Date(b.listening.last_played_at).getTime() : 0
          return bTime - aTime
        }
        return 0
      })
    }
    
    items.value = resultItems
    total.value = response.total || 0
    page.value = response.page || 1
    pageSize.value = response.page_size || 20
    totalPages.value = Math.ceil((response.total || 0) / (response.page_size || 20))
  } catch (err: any) {
    console.error('加载有声书中心列表失败:', err)
    toast.error(err.response?.data?.detail || err.message || '加载失败')
    items.value = []
    total.value = 0
    totalPages.value = 0
  } finally {
    loading.value = false
  }
}

// 应用筛选
const applyFilters = () => {
  page.value = 1
  loadItems()
}

// 重置筛选
const resetFilters = () => {
  filters.value = {
    keyword: '',
    tts_status: '',
    progress_filter: '',
    sort_by: ''
  }
  page.value = 1
  loadItems()
}

// 继续收听
const handleContinueListening = (ebookId: number) => {
  router.push({ 
    name: 'WorkDetail', 
    params: { ebookId },
    query: { autoplay: '1' }
  })
}

// 生成 TTS
const handleGenerateTTS = async (ebookId: number) => {
  if (generatingTTS.value[ebookId]) return
  
  generatingTTS.value[ebookId] = true
  try {
    await ttsUserApi.enqueueForWork(ebookId)
    toast.success('TTS 任务已创建')
    
    // 重新加载当前页
    await loadItems()
  } catch (err: any) {
    console.error('创建 TTS 任务失败:', err)
    toast.error(err.response?.data?.detail || err.message || '创建失败')
  } finally {
    generatingTTS.value[ebookId] = false
  }
}

// 切换收藏状态
const handleToggleFavorite = async (item: AudiobookCenterItem) => {
  if (favoriteLoading.value[item.work.ebook_id]) return
  
  favoriteLoading.value[item.work.ebook_id] = true
  try {
    if (item.is_favorite) {
      // 取消收藏
      await readingFavoriteApi.removeFavorite({
        media_type: 'AUDIOBOOK',
        target_id: item.work.ebook_id
      })
      toast.success('已取消收藏')
    } else {
      // 添加收藏
      await readingFavoriteApi.addFavorite({
        media_type: 'AUDIOBOOK',
        target_id: item.work.ebook_id
      })
      toast.success('已添加到收藏')
    }
    
    // 重新加载当前页（获取最新状态）
    await loadItems()
  } catch (err: any) {
    console.error('操作收藏失败:', err)
    toast.error(err.response?.data?.detail || err.message || '操作失败')
  } finally {
    favoriteLoading.value[item.work.ebook_id] = false
  }
}

// TTS 任务状态颜色
const getJobStatusColor = (status: string) => {
  switch (status) {
    case 'queued':
      return 'info'
    case 'running':
      return 'primary'
    case 'success':
      return 'success'
    case 'partial':
      return 'warning'
    case 'failed':
      return 'error'
    default:
      return 'default'
  }
}

// TTS 任务状态标签
const getJobStatusLabel = (status: string) => {
  switch (status) {
    case 'queued':
      return '队列中'
    case 'running':
      return '生成中'
    case 'success':
      return '已完成'
    case 'partial':
      return '部分完成'
    case 'failed':
      return '失败'
    default:
      return status
  }
}

// 获取最近活动时间
const getLastActivity = (item: AudiobookCenterItem): string | null => {
  const times: (string | null)[] = []
  if (item.listening.last_played_at) {
    times.push(item.listening.last_played_at)
  }
  if (item.tts.last_job_at) {
    times.push(item.tts.last_job_at)
  }
  if (times.length === 0) return null
  
  // 返回最新的时间
  return times.sort().reverse()[0] || null
}

// 分页处理
const handlePageChange = () => {
  loadItems()
}

const handlePageSizeChange = () => {
  page.value = 1
  loadItems()
}

// 初始化
onMounted(() => {
  loadItems()
})
</script>

