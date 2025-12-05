<template>
  <div class="search-page">
    <PageHeader
      title="搜索"
      subtitle="多站点资源聚合搜索"
    />
    
    <v-row>
      <!-- 搜索栏和筛选 -->
      <v-col cols="12" md="9">
        <!-- 搜索栏 -->
        <v-card class="mb-4">
          <v-card-text>
            <v-row>
              <v-col cols="12" md="8">
                <v-autocomplete
                  v-model="searchQuery"
                  :items="suggestions"
                  label="搜索关键词"
                  prepend-inner-icon="mdi-magnify"
                  variant="outlined"
                  @keydown.enter="handleSearch"
                  @update:search="handleQueryInputImmediate"
                  @select="handleSuggestionSelect"
                  clearable
                  autocomplete="off"
                  :loading="loadingSuggestions"
                  no-data-text="输入关键词搜索"
                  hide-details
                />
              </v-col>
              <v-col cols="12" md="4" class="d-flex align-center">
                <v-btn
                  color="primary"
                  prepend-icon="mdi-magnify"
                  @click="handleSearch"
                  :loading="loading"
                  block
                  size="large"
                >
                  搜索
                </v-btn>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>
      </v-col>

      <!-- 搜索历史 -->
      <v-col cols="12" md="3">
        <SearchHistory
          :limit="10"
          @select="handleHistorySelect"
        />
      </v-col>
    </v-row>

    <!-- 高级筛选和排序 -->
    <SearchFilters
      v-model="filters"
      v-model:sort-by="sortBy"
      v-model:sort-order="sortOrder"
      @apply="handleSearch"
      class="mb-4"
    />

    <!-- 搜索结果 -->
    <div v-if="loading" class="text-center py-12">
      <v-progress-circular indeterminate color="primary" size="64" />
      <div class="mt-4 text-body-1 text-medium-emphasis">搜索中...</div>
    </div>

    <div v-else-if="searchResults.total > 0">
      <!-- 结果统计和排序 -->
      <v-card class="mb-4">
        <v-card-text class="d-flex align-center justify-space-between flex-wrap ga-2">
          <div class="text-body-1">
            找到 <strong>{{ searchResults.total }}</strong> 个结果
            <span v-if="filteredResults.length !== searchResults.total && sourceFilter">
              (已过滤: {{ filteredResults.length }} 条)
            </span>
            <span v-if="searchResults.total_pages > 1">
              (第 {{ searchResults.page }} / {{ searchResults.total_pages }} 页)
            </span>
          </div>
          <div class="d-flex align-center ga-2 flex-wrap">
            <!-- Phase EXT-4: 来源过滤 -->
            <v-select
              v-model="sourceFilter"
              :items="sourceFilterOptions"
              label="来源"
              variant="outlined"
              density="compact"
              hide-details
              style="min-width: 120px;"
              @update:model-value="handleSourceFilterChange"
            />
            <v-select
              v-model="sortBy"
              :items="sortOptions"
              label="排序"
              variant="outlined"
              density="compact"
              hide-details
              style="min-width: 150px;"
              @update:model-value="handleSearch"
            />
            <v-btn-toggle
              v-model="sortOrderToggle"
              @update:model-value="handleSortOrderChange"
              density="compact"
              variant="outlined"
            >
              <v-btn value="desc" size="small">
                <v-icon>mdi-sort-descending</v-icon>
              </v-btn>
              <v-btn value="asc" size="small">
                <v-icon>mdi-sort-ascending</v-icon>
              </v-btn>
            </v-btn-toggle>
          </div>
        </v-card-text>
      </v-card>

      <!-- 结果列表 -->
      <v-row>
        <v-col
          v-for="(result, index) in filteredResults"
          :key="index"
          cols="12"
          sm="6"
          md="4"
          lg="3"
        >
          <SearchResultCard :result="result" />
        </v-col>
      </v-row>

      <!-- 分页 -->
      <v-card v-if="searchResults.total_pages > 1" class="mt-4">
        <v-card-text class="d-flex justify-center">
          <v-pagination
            v-model="currentPage"
            :length="searchResults.total_pages"
            :total-visible="7"
            @update:model-value="handlePageChange"
          />
        </v-card-text>
      </v-card>
    </div>

    <!-- 空状态 -->
    <v-card v-else-if="hasSearched">
      <v-card-text class="text-center py-12">
        <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-magnify</v-icon>
        <div class="text-h6 text-medium-emphasis mb-2">未找到结果</div>
        <div class="text-body-2 text-medium-emphasis">请尝试调整搜索条件或筛选条件</div>
      </v-card-text>
    </v-card>

    <v-card v-else>
      <v-card-text class="text-center py-12">
        <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-magnify</v-icon>
        <div class="text-h6 text-medium-emphasis mb-2">开始搜索</div>
        <div class="text-body-2 text-medium-emphasis">输入关键词搜索媒体资源</div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/services/api'
import PageHeader from '@/components/common/PageHeader.vue'
import SearchResultCard from '@/components/search/SearchResultCard.vue'
import SearchFilters from '@/components/search/SearchFilters.vue'
import SearchHistory from '@/components/search/SearchHistory.vue'

const route = useRoute()
const searchQuery = ref((route.query.q as string) || '')
const loading = ref(false)
const hasSearched = ref(false)
const sortBy = ref('seeders')
const sortOrder = ref('desc')
const currentPage = ref(1)
const pageSize = ref(50)
const sourceFilter = ref<string | null>(null) // Phase EXT-4: 来源过滤

interface Filters {
  media_type: string | null
  year: number | null
  resolution: string | null
  quality: string | null
  min_size: number | null
  max_size: number | null
  min_seeders: number | null
  max_seeders: number | null
  include: string | null
  exclude: string | null
  language: string | null
  category: string | null
  encoding: string | null
  source: string | null
  sites: number[] | null
  hr_filter: string | null  // Phase 9: HR 过滤
  index_source: string | null  // Phase EXT-4: 索引来源
}

const filters = ref<Filters>({
  media_type: null,
  year: null,
  resolution: null,
  quality: null,
  min_size: null,
  max_size: null,
  min_seeders: null,
  max_seeders: null,
  include: null,
  exclude: null,
  language: null,
  category: null,
  encoding: null,
  source: null,
  sites: null,
  hr_filter: null,  // Phase 9: HR 过滤
  index_source: null  // Phase EXT-4: 索引来源
})

const searchResults = ref({
  results: [] as any[],
  total: 0,
  page: 1,
  page_size: 50,
  total_pages: 0
})

const sortOptions = [
  { title: '评分', value: 'score' },
  { title: '做种数', value: 'seeders' },
  { title: '大小', value: 'size' },
  { title: '上传时间', value: 'date' }
]

const sortOrderToggle = computed({
  get: () => sortOrder.value,
  set: (value) => {
    sortOrder.value = value
  }
})

const suggestions = ref<string[]>([])
const loadingSuggestions = ref(false)

// Phase EXT-4: 来源过滤选项
const sourceFilterOptions = [
  { title: '全部', value: null },
  { title: '本地索引', value: 'local' },
  { title: '外部索引', value: 'external' }
]

// Phase EXT-4: 过滤后的结果
const filteredResults = computed(() => {
  if (!sourceFilter.value) {
    return searchResults.value.results
  }
  return searchResults.value.results.filter((result: any) => result.source === sourceFilter.value)
})

// Phase EXT-4: 处理来源过滤变化
const handleSourceFilterChange = () => {
  // 前端过滤，不需要重新请求后端
  // 结果已经通过 filteredResults computed 属性过滤
}

// 使用防抖函数优化搜索建议
const debounce = <T extends (...args: any[]) => any>(
  func: T,
  wait: number
): ((...args: Parameters<T>) => void) => {
  let timeout: ReturnType<typeof setTimeout> | null = null
  
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      timeout = null
      func(...args)
    }
    
    if (timeout) {
      clearTimeout(timeout)
    }
    timeout = setTimeout(later, wait)
  }
}

const handleQueryInput = debounce(async (search: string | null) => {
  if (!search || search.length < 2) {
    suggestions.value = []
    return
  }

  loadingSuggestions.value = true
  try {
    const response = await api.get('/media/search/suggestions', {
      params: {
        query: search,
        limit: 10
      }
    })
    suggestions.value = response.data.suggestions || []
  } catch (error) {
    console.error('获取搜索建议失败:', error)
    suggestions.value = []
  } finally {
    loadingSuggestions.value = false
  }
}, 300)

// 处理输入事件（立即更新显示，但延迟请求）
const handleQueryInputImmediate = (search: string | null) => {
  // 立即更新搜索框显示
  searchQuery.value = search || ''
  
  // 触发防抖的搜索建议
  handleQueryInput(search)
}

const handleSuggestionSelect = (value: string) => {
  searchQuery.value = value
  handleSearch()
}

const handleHistorySelect = (item: any) => {
  searchQuery.value = item.query
  if (item.media_type) {
    filters.value.media_type = item.media_type
  }
  if (item.filters) {
    // 应用历史记录的筛选条件
    Object.assign(filters.value, item.filters)
  }
  handleSearch()
}

const handleSortOrderChange = (value: string) => {
  sortOrder.value = value
  handleSearch()
}

const handleSearch = async () => {
  if (!searchQuery.value.trim()) return

  loading.value = true
  hasSearched.value = true
  currentPage.value = 1

  try {
    const requestData: any = {
      query: searchQuery.value,
      page: currentPage.value,
      page_size: pageSize.value,
      sort_by: sortBy.value,
      sort_order: sortOrder.value
    }

    // 添加筛选条件
    if (filters.value.media_type) {
      requestData.media_type = filters.value.media_type
    }
    if (filters.value.year) {
      requestData.year = filters.value.year
    }
    if (filters.value.resolution) {
      requestData.resolution = filters.value.resolution
    }
    if (filters.value.quality) {
      requestData.quality = filters.value.quality
    }
    if (filters.value.min_size) {
      requestData.min_size = filters.value.min_size
    }
    if (filters.value.max_size) {
      requestData.max_size = filters.value.max_size
    }
    if (filters.value.min_seeders) {
      requestData.min_seeders = filters.value.min_seeders
    }
    if (filters.value.max_seeders) {
      requestData.max_seeders = filters.value.max_seeders
    }
    if (filters.value.include) {
      requestData.include = filters.value.include
    }
    if (filters.value.exclude) {
      requestData.exclude = filters.value.exclude
    }
    if (filters.value.language) {
      requestData.language = filters.value.language
    }
    if (filters.value.category) {
      requestData.category = filters.value.category
    }
    if (filters.value.encoding) {
      requestData.encoding = filters.value.encoding
    }
    if (filters.value.source) {
      requestData.source = filters.value.source
    }
    if (filters.value.sites && filters.value.sites.length > 0) {
      requestData.sites = filters.value.sites
    }
    // Phase 9: HR 过滤（通过 exclude 字段传递，后端会识别）
    if (filters.value.hr_filter) {
      if (filters.value.hr_filter === 'exclude_hr') {
        // 如果排除 HR，添加到 exclude 字段
        requestData.exclude = (requestData.exclude ? requestData.exclude + ' ' : '') + 'hr'
      }
      // 注意：hr_only 需要后端 API 支持，暂时通过其他方式处理
      // 这里先记录，后续可以通过扩展 API 支持
    }

    const response = await api.post('/media/search', requestData)
    searchResults.value = response.data
  } catch (error: any) {
    console.error('搜索失败:', error)
    searchResults.value = {
      results: [],
      total: 0,
      page: 1,
      page_size: pageSize.value,
      total_pages: 0
    }
  } finally {
    loading.value = false
  }
}

const handlePageChange = (page: number) => {
  currentPage.value = page
  handleSearch()
  // 滚动到顶部
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

watch(() => route.query.q, (newQuery) => {
  if (newQuery && newQuery !== searchQuery.value) {
    searchQuery.value = newQuery as string
    handleSearch()
  }
})

onMounted(() => {
  if (searchQuery.value) {
    handleSearch()
  }
})
</script>

<style scoped>
.search-page {
  min-height: 100vh;
}
</style>
