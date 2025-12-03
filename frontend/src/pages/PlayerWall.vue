<template>
  <div class="player-wall-page">
    <!-- 顶部过滤区域 -->
    <PageHeader title="电视墙">
      <template v-slot:actions>
        <div class="d-flex align-center gap-3">
          <!-- 搜索框 -->
          <v-text-field
            v-model="searchKeyword"
            variant="outlined"
            density="compact"
            placeholder="搜索作品..."
            prepend-inner-icon="mdi-magnify"
            hide-details
            style="max-width: 300px;"
            @keyup.enter="handleSearch"
            clearable
          />

          <!-- 媒体类型下拉 -->
          <v-select
            v-model="selectedMediaType"
            :items="mediaTypeOptions"
            variant="outlined"
            density="compact"
            hide-details
            style="max-width: 150px;"
            clearable
          />

          <!-- 115 开关 -->
          <v-switch
            v-model="only115"
            label="只看 115 源"
            hide-details
            density="compact"
            color="deep-purple"
          />
        </div>
      </template>
    </PageHeader>

    <!-- 内容区域 -->
    <v-container fluid>
      <!-- 加载状态 - 骨架屏 -->
      <div v-if="loading">
        <v-row dense>
          <v-col
            v-for="n in pageSize"
            :key="n"
            cols="6"
            sm="4"
            md="3"
            lg="2"
            xl="2"
          >
            <v-skeleton-loader
              type="card"
              elevation="2"
              class="rounded-lg"
            />
          </v-col>
        </v-row>
      </div>

      <!-- 错误状态 -->
      <v-alert
        v-else-if="error"
        type="error"
        variant="tonal"
        class="mb-4"
      >
        <div class="d-flex align-center justify-space-between">
          <div>
            <v-alert-title class="text-h6">加载失败</v-alert-title>
            {{ error }}
          </div>
          <v-btn
            variant="outlined"
            color="error"
            prepend-icon="mdi-refresh"
            @click="handleRetry"
            :loading="loading"
          >
            重试
          </v-btn>
        </div>
      </v-alert>

      <!-- 海报墙 -->
      <div v-else>
        <v-row class="g-4">
          <v-col
            v-for="item in items"
            :key="item.work.id"
            cols="12"
            sm="6"
            md="4"
            lg="3"
            xl="2"
          >
            <WorkPosterCard
              :work="item.work"
              :source="item.source"
              :status="item.status"
              @click="handleSmartOpen(item.work)"
              @play="handlePlay(item.work.id, item.source, item.status)"
            />
          </v-col>
        </v-row>

        <!-- 智能空状态 -->
        <div v-if="!loading && items.length === 0" class="text-center py-12">
          <v-icon size="64" color="grey-lighten-1">
            {{ getEmptyStateIcon() }}
          </v-icon>
          <div class="mt-4 text-body-1 text-medium-emphasis">
            {{ getEmptyStateMessage() }}
          </div>
          <div class="mt-2 text-body-2 text-medium-emphasis">
            {{ getEmptyStateHint() }}
          </div>
        </div>

        <!-- 分页 -->
        <div v-if="totalPages > 1" class="d-flex justify-center align-center mt-6 mb-4">
          <v-pagination
            v-model="page"
            :length="totalPages"
            :total-visible="7"
            @update:model-value="loadList"
          />
          <v-select
            v-model="pageSize"
            :items="[12, 24, 30, 48]"
            variant="outlined"
            density="compact"
            hide-details
            style="max-width: 100px; margin-left: 16px;"
            @update:model-value="handlePageSizeChange"
          />
        </div>
      </div>
    </v-container>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useToast } from '@/composables/useToast'
import { useMediaPlayActions } from '@/composables/useMediaPlayActions'
import { useSmartTvWallOpen } from '@/composables/useSmartTvWallOpen'
import { playerWallApi } from '@/services/api'
import type { PlayerWallItem, PlayerWallWorkSummary } from '@/types/playerWall'
import PageHeader from '@/components/common/PageHeader.vue'
import WorkPosterCard from '@/components/player/WorkPosterCard.vue'

const toast = useToast()
const { play } = useMediaPlayActions()
const { openSmartTvWall } = useSmartTvWallOpen()

// 状态
const loading = ref(false)
const error = ref<string | null>(null)
const items = ref<PlayerWallItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(24)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

// 筛选条件
const searchKeyword = ref('')
const selectedMediaType = ref<string | null>(null)
const only115 = ref(false)

// 媒体类型选项
const mediaTypeOptions = [
  { title: '全部', value: null },
  { title: '电影', value: 'movie' },
  { title: '电视剧', value: 'tv' },
  { title: '短剧', value: 'short_drama' },
  { title: '动漫', value: 'anime' },
  { title: '音乐', value: 'music' }
]

// 搜索处理
const handleSearch = () => {
  page.value = 1
  loadList()
}

// 页面大小改变
const handlePageSizeChange = () => {
  page.value = 1
  loadList()
}

// 监听筛选条件变化
watch([selectedMediaType, only115], () => {
  page.value = 1
  loadList()
})

// 加载列表
const loadList = async () => {
  try {
    loading.value = true
    error.value = null

    const response = await playerWallApi.getList({
      page: page.value,
      page_size: pageSize.value,
      keyword: searchKeyword.value ?? undefined,
      media_type: selectedMediaType.value ?? undefined,
      has_115: only115.value ? 1 : undefined
    })

    // 兼容性处理：如果API不返回status字段，提供默认值
    items.value = (response.items || []).map(item => ({
      ...item,
      status: item.status || {
        has_subscription: false,
        has_active_downloads: false,
        library_status: 'not_in_library',
        hr_risk: false,
        has_progress: false,
        is_finished: false
      }
    }))
    total.value = response.total || 0
  } catch (err: any) {
    console.error('加载电视墙列表失败:', err)
    error.value = err.response?.data?.detail || err.message || '加载列表失败'
    toast.error(error.value || '加载列表失败')
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

// 处理播放按钮点击
const handlePlay = (workId: number, source: any, status: any) => {
  play({
    workId,
    source,
    status,
    preferredSource: 'auto' // 自动选择播放源
  })
}

// 智能打开处理
const handleSmartOpen = async (work: PlayerWallWorkSummary) => {
  await openSmartTvWall({ work })
}

// 智能空状态图标
const getEmptyStateIcon = () => {
  if (searchKeyword.value) return 'mdi-magnify'
  if (only115.value) return 'mdi-cloud-off-outline'
  if (selectedMediaType.value) return 'mdi-filter-off-outline'
  return 'mdi-television-off'
}

// 智能空状态消息
const getEmptyStateMessage = () => {
  if (searchKeyword.value) return `未找到包含 "${searchKeyword.value}" 的作品`
  if (only115.value) return '暂无115源作品'
  if (selectedMediaType.value) {
    const mediaType = mediaTypeOptions.find(opt => opt.value === selectedMediaType.value)
    return `暂无${mediaType?.title || '该类型'}作品`
  }
  return '暂无作品'
}

// 智能空状态提示
const getEmptyStateHint = () => {
  if (searchKeyword.value) return '尝试使用其他关键词搜索'
  if (only115.value) return '关闭"只看115源"查看更多作品'
  if (selectedMediaType.value) return '尝试选择其他媒体类型'
  return '添加一些作品到媒体库开始使用'
}

// 重试加载
const handleRetry = () => {
  loadList()
}

// 初始化
onMounted(() => {
  loadList()
})
</script>

<style scoped lang="scss">
.player-wall-page {
  min-height: 100vh;
  background-color: #f5f5f5;
}
</style>

